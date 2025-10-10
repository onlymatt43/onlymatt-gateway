# onlymatt Render Gateway
# FastAPI proxy vers ai.onlymatt.ca (Hostinger)
# Routes:
#   POST /ai/chat   -> https://ai.onlymatt.ca/chat/ai-chat.php
#   POST /ai/admin  -> https://ai.onlymatt.ca/admin/ai-admin.php (avec X-OM-ADMIN-KEY)
import os, json, logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
import asyncio
import libsql
from datetime import datetime, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AI_BACKEND = os.getenv("AI_BACKEND", "https://ai.onlymatt.ca")
OM_ADMIN_KEY = os.getenv("OM_ADMIN_KEY")
OM_GATEWAY_KEY = os.getenv("OM_GATEWAY_KEY")
TURSO_DB_URL = os.getenv("TURSO_DB_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

app = FastAPI(title="ONLYMATT Gateway", version="1.0.0")

# --- Turso DB Client ---
turso_client = None

@app.on_event("startup")
async def startup_event():
    global turso_client
    if TURSO_DB_URL and TURSO_AUTH_TOKEN:
        logging.info("Connecting to Turso DB...")
        turso_client = libsql.connect(TURSO_DB_URL, auth_token=TURSO_AUTH_TOKEN)
        await setup_database()
    else:
        logging.warning("Turso DB environment variables not set. Logging is disabled.")

async def setup_database():
    if not turso_client: return
    try:
        await asyncio.to_thread(turso_client.execute, """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_origin TEXT,
                request_path TEXT,
                request_body TEXT,
                response_body TEXT,
                status_code INTEGER
            )
        """)
        await asyncio.to_thread(turso_client.execute, """
            CREATE TABLE IF NOT EXISTS avatars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        await asyncio.to_thread(turso_client.execute, """
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL UNIQUE,
                avatar_id INTEGER,
                FOREIGN KEY (avatar_id) REFERENCES avatars(id)
            )
        """)
        
        # --- Seed default data if tables are empty ---
        rs_avatars = await asyncio.to_thread(turso_client.execute, "SELECT count(*) FROM avatars")
        avatar_count = rs_avatars.fetchall()
        if avatar_count and avatar_count[0][0] == 0:
            logging.info("Seeding default avatars...")
            await asyncio.to_thread(turso_client.execute, "INSERT INTO avatars (name) VALUES ('public')")
            await asyncio.to_thread(turso_client.execute, "INSERT INTO avatars (name) VALUES ('coach')")

        rs_sites = await asyncio.to_thread(turso_client.execute, "SELECT count(*) FROM sites")
        site_count = rs_sites.fetchall()
        if site_count and site_count[0][0] == 0:
            logging.info("Seeding default site configuration...")
            # Get avatar IDs
            rs_public_avatar = await asyncio.to_thread(turso_client.execute, "SELECT id FROM avatars WHERE name = 'public'")
            rs_coach_avatar = await asyncio.to_thread(turso_client.execute, "SELECT id FROM avatars WHERE name = 'coach'")
            
            public_result = rs_public_avatar.fetchall()
            coach_result = rs_coach_avatar.fetchall()
            
            public_avatar_id = public_result[0][0] if public_result else None
            coach_avatar_id = coach_result[0][0] if coach_result else None

            # Default wildcard site uses 'public'
            if public_avatar_id:
                await asyncio.to_thread(turso_client.execute,
                    "INSERT INTO sites (domain, avatar_id) VALUES (?, ?)",
                    ["*", public_avatar_id]
                )
            
            # admin.onlymatt.ca uses 'coach'
            if coach_avatar_id:
                await asyncio.to_thread(turso_client.execute,
                    "INSERT INTO sites (domain, avatar_id) VALUES (?, ?)",
                    ["admin.onlymatt.ca", coach_avatar_id]
                )

        logging.info("Turso tables are ready.")
    except Exception as e:
        logging.error(f"Failed to setup Turso tables: {e}")

async def log_to_turso(origin, path, req_body, resp_body, status):
    if not turso_client: return
    try:
        # Ensure bodies are strings
        req_body_str = json.dumps(req_body) if isinstance(req_body, dict) else str(req_body)
        resp_body_str = json.dumps(resp_body) if isinstance(resp_body, dict) else str(resp_body)

        await asyncio.to_thread(turso_client.execute,
            "INSERT INTO interactions (timestamp, source_origin, request_path, request_body, response_body, status_code) VALUES (?, ?, ?, ?, ?, ?)",
            [
                datetime.now(timezone.utc).isoformat(),
                origin,
                path,
                req_body_str,
                resp_body_str,
                status
            ]
        )
    except Exception as e:
        logging.error(f"Failed to log to Turso: {e}")


# --- security ---
async def verify_gateway_key(request: Request):
    if not OM_GATEWAY_KEY:
        logging.warning("OM_GATEWAY_KEY is not set. Allowing request without verification.")
        return
    
    key = request.headers.get("x-om-gateway-key")
    if not key:
        raise HTTPException(status_code=403, detail="Missing X-OM-GATEWAY-KEY header")
    if key != OM_GATEWAY_KEY:
        raise HTTPException(status_code=403, detail="Invalid X-OM-GATEWAY-KEY")

# CORS: autorise onlymatt.ca & om43.com (tous sous-domaines) + localhost pour tests
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
if ALLOWED_ORIGINS == "*":
    origins = [
        "https://onlymatt.ca",
        "https://om43.com",
    ]
    # wildcards pour sous-domaines communs
    origins += [f"https://{sub}.{root}" for root in ("onlymatt.ca","om43.com") for sub in ["ai","api","video","www","mattcourchesne","*"]]
    origins += ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
else:
    origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



logger = logging.getLogger("uvicorn.error")

TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "20"))

secure_router = APIRouter(dependencies=[Depends(verify_gateway_key)])

@app.get("/diagnostic")
async def diagnostic():
    """Simple diagnostic endpoint to check environment and connections"""
    try:
        # Check environment variables (don't expose sensitive data)
        env_status = {
            "TURSO_DB_URL": bool(os.getenv("TURSO_DB_URL")),
            "TURSO_AUTH_TOKEN": bool(os.getenv("TURSO_AUTH_TOKEN")),
            "AI_BACKEND": os.getenv("AI_BACKEND"),
            "OM_GATEWAY_KEY": bool(os.getenv("OM_GATEWAY_KEY")),
        }
        
        # Test Turso connection
        turso_status = "not configured"
        if turso_client:
            try:
                # Simple test query
                result = await asyncio.to_thread(turso_client.execute, "SELECT 1 as test")
                turso_status = "connected"
            except Exception as e:
                turso_status = f"error: {str(e)[:100]}"
        else:
            turso_status = "client not initialized"
        
        return {
            "ok": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": env_status,
            "turso": turso_status,
            "version": "1.0.0"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

async def forward_request(request: Request, target_url: str, extra_headers: Optional[Dict[str, str]] = None) -> Response:
    """
    Forwards a request to a target URL, preserving method, content, and headers.
    Injects extra headers if provided.
    Also determines avatar from Turso and logs the interaction.
    """
    # Determine the origin for logging and configuration
    origin_header = request.headers.get("Origin") or request.headers.get("Referer")
    origin_domain = "unknown"
    if origin_header:
        try:
            # Extract just the domain (e.g., 'om43.com', 'localhost')
            parsed_uri = urlparse(origin_header)
            origin_domain = parsed_uri.netloc.split(':')[0] # remove port
        except Exception:
            origin_domain = "unknown"

    # Prepare headers for the backend, removing Host header
    backend_headers = {key: value for key, value in request.headers.items() if key.lower() != 'host'}
    if extra_headers:
        backend_headers.update(extra_headers)

    # --- Determine Avatar from Turso based on Origin ---
    avatar_name = "public" # Default avatar
    if turso_client:
        try:
            # Find a specific site configuration
            rs_site = await asyncio.to_thread(turso_client.execute,
                "SELECT s.domain, a.name FROM sites s JOIN avatars a ON s.avatar_id = a.id WHERE s.domain = ?", [origin_domain]
            )
            
            site_result = rs_site.fetchall()
            if site_result:
                avatar_name = site_result[0][1]
                logging.info(f"Avatar '{avatar_name}' selected for specific domain '{origin_domain}'")
            else:
                # If no specific domain, look for the wildcard default
                rs_default_site = await asyncio.to_thread(turso_client.execute,
                    "SELECT a.name FROM sites s JOIN avatars a ON s.avatar_id = a.id WHERE s.domain = '*'"
                )
                default_result = rs_default_site.fetchall()
                if default_result:
                    avatar_name = default_result[0][0]
                    logging.info(f"Avatar '{avatar_name}' selected for wildcard domain.")
            
        except Exception as e:
            logging.error(f"Failed to retrieve avatar from Turso: {e}. Using default avatar '{avatar_name}'.")
    
    # Add the determined avatar to the headers for the backend
    backend_headers["X-OM-AVATAR"] = avatar_name
    # --- End Avatar Determination ---

    req_body = await request.body()
    method = request.method
    path = request.url.path

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.request(method, target_url, content=req_body, headers=backend_headers)
        
        # Return the response from the backend
        # Don't try to decode content that might be binary
        response_headers = {k: v for k, v in r.headers.items() if k.lower() not in ['content-encoding', 'transfer-encoding']}
        return Response(content=r.content, status_code=r.status_code, headers=response_headers)

    except httpx.ReadTimeout:
        logging.error(f"Gateway timeout when forwarding to {target_url}")
        req_body_for_log = req_body.decode() if isinstance(req_body, bytes) else str(req_body)
        asyncio.create_task(log_to_turso(origin_domain, path, req_body_for_log, {"error": "Gateway timeout"}, 504))
        return JSONResponse({"ok": False, "error": "Gateway timeout"}, status_code=504)
    except Exception as e:
        logging.error(f"Error forwarding request to {target_url}: {e}")
        req_body_for_log = req_body.decode() if isinstance(req_body, bytes) else str(req_body)
        asyncio.create_task(log_to_turso(origin_domain, path, req_body_for_log, {"error": str(e)}, 502))
        return JSONResponse({"ok": False, "error": f"Failed to connect to backend: {e}"}, status_code=502)

@secure_router.post("/ai/chat")
async def proxy_chat(request: Request):
    return await forward_request(request, f"{AI_BACKEND}/chat/ai-chat.php")

@secure_router.post("/ai/admin")
async def proxy_admin(request: Request):
    if not OM_ADMIN_KEY:
        return JSONResponse({"ok": False, "error": "Gateway is missing OM_ADMIN_KEY"}, status_code=500)
    
    return await forward_request(
        request, 
        f"{AI_BACKEND}/admin/ai-admin.php",
        extra_headers={"X-OM-ADMIN-KEY": OM_ADMIN_KEY}
    )

app.include_router(secure_router)
