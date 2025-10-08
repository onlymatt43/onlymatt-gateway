# ONLYMATT Gateway - Version complète
# Unifie : Ollama local / OpenAI / Render proxy / Hostinger backend
# Auteur : M. Courchesne

import os
import json
import httpx
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------------------------
# CONFIGURATION GLOBALE
# ------------------------------------------------------------------------------
AI_BACKEND = os.getenv("AI_BACKEND", "https://ai.onlymatt.ca")
OM_ADMIN_KEY = os.getenv("OM_ADMIN_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OM_GATEWAY_KEY = os.getenv("OM_GATEWAY_KEY", "sk_gateway_default")
OM_ALLOWED_ORIGINS = os.getenv(
    "OM_ALLOWED_ORIGINS",
    "https://onlymatt.ca,https://om43.com,https://*.onlymatt.ca,https://*.om43.com,http://localhost:3000"
).split(",")

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="ONLYMATT Gateway", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=OM_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# HEALTHCHECK
# ------------------------------------------------------------------------------
@app.get("/healthz")
async def health():
    return {"ok": True, "backend": AI_BACKEND, "ollama": OLLAMA_URL}

# ------------------------------------------------------------------------------
# GENERIC POST PROXY
# ------------------------------------------------------------------------------
async def proxy_post(url: str, data: dict, headers: dict = None):
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(url, json=data, headers=headers)
            return JSONResponse(content=r.json(), status_code=r.status_code)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# ------------------------------------------------------------------------------
# LOCAL / OLLAMA
# ------------------------------------------------------------------------------
@app.post("/local/chat")
async def local_chat(request: Request):
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(OLLAMA_URL, json=data)
    return JSONResponse(r.json())

# ------------------------------------------------------------------------------
# REMOTE / OPENAI STYLE ENDPOINT
# ------------------------------------------------------------------------------
@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    return await proxy_post(AI_BACKEND + "/chat/ai-chat.php", data)

# ------------------------------------------------------------------------------
# ADMIN CALLS (avec clé)
# ------------------------------------------------------------------------------
@app.post("/api/admin")
async def api_admin(request: Request):
    data = await request.json()
    headers = {"X-OM-ADMIN-KEY": OM_ADMIN_KEY}
    return await proxy_post(AI_BACKEND + "/admin/ai-admin.php", data, headers=headers)

# ------------------------------------------------------------------------------
# NOUVELLES ROUTES POUR LE SYSTÈME HOSTINGER
# ------------------------------------------------------------------------------
@app.post("/ai/chat")
async def ai_chat(request: Request):
    """Route publique relayée vers le backend Hostinger."""
    data = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post("https://ai.onlymatt.ca/chat/ai-chat.php", json=data)
        return JSONResponse(r.json(), status_code=r.status_code)

@app.post("/ai/admin")
async def ai_admin(request: Request):
    """Route d'administration sécurisée relayée vers Hostinger."""
    data = await request.json()
    headers = {"X-OM-ADMIN-KEY": OM_ADMIN_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.post("https://ai.onlymatt.ca/admin/ai-admin.php", json=data, headers=headers)
        return JSONResponse(r.json(), status_code=r.status_code)

# ------------------------------------------------------------------------------
# DEFAULT / ROOT
# ------------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "ok": True,
        "service": "ONLYMATT Gateway",
        "version": "2.0",
        "routes": ["/ai/chat", "/ai/admin", "/api/chat", "/api/admin", "/local/chat"]
    }