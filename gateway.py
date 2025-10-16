import os, httpx, logging
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

OM_ADMIN_KEY = os.getenv("OM_ADMIN_KEY", "")
AI_BACKEND   = os.getenv("AI_BACKEND", "")
OLLAMA_URL   = os.getenv("OLLAMA_URL", "")

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="ONLYMATT Gateway", version="prod-1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9.-]+\.)?(onlymatt\.ca|om43\.com|ai\.onlymatt\.ca|video\.onlymatt\.ca|localhost)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["*"],
)

@app.get("/ai/health")
async def ai_health():
    return {"ok": True, "version": app.version, "ai_backend": bool(AI_BACKEND), "ollama": bool(OLLAMA_URL)}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

def require_admin(key: Optional[str]):
    if not OM_ADMIN_KEY:
        raise HTTPException(500, "OM_ADMIN_KEY not set")
    if key != OM_ADMIN_KEY:
        raise HTTPException(401, "Bad key")

@app.post("/ai/admin")
async def ai_admin(x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    return {"ok": True, "version": app.version, "ai_backend": AI_BACKEND or None, "ollama_url": OLLAMA_URL or None}

@app.post("/ai/chat")
async def ai_chat(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Bad JSON")
    target = OLLAMA_URL or AI_BACKEND
    if not target:
        raise HTTPException(502, "No AI backend configured")
    try:
        async with httpx.AsyncClient(timeout=60) as hx:
            r = await hx.post(target, json=payload)
            ct = r.headers.get("content-type","")
            data = r.json() if "application/json" in ct else {"raw": r.text}
            return JSONResponse(data, status_code=r.status_code)
    except httpx.ConnectError:
        raise HTTPException(502, "AI backend unreachable")
    except httpx.ReadTimeout:
        raise HTTPException(504, "AI backend timeout")
