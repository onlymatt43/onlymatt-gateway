# OnlyMatt Gateway (FastAPI) — CORS dynamique (onlymatt.ca & om43.com),
# /healthz, /api/tags, /api/chat, header X-OM-KEY, rate-limit simple par IP.
# + Turso logging (async) : IP, modèle, prompt, durées, statut.

import os
import time
from collections import defaultdict
from typing import List
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

# === Turso (libsql-client) ===
# NOTE: On utilise le endpoint HTTP: TURSO_DATABASE_URL=https://<db>.turso.io
#       PAS "libsql://", PAS d'URL avec la région.
import asyncio
from libsql_client import create_client

# -----------------------
# ENV / Config
# -----------------------
APP_KEY = os.getenv("OM_GATEWAY_KEY", "CHANGE_ME")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

TURSO_URL = os.getenv("TURSO_DATABASE_URL")  # ex: https://onlymatt-memory-onlymatt43.turso.io
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")  # ex: tkn_...

# Optionnel : origines explicites (non-wildcard) séparées par virgules
EXPLICIT_ALLOWED = [
    o.strip() for o in os.getenv(
        "OM_ALLOWED_ORIGINS",
        "https://onlymatt.ca,https://om43.com,https://api.onlymatt.ca"
    ).split(",")
    if o.strip()
]

# Racines wildcard autorisées
ALLOWED_ROOTS = ["onlymatt.ca", "om43.com"]

# -----------------------
# App
# -----------------------
app = FastAPI(title="OnlyMatt Gateway", version="0.4.0")

# CORS “de base” pour les origines explicites (FastAPI/Starlette)
app.add_middleware(
    CORSMiddleware,
    allow_origins=EXPLICIT_ALLOWED,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware wildcard pour *.onlymatt.ca / *.om43.com
class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        response = await call_next(request)

        if origin:
            netloc = urlparse(origin).netloc.lower()
            for root in ALLOWED_ROOTS:
                if netloc == root or netloc.endswith(f".{root}"):
                    # Autoriser dynamiquement ce sous-domaine
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Vary"] = "Origin"
                    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
                    response.headers["Access-Control-Allow-Headers"] = "*"
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    break
        return response

app.add_middleware(WildcardCORSMiddleware)

# -----------------------
# Rate-limit (ultra simple): 60 req / 60s / IP
# -----------------------
WINDOW = 60
MAX_REQ = 60
_hits = defaultdict(list)

def ratelimit(ip: str):
    now = time.time()
    bucket = _hits[ip]
    # purge
    while bucket and now - bucket[0] > WINDOW:
        bucket.pop(0)
    if len(bucket) >= MAX_REQ:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    bucket.append(now)

# -----------------------
# Schemas
# -----------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    model: str
    messages: List[ChatMessage]

# -----------------------
# Turso client (async) + init table
# -----------------------
_db = None

async def get_db():
    """Retourne un client Turso réutilisable (singleton simple)."""
    global _db
    if _db is None and TURSO_URL and TURSO_TOKEN:
        _db = create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
    return _db

async def turso_init():
    """Crée la table de logs si elle n'existe pas (best effort)."""
    db = await get_db()
    if not db:
        return
    try:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ip TEXT,
          model TEXT,
          message TEXT,
          status_code INTEGER,
          provider_latency_ms INTEGER,
          total_latency_ms INTEGER,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # index simples
        await db.execute("CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_logs_model ON logs(model);")
    except Exception as e:
        # On ne bloque pas le service si Turso échoue
        print(f"[turso_init] warning: {e}")

@app.on_event("startup")
async def on_startup():
    await turso_init()

# -----------------------
# Routes
# -----------------------
@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "service": "onlymatt-gateway",
        "provider": "ollama",
        "roots": ALLOWED_ROOTS,
        "turso": bool(TURSO_URL and TURSO_TOKEN)
    }

@app.get("/api/tags")
async def tags(request: Request, x_om_key: str = Header(None)):
    if x_om_key != APP_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    ratelimit(request.client.host if request.client else "unknown")

    url = f"{OLLAMA_URL}/api/tags"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

@app.post("/api/chat")
async def chat(payload: ChatPayload, request: Request, x_om_key: str = Header(None)):
    if x_om_key != APP_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    ratelimit(request.client.host if request.client else "unknown")

    ip = request.client.host if request.client else "unknown"
    model = payload.model
    last_msg = payload.messages[-1].content if payload.messages else ""

    t0 = time.time()
    status_code = 0
    provider_ms = None

    # Forward à Ollama
    url = f"{OLLAMA_URL}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, json=payload.dict())
            status_code = r.status_code
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        status_code = getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0
        data = {"error": str(e)}

    total_ms = int((time.time() - t0) * 1000)

    # Essaye d'estimer une latence provider si l'API la renvoie (certains backends renvoient des durations)
    try:
        # Exemples possibles dans tes retours Ollama:
        # "total_duration": 3489319166, "load_duration": 2644460958, "eval_duration": 722616042
        # on prend total_duration en ns si présent
        ns = None
        if isinstance(data, dict) and "total_duration" in data:
            ns = int(data["total_duration"])
        if ns is not None:
            provider_ms = int(ns / 1_000_000)
    except Exception:
        pass

    # Log dans Turso (best effort, jamais bloquant)
    try:
        db = await get_db()
        if db:
            await db.execute(
                "INSERT INTO logs (ip, model, message, status_code, provider_latency_ms, total_latency_ms) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [ip, model, last_msg[:1000], int(status_code), provider_ms, total_ms]
            )
    except Exception as e:
        print(f"[turso_log] warning: {e}")

    return data