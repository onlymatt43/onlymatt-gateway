# gateway.py
# OnlyMatt Gateway (FastAPI) — CORS dynamique (onlymatt.ca & om43.com),
# /healthz, /api/tags, /api/chat, header X-OM-KEY, rate-limit simple par IP.

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

# -----------------------
# ENV / Config
# -----------------------
APP_KEY = os.getenv("OM_GATEWAY_KEY", "CHANGE_ME")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
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
app = FastAPI(title="OnlyMatt Gateway", version="0.3.0")

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
# Routes
# -----------------------
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "onlymatt-gateway", "provider": "ollama", "roots": ALLOWED_ROOTS}

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

    url = f"{OLLAMA_URL}/api/chat"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload.dict())
        r.raise_for_status()
        return r.json()