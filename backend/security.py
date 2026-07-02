"""
Valence Security Layer
======================
Covers:
  1. Auth Security        – session hardening, brute-force protection
  2. Access Control       – IDOR ownership enforcement on every data-touching route
  3. Secrets / Env guard  – startup audit that refuses to run if keys are exposed
  4. Bot Defense          – rate limiting (login, register, API, AI endpoints)
  5. Deployment           – HTTPS redirect, security headers, anomaly logging

Drop this file alongside main.py and wire it in as shown at the bottom.
"""

import os
import re
import time
import logging
from collections import defaultdict
from typing import Callable, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
security_log = logging.getLogger("valence.security")


# ===========================================================================
# 1. SECRETS AUDIT
#    Called at startup. Raises immediately if any secret looks exposed.
# ===========================================================================

# Patterns that must NEVER appear as literal values in env vars
_FORBIDDEN_PATTERNS = [
    re.compile(r"^(your[-_]?secret|changeme|replace[-_]?me|todo|placeholder|xxx|abc123|password)$", re.I),
    re.compile(r"^.{0,8}$"),        # suspiciously short secret
]

# Env vars that must be present and non-trivial
REQUIRED_SECRETS = [
    "SECRET_KEY",           # session signing
    "GOOGLE_CLIENT_SECRET", # Google OAuth
]

OPTIONAL_WARN_SECRETS = [
    "GOOGLE_CLIENT_ID",
    "FRONTEND_URL",
]


def audit_secrets() -> None:
    """
    Validate that required secrets are set and do not look like placeholders.
    Called once during lifespan startup. Hard-stops the server on failure.
    """
    errors: list[str] = []

    for var in REQUIRED_SECRETS:
        value = os.getenv(var, "")
        if not value:
            errors.append(f"[SECRETS] {var} is not set.")
            continue
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern.match(value):
                errors.append(f"[SECRETS] {var} looks like a placeholder: '{value[:8]}…'")
                break

    for var in OPTIONAL_WARN_SECRETS:
        if not os.getenv(var):
            security_log.warning("[SECRETS] Optional env var %s is not set.", var)

    if errors:
        for e in errors:
            security_log.critical(e)
        raise RuntimeError(
            "Security audit failed – fix the above secrets before starting the server."
        )

    security_log.info("[SECRETS] Audit passed – all required secrets present.")


# ===========================================================================
# 2. IN-MEMORY RATE LIMITER
#    Sliding-window counter keyed by (IP, endpoint-bucket).
# ===========================================================================

class _RateLimiter:
    """
    Simple in-memory sliding-window rate limiter.
    Not distributed – fine for a single-process deployment.
    For multi-process / multi-instance deployments swap the store for Redis.
    """

    def __init__(self) -> None:
        # {key: [timestamp, ...]}
        self._windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_calls: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        hits = self._windows[key]
        # prune old entries
        hits[:] = [t for t in hits if t > cutoff]
        if len(hits) >= max_calls:
            return False
        hits.append(now)
        return True

    def remaining(self, key: str, max_calls: int, window_seconds: int) -> int:
        now = time.monotonic()
        cutoff = now - window_seconds
        hits = self._windows[key]
        hits[:] = [t for t in hits if t > cutoff]
        return max(0, max_calls - len(hits))


_limiter = _RateLimiter()


# Bucket configuration: path_prefix -> (max_calls, window_seconds, scope)
# scope: "ip" | "user"  (user requires auth token, falls back to ip)
_RATE_BUCKETS: list[tuple[str, int, int, str]] = [
    # (prefix,                      max,  window_s,  scope)
    ("/api/auth/login",              10,   60,        "ip"),    # brute-force login
    ("/api/auth/register",           5,    60,        "ip"),    # account creation spam
    ("/api/auth/google",             10,   60,        "ip"),    # OAuth abuse
    ("/api/results/submit",          30,   60,        "user"),  # AI generation / test submit
    ("/api/",                        200,  60,        "ip"),    # general API catch-all
]


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_rate_key(request: Request, scope: str) -> str:
    ip = _get_client_ip(request)
    if scope == "user":
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        identifier = token[:16] if token else ip
    else:
        identifier = ip
    return identifier


def check_rate_limit(request: Request) -> Optional[JSONResponse]:
    path = request.url.path
    for prefix, max_calls, window_s, scope in _RATE_BUCKETS:
        if path.startswith(prefix):
            key = f"{prefix}:{_get_rate_key(request, scope)}"
            if not _limiter.is_allowed(key, max_calls, window_s):
                security_log.warning(
                    "[RATE_LIMIT] %s blocked on %s (max=%d / %ds)",
                    _get_client_ip(request), prefix, max_calls, window_s,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please slow down.",
                        "retry_after": window_s,
                    },
                    headers={"Retry-After": str(window_s)},
                )
    return None


