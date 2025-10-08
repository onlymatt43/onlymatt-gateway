# gateway.py
# OnlyMatt Gateway (FastAPI) — CORS dynamique (onlymatt.ca & om43.com),
# /healthz, /api/tags, /api/chat, header X-OM-KEY, Turso logging intégré

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

# -------------------------------------------------------
# ENV / CONFIG
# -------------------------------------------------------
APP_KEY = os.getenv("OM_GATEWAY_KEY", "CHANGE_ME")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

EXPLICIT_ALLOWED = [
    o.strip() for o in os.getenv(
        "OM_ALLOWED_ORIGINS",
        "https://onlymatt.ca,https://om43.com,https://api.onlymatt.ca"
    ).split(",")
    if o.strip()
]
ALLOWED_ROOTS = ["onlymatt.ca", "om43.com"]

# Turso
from libsql_client import create_client
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

async def get_db():
    if not (TURSO_URL and TURSO_TOKEN):
        return None
    try:
        return create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
    except Exception as e:
        print("[TURSO] init error:", e)
        return None

# -------------------------------------------------------
# APP SETUP
# -------------------------------------------------------
app = FastAPI(title="OnlyMatt Gateway", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=EXPLICIT_ALLOWED,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class WildcardCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        response = await call_next(request)
        if origin:
            netloc = urlparse(origin).netloc.lower()
            for root in ALLOWED_ROOTS:
                if netloc == root or netloc.endswith(f".{root}"):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Vary"] = "Origin"
                    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
                    response.headers["Access-Control-Allow-Headers"] = "*"
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    break
        return response

app.add_middleware(WildcardCORSMiddleware)

# -------------------------------------------------------
# RATE LIMIT (simple)
# -------------------------------------------------------
WINDOW = 60
MAX_REQ = 60
_hits = defaultdict(list)

def ratelimit(ip: str):
    now = time.time()
    bucket = _hits[ip]
    while bucket and now - bucket[0] > WINDOW:
        bucket.pop(0)
    if len(bucket) >= MAX_REQ:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    bucket.append(now)

# -------------------------------------------------------
# SCHEMAS
# -------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    model: str
    messages: List[ChatMessage]

# -------------------------------------------------------
# ROUTES
# -------------------------------------------------------
@app.get("/healthz")
async def healthz():
    return {
        "ok": True,
        "service": "onlymatt-gateway",
        "provider": "ollama",
        "turso": bool(TURSO_URL and TURSO_TOKEN),
        "roots": ALLOWED_ROOTS
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
    data = None
    url = f"{OLLAMA_URL}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            body = {**payload.dict(), "stream": False}
            r = await client.post(url, json=body)
            status_code = r.status_code
            r.raise_for_status()
            try:
                data = r.json()
            except ValueError:
                text = await r.aread()
                data = {"error": "Upstream returned non-JSON", "raw": text.decode(errors="ignore")}
    except httpx.HTTPError as e:
        status_code = getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0
        data = {"error": str(e)}

    total_ms = int((time.time() - t0) * 1000)
    try:
        if isinstance(data, dict) and "total_duration" in data:
            provider_ms = int(int(data["total_duration"]) / 1_000_000)
    except Exception:
        pass

    # Turso logging
    try:
        db = await get_db()
        if db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ip TEXT, model TEXT, message TEXT,
              status_code INT,
              provider_latency_ms INT,
              total_latency_ms INT,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await db.execute(
                "INSERT INTO logs (ip, model, message, status_code, provider_latency_ms, total_latency_ms) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [ip, model, last_msg[:1000], status_code, provider_ms, total_ms]
            )
            await db.close()
    except Exception as e:
        print(f"[turso_log] warning: {e}")

    return data