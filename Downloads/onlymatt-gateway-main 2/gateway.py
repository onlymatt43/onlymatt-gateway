# ONLYMATT Gateway (v2.1.1) – root paths fix
import os, httpx, logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

AI_BACKEND   = os.getenv("AI_BACKEND", "https://ai.onlymatt.ca")
OM_ADMIN_KEY = os.getenv("OM_ADMIN_KEY", "")
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="ONLYMATT Gateway", version="2.1.1")

# CORS: allow *.onlymatt.ca, *.om43.com, localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?(onlymatt\.ca|om43\.com)$|http://localhost:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def health():
    return {"ok": True, "backend": AI_BACKEND, "ollama": OLLAMA_URL}

async def proxy_post_raw(url: str, request: Request, extra_headers: dict | None = None):
    body = await request.body()
    headers = {"Content-Type": request.headers.get("content-type", "application/json")}
    if extra_headers:
        headers.update(extra_headers)
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.post(url, content=body, headers=headers)
        return Response(
            content=r.content,
            status_code=r.status_code,
            media_type=r.headers.get("content-type", "application/octet-stream"),
        )
    except Exception as e:
        logging.exception("proxy error")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# ---------- OLLAMA local ----------
@app.post("/local/chat")
async def local_chat(request: Request):
    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            OLLAMA_URL,
            content=body,
            headers={"Content-Type": request.headers.get("content-type", "application/json")},
        )
    return Response(r.content, r.status_code, media_type=r.headers.get("content-type","application/json"))

# ---------- legacy /api/* (compat) -> root files ----------
@app.post("/api/chat")
async def api_chat(request: Request):
    # primary: root file
    resp = await proxy_post_raw(f"{AI_BACKEND}/ai-chat.php", request)
    # optional fallback: old subdir if host returns HTML (404 page)
    if resp.media_type.startswith("text/html"):
        return await proxy_post_raw(f"{AI_BACKEND}/chat/ai-chat.php", request)
    return resp

@app.post("/api/admin")
async def api_admin(request: Request):
    resp = await proxy_post_raw(f"{AI_BACKEND}/ai-admin.php", request, {"X-OM-ADMIN-KEY": OM_ADMIN_KEY})
    if resp.media_type.startswith("text/html"):
        return await proxy_post_raw(f"{AI_BACKEND}/admin/ai-admin.php", request, {"X-OM-ADMIN-KEY": OM_ADMIN_KEY})
    return resp

# ---------- official /ai/* ----------
@app.post("/ai/chat")
async def ai_chat(request: Request):
    resp = await proxy_post_raw(f"{AI_BACKEND}/ai-chat.php", request)
    if resp.media_type.startswith("text/html"):
        return await proxy_post_raw(f"{AI_BACKEND}/chat/ai-chat.php", request)
    return resp

@app.post("/ai/admin")
async def ai_admin(request: Request):
    resp = await proxy_post_raw(f"{AI_BACKEND}/ai-admin.php", request, {"X-OM-ADMIN-KEY": OM_ADMIN_KEY})
    if resp.media_type.startswith("text/html"):
        return await proxy_post_raw(f"{AI_BACKEND}/admin/ai-admin.php", request, {"X-OM-ADMIN-KEY": OM_ADMIN_KEY})
    return resp

@app.get("/")
async def root():
    return {"ok": True, "service": "ONLYMATT Gateway", "version": "2.1.1",
            "routes": ["/ai/chat","/ai/admin","/api/chat","/api/admin","/local/chat"]}