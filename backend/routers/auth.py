from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
import bcrypt
import uuid
import secrets
from datetime import datetime, timedelta
from database.db import get_db
from security import validate_session_token
import httpx
import os

router = APIRouter()

GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Precomputed valid bcrypt hash used for constant-time comparison when the
# user does not exist (prevents both a timing oracle and a bcrypt ValueError).
_DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(16), bcrypt.gensalt())

AVATAR_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
]

# ---------------------------------------------------------------------------
# In-memory failed-login counter (per identifier+ip) for account lockout.
# Cleared on successful login.  For multi-process deploys, move to Redis.
# ---------------------------------------------------------------------------
_failed_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS  = 10
_LOCKOUT_SECS  = 15 * 60   # 15 minutes


def _lockout_key(identifier: str, ip: str) -> str:
    return f"{ip}:{identifier.lower()}"


def _record_failure(identifier: str, ip: str) -> None:
    import time
    key = _lockout_key(identifier, ip)
    now = time.monotonic()
    hits = _failed_attempts.setdefault(key, [])
    hits.append(now)
    # prune old
    _failed_attempts[key] = [t for t in hits if t > now - _LOCKOUT_SECS]


def _is_locked_out(identifier: str, ip: str) -> bool:
    import time
    key = _lockout_key(identifier, ip)
    now = time.monotonic()
    hits = [t for t in _failed_attempts.get(key, []) if t > now - _LOCKOUT_SECS]
    _failed_attempts[key] = hits
    return len(hits) >= _MAX_ATTEMPTS


def _clear_failures(identifier: str, ip: str) -> None:
    key = _lockout_key(identifier, ip)
    _failed_attempts.pop(key, None)


def _client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

def create_session(user_id: str) -> str:
    token   = secrets.token_urlsafe(48)
    expires = datetime.utcnow() + timedelta(days=30)
    db      = get_db()
    db.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires.isoformat())
    )
    db.commit()
    db.close()
    return token


def get_current_user(request: Request):
    raw_token = request.headers.get("Authorization", "")
    token     = raw_token.replace("Bearer ", "").strip()

    # Structural validation before hitting the DB
    if not validate_session_token(token):
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        db      = get_db()
        session = db.execute(
            "SELECT * FROM sessions WHERE token = ? AND expires_at > datetime('now')",
            (token,)
        ).fetchone()

        if not session:
            db.close()
            raise HTTPException(status_code=401, detail="Session expired or invalid")

        user = db.execute(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],)
        ).fetchone()
        db.close()
    except HTTPException:
        raise
    except Exception:
        # Any storage-layer hiccup (locked DB, missing table on first run, …)
        # must surface as "not authenticated", never as a 500.
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return dict(user)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    identifier: str
    password: str

class GoogleAuthRequest(BaseModel):
    code: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register")
def register(body: RegisterRequest):
    if len(body.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    db       = get_db()
    existing = db.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (body.username.lower(), body.email.lower())
    ).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Username or email already in use")

    user_id = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    color   = AVATAR_COLORS[len(body.username) % len(AVATAR_COLORS)]

    db.execute(
        "INSERT INTO users (id, username, email, password_hash, avatar_color) VALUES (?, ?, ?, ?, ?)",
        (user_id, body.username.lower(), body.email.lower(), pw_hash, color)
    )
    db.execute(
        "INSERT INTO unified_profiles (user_id, completed_tests) VALUES (?, '[]')",
        (user_id,)
    )
    db.commit()
    db.close()

    token = create_session(user_id)
    return {
        "token": token,
        "user": {
            "id": user_id,
            "username": body.username.lower(),
            "email": body.email.lower(),
            "avatar_color": color,
        },
    }


@router.post("/login")
def login(body: LoginRequest, request: Request):
    ip = _client_ip(request)

    if _is_locked_out(body.identifier, ip):
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Please wait 15 minutes before trying again.",
        )

    db   = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE (username = ? OR email = ?) AND password_hash IS NOT NULL",
        (body.identifier.lower(), body.identifier.lower())
    ).fetchone()
    db.close()

    # Use constant-time check even on None to prevent timing oracle.
    # _DUMMY_HASH is a real bcrypt hash of a random value so checkpw never raises.
    candidate_hash = user["password_hash"].encode() if user else _DUMMY_HASH
    try:
        password_valid = bcrypt.checkpw(body.password.encode(), candidate_hash)
    except ValueError:
        # Malformed stored hash must read as "invalid credentials", not a 500.
        password_valid = False

    if not user or not password_valid:
        _record_failure(body.identifier, ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    _clear_failures(body.identifier, ip)
    token = create_session(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "avatar_color": user["avatar_color"],
        },
    }


@router.post("/google")
async def google_auth(body: GoogleAuthRequest):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": body.code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{FRONTEND_URL}/auth/callback",
            "grant_type": "authorization_code",
        })
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google OAuth failed")
        tokens    = token_resp.json()
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        guser = user_resp.json()

    db       = get_db()
    existing = db.execute(
        "SELECT * FROM users WHERE google_id = ? OR email = ?",
        (guser["id"], guser["email"].lower())
    ).fetchone()

    if existing:
        user = dict(existing)
        if not user.get("google_id"):
            db.execute("UPDATE users SET google_id = ? WHERE id = ?", (guser["id"], user["id"]))
            db.commit()
    else:
        user_id       = str(uuid.uuid4())
        base_username = guser.get("given_name", guser["email"].split("@")[0]).lower().replace(" ", "_")
        username      = base_username
        suffix        = 1
        while db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
            username = f"{base_username}{suffix}"
            suffix  += 1
        color = AVATAR_COLORS[len(username) % len(AVATAR_COLORS)]
        db.execute(
            "INSERT INTO users (id, username, email, google_id, avatar_color) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, guser["email"].lower(), guser["id"], color)
        )
        db.execute(
            "INSERT INTO unified_profiles (user_id, completed_tests) VALUES (?, '[]')",
            (user_id,)
        )
        db.commit()
        user = {"id": user_id, "username": username, "email": guser["email"].lower(), "avatar_color": color}

    db.close()
    token = create_session(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "avatar_color": user["avatar_color"],
        },
    }


@router.post("/logout")
def logout(request: Request):
    raw   = request.headers.get("Authorization", "")
    token = raw.replace("Bearer ", "").strip()
    if token:
        db = get_db()
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        db.commit()
        db.close()
    return {"ok": True}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return current_user
