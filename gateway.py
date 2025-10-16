# ONLYMATT Gateway — prod-1.2 (Render)
import os, time, logging, httpx
from typing import Optional, Deque, Dict
from collections import defaultdict, deque

from fastapi import FastAPI, Request, HTTPException, Header, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

# -------- Env --------
OM_ADMIN_KEY = os.getenv("OM_ADMIN_KEY", "")
AI_BACKEND   = os.getenv("AI_BACKEND", "")
OLLAMA_URL   = os.getenv("OLLAMA_URL", "")

TURSO_DB_URL  = os.getenv("TURSO_DB_URL", "")
TURSO_DB_AUTH = os.getenv("TURSO_DB_AUTH_TOKEN", "")

# -------- App --------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("om-gateway")
app = FastAPI(title="ONLYMATT Gateway", version="prod-1.2")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9.-]+\.)?(onlymatt\.ca|om43\.com|ai\.onlymatt\.ca|video\.onlymatt\.ca|localhost)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -------- Health Routes (Render) --------
@app.get("/")
async def root():
    return {"ok": True, "service": "ONLYMATT Gateway"}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

# -------- Simple rate-limit (in-memory) --------
WINDOW_SEC = 60
MAX_REQ_PER_WINDOW = 60
_req_window: Dict[str, Deque[float]] = defaultdict(deque)

def rl(ip: str):
    now = time.time()
    dq = _req_window[ip]
    while dq and dq[0] < now - WINDOW_SEC:
        dq.popleft()
    if len(dq) >= MAX_REQ_PER_WINDOW:
        raise HTTPException(429, "Rate limit exceeded")
    dq.append(now)

def require_admin(key: Optional[str]):
    if not OM_ADMIN_KEY:
        raise HTTPException(500, "OM_ADMIN_KEY not set")
    if key != OM_ADMIN_KEY:
        raise HTTPException(401, "Bad key")

# -------- Health/Admin --------
@app.get("/ai/health")
async def ai_health():
    return {
        "ok": True,
        "version": app.version,
        "ai_backend": bool(AI_BACKEND),
        "ollama": bool(OLLAMA_URL),
        "turso": bool(TURSO_DB_URL and TURSO_DB_AUTH),
    }

# -------- LibSQL checks --------
@app.get("/ai/libcheck")
async def libcheck():
    try:
        import libsql_client as L
        return {"ok": True, "lib": "libsql-client", "version": getattr(L, "__version__", "?")}
    except Exception as e:
        return {"ok": False, "err": str(e)}

@app.get("/ai/tursocheck")
async def tursocheck():
    try:
        from libsql_client import create_client
        url = os.getenv("TURSO_DB_URL", "")
        tok = os.getenv("TURSO_DB_AUTH_TOKEN", "")
        if not url or not tok:
            return {"ok": False, "err": "Missing env", "url": bool(url), "token": bool(tok)}
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        c = create_client(url=url, auth_token=tok)
        res = await c.execute("SELECT 1 AS ok")
        row = res.rows[0]
        return JSONResponse({"ok": True, "select1": jsonable_encoder(row)})
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

# -------- Chat proxy --------
@app.post("/ai/chat")
async def ai_chat(request: Request):
    rl(request.client.host)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Bad JSON")

    target = OLLAMA_URL or AI_BACKEND
    if not target:
        raise HTTPException(502, "No AI backend configured")

    try:
        timeout = httpx.Timeout(60.0, read=60.0, write=30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as hx:
            r = await hx.post(target, json=payload)
            ct = r.headers.get("content-type", "")
            data = r.json() if "application/json" in ct else {"raw": r.text}
            return JSONResponse(data, status_code=r.status_code)
    except httpx.ConnectError:
        raise HTTPException(502, "AI backend unreachable")
    except httpx.ReadTimeout:
        raise HTTPException(504, "AI backend timeout")

# -------- Memory (Turso) --------
try:
    from libsql_client import create_client
    _db = None

    def _normalize_turso_url(u: str) -> str:
        return ("https://" + u[len("libsql://"):]) if u.startswith("libsql://") else u

    async def db():
        global _db
        if not TURSO_DB_URL or not TURSO_DB_AUTH:
            raise HTTPException(500, "Turso not configured")
        if _db is None:
            _db = create_client(url=_normalize_turso_url(TURSO_DB_URL), auth_token=TURSO_DB_AUTH)
        return _db

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS memories (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      persona TEXT NOT NULL,
      key TEXT NOT NULL,
      value TEXT NOT NULL,
      confidence REAL DEFAULT 0.8,
      ttl_days INTEGER DEFAULT 180,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id, persona, key);
    """

    @app.on_event("startup")
    async def init_schema():
        if TURSO_DB_URL and TURSO_DB_AUTH:
            try:
                dbc = await db()
                await dbc.execute_batch(SCHEMA_SQL)
                log.info("Turso schema ready.")
            except Exception as e:
                log.warning(f"Turso init skipped: {e}")
        else:
            log.info("Turso not configured; memory routes will 500 if called.")

    @app.on_event("shutdown")
    async def close_db():
        global _db
        try:
            if _db is not None:
                close_fn = getattr(_db, "close", None)
                if callable(close_fn):
                    ret = close_fn()
                    if hasattr(ret, "__await__"):
                        await ret
                _db = None
        except Exception:
            pass

except Exception as e:
    log.warning(f"Turso client not available: {e}")
    async def db():
        raise HTTPException(500, "libsql-client not installed")

@app.post("/ai/memory/remember")
async def memory_remember(request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    for f in ["user_id", "persona", "key", "value"]:
        if not payload.get(f):
            raise HTTPException(400, f"{f} required")
    mid = f"mem_{int(time.time()*1000)}_{int.from_bytes(os.urandom(3),'big')}"
    try:
        dbc = await db()
        await dbc.execute(
            "INSERT INTO memories(id,user_id,persona,key,value,confidence,ttl_days) VALUES(?,?,?,?,?,?,?)",
            [
                mid,
                payload["user_id"], payload["persona"],
                payload["key"], payload["value"],
                float(payload.get("confidence", 0.8)),
                int(payload.get("ttl_days", 180)),
            ],
        )
        return {"ok": True, "id": mid}
    except Exception as e:
        logging.exception("remember failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.get("/ai/memory/recall")
async def memory_recall(user_id: str, persona: str = "coach_v1", limit: int = 100):
    try:
        # bornage LIMIT et quoting ultra simple (doublage des quotes)
        limit_int = max(1, min(int(limit), 500))
        def q(s: str) -> str:
            return s.replace("'", "''")

        sql = (
            "SELECT key, value, confidence, created_at "
            f"FROM memories WHERE user_id='{q(user_id)}' AND persona='{q(persona)}' "
            f"ORDER BY created_at DESC LIMIT {limit_int}"
        )

        res = await db().execute(sql)  # <-- aucun paramètre passé au driver
        out = []
        for r in res.rows:
            try:
                out.append({
                    "key": r["key"] if "key" in r else None,
                    "value": r["value"] if "value" in r else None,
                    "confidence": float(r["confidence"]) if "confidence" in r else None,
                    "created_at": str(r["created_at"]) if "created_at" in r else None,
                })
            except Exception:
                out.append({})
        return {"ok": True, "memories": out}
    except Exception as e:
        logging.exception("recall failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)