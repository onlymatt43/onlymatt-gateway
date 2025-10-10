# ONLYMATT Gateway (v2.2) – Cleaned up with Turso integration
import os, httpx, logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from libsql_client import create_client

AI_BACKEND   = os.getenv("AI_BACKEND", "https://ai.onlymatt.ca")
OM_ADMIN_KEY = os.getenv("OM_ADMIN_KEY", "")
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
TURSO_URL    = os.getenv("TURSO_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="ONLYMATT Gateway", version="2.2")

# CORS: allow *.onlymatt.ca, *.om43.com, localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?(onlymatt\.ca|om43\.com)$|http://localhost:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Turso Database Client
db_client = None
if TURSO_URL and TURSO_AUTH_TOKEN:
    try:
        db_client = create_client(url=TURSO_URL, auth_token=TURSO_AUTH_TOKEN)
        logging.info("Turso database connected")
    except Exception as e:
        logging.error(f"Turso connection failed: {e}")
else:
    logging.warning("Turso URL or auth token not set")

@app.get("/healthz")
async def health():
    return {"ok": True, "backend": AI_BACKEND, "ollama": OLLAMA_URL, "turso": bool(db_client)}

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
    return await proxy_post_raw(f"{AI_BACKEND}/ai-chat.php", request)

@app.post("/api/admin")
async def api_admin(request: Request):
    return await proxy_post_raw(f"{AI_BACKEND}/ai-admin.php", request, {"X-OM-ADMIN-KEY": OM_ADMIN_KEY})

# ---------- official /ai/* ----------
@app.post("/ai/chat")
async def ai_chat(request: Request):
    return await proxy_post_raw(f"{AI_BACKEND}/ai-chat.php", request)

@app.post("/ai/admin")
async def ai_admin(request: Request):
    return await proxy_post_raw(f"{AI_BACKEND}/ai-admin.php", request, {"X-OM-ADMIN-KEY": OM_ADMIN_KEY})

# ---------- New: AI Coach Admin (with Turso) ----------
@app.post("/ai/coach/admin")
async def coach_admin(request: Request):
    if not db_client:
        raise HTTPException(status_code=503, detail="Database not available")
    data = await request.json()
    action = data.get("action")
    if action == "create_coach":
        # Example: Insert into coaches table
        coach_data = data.get("coach", {})
        try:
            result = db_client.execute("INSERT INTO coaches (name, description) VALUES (?, ?)", 
                                       [coach_data.get("name"), coach_data.get("description")])
            return {"ok": True, "id": result.last_insert_rowid}
        except Exception as e:
            logging.error(f"DB error: {e}")
            raise HTTPException(status_code=500, detail="DB insert failed")
    elif action == "list_coaches":
        try:
            result = db_client.execute("SELECT * FROM coaches")
            coaches = [dict(row) for row in result]
            return {"ok": True, "coaches": coaches}
        except Exception as e:
            logging.error(f"DB error: {e}")
            raise HTTPException(status_code=500, detail="DB query failed")
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

# ---------- New: AI Public Avatar ----------
@app.get("/ai/avatar/public")
async def avatar_public():
    if not db_client:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        result = db_client.execute("SELECT * FROM avatars WHERE public = 1")
        avatars = [dict(row) for row in result]
        return {"ok": True, "avatars": avatars}
    except Exception as e:
        logging.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="DB query failed")

@app.post("/ai/avatar/public")
async def avatar_public_post(request: Request):
    # Example: Allow public interaction, like logging views
    data = await request.json()
    avatar_id = data.get("avatar_id")
    if not avatar_id:
        raise HTTPException(status_code=400, detail="avatar_id required")
    try:
        db_client.execute("UPDATE avatars SET views = views + 1 WHERE id = ?", [avatar_id])
        return {"ok": True}
    except Exception as e:
        logging.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="DB update failed")

# ---------- Diagnostic ----------
@app.get("/diagnostic")
async def diagnostic():
    results = {}
    # Check gateway to ai.onlymatt.ca
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{AI_BACKEND}/ai-chat.php", json={"message": "ping"})
        results["gateway_to_ai_onlymatt"] = "ok" if r.status_code == 200 else f"error {r.status_code}"
    except Exception as e:
        results["gateway_to_ai_onlymatt"] = f"error: {str(e)}"
    
    # Check ai admin ping
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{AI_BACKEND}/ai-admin.php", json={"action": "ping"}, 
                                  headers={"X-OM-ADMIN-KEY": OM_ADMIN_KEY})
        results["ai_admin_ping"] = "ok" if r.status_code == 200 else f"error {r.status_code}"
    except Exception as e:
        results["ai_admin_ping"] = f"error: {str(e)}"
    
    # Check ai chat ping
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{AI_BACKEND}/ai-chat.php", json={"message": "ping"})
        results["ai_chat_ping"] = "ok" if r.status_code == 200 else f"error {r.status_code}"
    except Exception as e:
        results["ai_chat_ping"] = f"error: {str(e)}"
    
    # Check WordPress diagnostic (if available)
    try:
        # Assuming diagnostic is at a public endpoint, e.g., https://onlymatt.ca/diagnostic
        wp_diagnostic_url = os.getenv("WP_DIAGNOSTIC_URL", "https://onlymatt.ca/diagnostic")
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(wp_diagnostic_url)
        if r.status_code == 200:
            wp_data = r.json()
            results["wp_diagnostic"] = "ok"
            results.update({f"wp_{k}": v for k, v in wp_data.items()})
        else:
            results["wp_diagnostic"] = f"error {r.status_code}"
    except Exception as e:
        results["wp_diagnostic"] = f"error: {str(e)}"
    
    # Check Turso database
    if db_client:
        try:
            # Check coaches table
            result = db_client.execute("SELECT COUNT(*) as count FROM coaches")
            coaches_count = result.fetchone()[0]
            results["turso_coaches"] = f"ok ({coaches_count} coaches)"
        except Exception as e:
            results["turso_coaches"] = f"error: {str(e)}"
        
        try:
            # Check avatars table
            result = db_client.execute("SELECT COUNT(*) as count FROM avatars")
            avatars_count = result.fetchone()[0]
            results["turso_avatars"] = f"ok ({avatars_count} avatars)"
        except Exception as e:
            results["turso_avatars"] = f"error: {str(e)}"
    else:
        results["turso_coaches"] = "error: DB not connected"
        results["turso_avatars"] = "error: DB not connected"
    
    return results

@app.get("/")
async def root():
    return {"ok": True, "service": "ONLYMATT Gateway", "version": "2.2",
            "routes": ["/ai/chat","/ai/admin","/ai/coach/admin","/ai/avatar/public","/api/chat","/api/admin","/local/chat","/diagnostic"]}