# ===========================================================================
# 3. IDOR / OWNERSHIP ENFORCEMENT HELPERS
#    Import and call these inside your route handlers.
# ===========================================================================

def assert_owns_result(result_row: Optional[dict], current_user_id: str, resource: str = "result") -> None:
    """
    Raises HTTP 404 (not 403, to avoid leaking existence) if the row
    belongs to a different user or does not exist.
    Always use this instead of a plain None-check on DB results.
    """
    if result_row is None or result_row.get("user_id") != current_user_id:
        security_log.warning(
            "[IDOR] User %s attempted to access %s owned by someone else.",
            current_user_id, resource,
        )
        raise HTTPException(status_code=404, detail=f"{resource.capitalize()} not found")


def assert_owns_profile(profile_row: Optional[dict], current_user_id: str) -> None:
    """Same as assert_owns_result but for unified_profiles."""
    if profile_row is None or profile_row.get("user_id") != current_user_id:
        security_log.warning(
            "[IDOR] User %s attempted to access profile owned by someone else.",
            current_user_id,
        )
        raise HTTPException(status_code=404, detail="Profile not found")


# ===========================================================================
# 4. SECURITY HEADERS MIDDLEWARE
# ===========================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options":        "nosniff",
    "X-Frame-Options":               "DENY",
    "X-XSS-Protection":              "1; mode=block",
    "Referrer-Policy":               "strict-origin-when-cross-origin",
    "Permissions-Policy":            "geolocation=(), microphone=(), camera=()",
    "Strict-Transport-Security":     "max-age=63072000; includeSubDomains; preload",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "connect-src 'self' https://oauth2.googleapis.com https://www.googleapis.com; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self';"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


# ===========================================================================
# 5. HTTPS REDIRECT MIDDLEWARE (only active when FORCE_HTTPS=true)
# ===========================================================================

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if os.getenv("FORCE_HTTPS", "false").lower() == "true":
            if request.url.scheme == "http":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url=str(url), status_code=301)
        return await call_next(request)


# ===========================================================================
# 6. RATE LIMIT + ANOMALY LOGGING MIDDLEWARE
# ===========================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Block bots / scrapers by missing or suspicious User-Agent
        ua = request.headers.get("User-Agent", "")
        if not ua or ua.lower() in ("", "-", "python-requests", "go-http-client"):
            security_log.warning(
                "[BOT] Suspicious User-Agent '%s' from %s on %s",
                ua, _get_client_ip(request), request.url.path,
            )
            # Don't hard-block UA checks – bots can spoof. Just log.
            # Uncomment next line to hard-block:
            # return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        # Rate limit check
        blocked = check_rate_limit(request)
        if blocked:
            return blocked

        # Log anomalous patterns: unusually large request bodies
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > 2_000_000:   # 2 MB
            security_log.warning(
                "[ANOMALY] Large body (%s bytes) from %s on %s",
                content_length, _get_client_ip(request), request.url.path,
            )

        response = await call_next(request)

        # Log auth failures for monitoring
        if response.status_code == 401:
            security_log.warning(
                "[AUTH_FAIL] 401 from %s on %s",
                _get_client_ip(request), request.url.path,
            )
        if response.status_code == 403:
            security_log.warning(
                "[AUTH_FAIL] 403 from %s on %s",
                _get_client_ip(request), request.url.path,
            )

        return response


# ===========================================================================
# 7. SESSION VALIDATION HELPER
#    Use inside get_current_user so it benefits from the rate limiting above.
# ===========================================================================

def validate_session_token(token: str) -> bool:
    """
    Basic structural validation of a session token before hitting the DB.
    Tokens are created with secrets.token_urlsafe(48) → 64 URL-safe chars.
    """
    if not token:
        return False
    if not re.match(r'^[A-Za-z0-9_\-]{20,128}$', token):
        security_log.warning("[AUTH] Malformed session token rejected: %s…", token[:10])
        return False
    return True


# ===========================================================================
# 8. WIRING FUNCTION
#    Call this from main.py: wire_security(app)
# ===========================================================================

def wire_security(app: FastAPI) -> None:
    """
    Attach all security middleware to the FastAPI app.
    Order matters: outermost middleware runs first on request, last on response.
    """
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(HTTPSRedirectMiddleware)
    security_log.info("[SECURITY] All middleware wired.")