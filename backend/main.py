import sys
import os
from dotenv import load_dotenv
# Load .env BEFORE any router/ml imports , ml.psych_layer reads its env vars
# at import time.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.db import init_db
from routers import auth, tests, results, user, psych, research
from security import audit_secrets, wire_security
import numpy as np
import sklearn

print(f"--- DIAGNOSTICS ---")
print(f"Python Executable: {sys.executable}")
print(f"NumPy Version: {np.__version__}")
print(f"Scikit-Learn Version: {sklearn.__version__}")
print(f"-------------------")

@asynccontextmanager
async def lifespan(app: FastAPI):
    audit_secrets()
    init_db()
    try:
        import threading
        from ml import psych_layer
        threading.Thread(target=psych_layer.ensure_server, daemon=True).start()
        from ml import meaning_check
        threading.Thread(target=meaning_check.load, daemon=True).start()
    except Exception:
        pass
    yield
    try:
        from ml import psych_layer
        psych_layer._stop_server()
    except Exception:
        pass

app = FastAPI(title="Valence API", version="1.0.0", lifespan=lifespan)

# CORS - only allow known origins.
# In production set ALLOWED_ORIGINS env var to a comma-separated list of real domains.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Wire security middleware (rate limiting, headers, HTTPS redirect, anomaly logging)
wire_security(app)

app.include_router(auth.router,    prefix="/api/auth",    tags=["auth"])
app.include_router(tests.router,   prefix="/api/tests",   tags=["tests"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(user.router,    prefix="/api/user",    tags=["user"])
app.include_router(psych.router,   prefix="/api/psych",   tags=["psych"])
app.include_router(research.router, prefix="/api/research", tags=["research"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Valence API"}