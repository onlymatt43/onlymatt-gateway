# ONLYMATT Gateway — prod-1.6 (Render, libsql-client 0.3.x stable)
import os, time, logging, httpx
from typing import Optional, Deque, Dict
from collections import defaultdict, deque
from fastapi import FastAPI, Request, HTTPException, Body, Header, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------- Env ----------
OM_ADMIN_KEY  = os.getenv("OM_ADMIN_KEY", "")
AI_BACKEND    = os.getenv("AI_BACKEND", "")
OLLAMA_URL    = os.getenv("OLLAMA_URL", "")
TURSO_DB_URL  = os.getenv("TURSO_DB_URL", "")
TURSO_DB_AUTH = os.getenv("TURSO_DB_AUTH_TOKEN", "")

# ---------- App ----------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("om-gateway")
app = FastAPI(title="ONLYMATT Gateway", version="prod-1.6")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9.-]+\.)?(onlymatt\.ca|om43\.com|ai\.onlymatt\.ca|video\.onlymatt\.ca|localhost)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["*"],
)

# ---------- Health endpoints ----------
@app.get("/")
async def root():
    return {"ok": True, "service": "ONLYMATT Gateway"}

@app.head("/")
def root_head():
    return Response(status_code=200)

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

# ---------- Rate-limit ----------
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

# ---------- Health/Admin ----------
@app.get("/ai/health")
async def ai_health():
    return {
        "ok": True,
        "version": app.version,
        "ai_backend": bool(AI_BACKEND),
        "ollama": bool(OLLAMA_URL),
        "turso": bool(TURSO_DB_URL and TURSO_DB_AUTH),
    }

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
        url = os.getenv("TURSO_DB_URL","")
        tok = os.getenv("TURSO_DB_AUTH_TOKEN","")
        if not url or not tok:
            return {"ok": False, "err": "Missing env", "url": bool(url), "token": bool(tok)}
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        c = create_client(url=url, auth_token=tok)
        res = await c.execute("SELECT 1 AS ok")
        row = res.rows[0] if res.rows else None
        if row is None:
            return {"ok": False, "err": "no rows"}
        try:
            val = row["ok"]
        except Exception:
            try:
                val = row[0]
            except Exception:
                val = 1
        return {"ok": True, "select1": {"ok": int(val)}}
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.post("/ai/admin")
async def ai_admin(x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    return {
        "ok": True,
        "version": app.version,
        "ai_backend": AI_BACKEND or None,
        "ollama_url": OLLAMA_URL or None,
        "turso": bool(TURSO_DB_URL and TURSO_DB_AUTH),
    }

# ---------- Chat proxy ----------
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

# ---------- Memory (Turso) ----------
try:
    from libsql_client import create_client
    _db = None

    def _normalize_turso_url(u: str) -> str:
        return ("https://" + u[len("libsql://"):]) if u.startswith("libsql://") else u

    def db():
        global _db
        if not TURSO_DB_URL or not TURSO_DB_AUTH:
            raise HTTPException(500, "Turso not configured")
        if _db is None:
            _db = create_client(url=_normalize_turso_url(TURSO_DB_URL), auth_token=TURSO_DB_AUTH)
        return _db

    SCHEMA_SQL = [
        """
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
        """,
        "CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id, persona, key);",
    ]

    @app.on_event("startup")
    async def init_schema():
        if TURSO_DB_URL and TURSO_DB_AUTH:
            try:
                conn = db()
                for stmt in SCHEMA_SQL:              # pas d'execute_batch en 0.3.x
                    s = stmt.strip().rstrip(";")
                    if s:
                        await conn.execute(s)
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
    def db():
        raise HTTPException(500, "libsql-client not installed")

# ---------- Memory endpoints ----------
@app.post("/ai/memory/remember")
async def memory_remember(request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    for f in ["user_id","persona","key","value"]:
        if not payload.get(f):
            raise HTTPException(400, f"{f} required")

    mid = f"mem_{int(time.time()*1000)}_{int.from_bytes(os.urandom(3),'big')}"
    try:
        sql = (
            "INSERT INTO memories("
            " id,user_id,persona,key,value,confidence,ttl_days"
            ") VALUES("
            " :id,:user_id,:persona,:key,:value,:confidence,:ttl_days"
            ")"
        )
        params = {
            "id": mid,
            "user_id": payload["user_id"],
            "persona": payload["persona"],
            "key": payload["key"],
            "value": payload["value"],
            "confidence": float(payload.get("confidence", 0.8)),
            "ttl_days": int(payload.get("ttl_days", 180)),
        }
        await db().execute(sql, params)
        return {"ok": True, "id": mid}
    except Exception as e:
        logging.exception("remember failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.get("/ai/memory/recall")
async def memory_recall(user_id: str, persona: str = "coach_v1", limit: int = 100):
    try:
        # bornage LIMIT & quoting simple (bypass bug 'result')
        limit_int = max(1, min(int(limit), 500))

        def q(s: str) -> str:
            return s.replace("'", "''")

        # aliases stables pour extraction robuste
        sql = (
            "SELECT key  AS k, "
            "       value AS v, "
            "       confidence AS c, "
            "       created_at AS t "
            f"FROM memories WHERE user_id='{q(user_id)}' AND persona='{q(persona)}' "
            f"ORDER BY created_at DESC LIMIT {limit_int}"
        )

        res = await db().execute(sql)

        def pick(row, name, idx):
            try:
                if isinstance(row, dict):
                    return row.get(name)
                try:
                    return row[name]      # mapping-like
                except Exception:
                    return row[idx]       # tuple/list-like
            except Exception:
                return None

        out = []
        for r in res.rows:
            k = pick(r, "k", 0)
            v = pick(r, "v", 1)
            c = pick(r, "c", 2)
            t = pick(r, "t", 3)
            out.append({
                "key": k,
                "value": v,
                "confidence": (float(c) if c is not None else None),
                "created_at": (str(t) if t is not None else None),
            })

        return {"ok": True, "memories": out}
    except Exception as e:
        logging.exception("recall failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

# ---------- File monitoring endpoints ----------
import os
from pathlib import Path

@app.get("/ai/files/list")
async def list_files(path: str = ".", recursive: bool = False, x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    try:
        p = Path(path).resolve()
        if not p.exists():
            raise HTTPException(404, "Path not found")
        if recursive:
            files = [str(f.relative_to(p)) for f in p.rglob("*") if f.is_file()]
        else:
            files = [f.name for f in p.iterdir() if f.is_file()]
        return {"ok": True, "path": str(p), "files": files}
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)