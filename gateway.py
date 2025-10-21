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

# Templates
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

# Static files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

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
        """
        CREATE TABLE IF NOT EXISTS admin_tasks (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          description TEXT NOT NULL,
          priority TEXT DEFAULT 'medium',
          status TEXT DEFAULT 'pending',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS admin_reports (
          id TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS admin_analyses (
          id TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          path TEXT,
          results TEXT NOT NULL,
          stats TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS chat_history (
          id TEXT PRIMARY KEY,
          user_message TEXT NOT NULL,
          assistant_response TEXT NOT NULL,
          model TEXT,
          temperature REAL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
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

# ---------- Admin Data Management (Turso) ----------
@app.post("/admin/tasks")
async def create_task(request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    require_admin(request.headers.get("x_om_key"))

    for f in ["title", "description"]:
        if not payload.get(f):
            raise HTTPException(400, f"{f} required")

    task_id = f"task_{int(time.time()*1000)}_{int.from_bytes(os.urandom(3),'big')}"
    try:
        sql = (
            "INSERT INTO admin_tasks("
            " id,title,description,priority,status"
            ") VALUES("
            " :id,:title,:description,:priority,:status"
            ")"
        )
        params = {
            "id": task_id,
            "title": payload["title"],
            "description": payload["description"],
            "priority": payload.get("priority", "medium"),
            "status": "pending",
        }
        await db().execute(sql, params)
        return {"ok": True, "id": task_id}
    except Exception as e:
        logging.exception("create task failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.get("/admin/tasks")
async def get_tasks(x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    try:
        sql = "SELECT * FROM admin_tasks ORDER BY created_at DESC"
        res = await db().execute(sql)

        def pick(row, name, idx):
            try:
                if isinstance(row, dict):
                    return row.get(name)
                try:
                    return row[name]
                except Exception:
                    return row[idx]
            except Exception:
                return None

        tasks = []
        for r in res.rows:
            tasks.append({
                "id": pick(r, "id", 0),
                "title": pick(r, "title", 1),
                "description": pick(r, "description", 2),
                "priority": pick(r, "priority", 3),
                "status": pick(r, "status", 4),
                "created_at": pick(r, "created_at", 5),
                "updated_at": pick(r, "updated_at", 6),
            })

        return {"ok": True, "tasks": tasks}
    except Exception as e:
        logging.exception("get tasks failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.put("/admin/tasks/{task_id}")
async def update_task(task_id: str, request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    require_admin(request.headers.get("x_om_key"))

    try:
        sql = (
            "UPDATE admin_tasks SET "
            "status = :status, "
            "updated_at = CURRENT_TIMESTAMP "
            "WHERE id = :id"
        )
        params = {
            "id": task_id,
            "status": payload.get("status", "pending"),
        }
        await db().execute(sql, params)
        return {"ok": True}
    except Exception as e:
        logging.exception("update task failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.delete("/admin/tasks/{task_id}")
async def delete_task(task_id: str, request: Request, x_om_key: Optional[str] = Header(None)):
    rl(request.client.host)
    require_admin(x_om_key)

    try:
        sql = "DELETE FROM admin_tasks WHERE id = :id"
        params = {"id": task_id}
        await db().execute(sql, params)
        return {"ok": True}
    except Exception as e:
        logging.exception("delete task failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.post("/admin/reports")
async def create_report(request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    require_admin(request.headers.get("x_om_key"))

    for f in ["type", "title", "content"]:
        if not payload.get(f):
            raise HTTPException(400, f"{f} required")

    report_id = f"report_{int(time.time()*1000)}_{int.from_bytes(os.urandom(3),'big')}"
    try:
        sql = (
            "INSERT INTO admin_reports("
            " id,type,title,content"
            ") VALUES("
            " :id,:type,:title,:content"
            ")"
        )
        params = {
            "id": report_id,
            "type": payload["type"],
            "title": payload["title"],
            "content": payload["content"],
        }
        await db().execute(sql, params)
        return {"ok": True, "id": report_id}
    except Exception as e:
        logging.exception("create report failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.get("/admin/reports")
async def get_reports(x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    try:
        sql = "SELECT * FROM admin_reports ORDER BY created_at DESC LIMIT 50"
        res = await db().execute(sql)

        def pick(row, name, idx):
            try:
                if isinstance(row, dict):
                    return row.get(name)
                try:
                    return row[name]
                except Exception:
                    return row[idx]
            except Exception:
                return None

        reports = []
        for r in res.rows:
            reports.append({
                "id": pick(r, "id", 0),
                "type": pick(r, "type", 1),
                "title": pick(r, "title", 2),
                "content": pick(r, "content", 3),
                "created_at": pick(r, "created_at", 4),
            })

        return {"ok": True, "reports": reports}
    except Exception as e:
        logging.exception("get reports failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.post("/admin/analyses")
async def create_analysis(request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    require_admin(request.headers.get("x_om_key"))

    for f in ["type", "results"]:
        if not payload.get(f):
            raise HTTPException(400, f"{f} required")

    analysis_id = f"analysis_{int(time.time()*1000)}_{int.from_bytes(os.urandom(3),'big')}"
    try:
        sql = (
            "INSERT INTO admin_analyses("
            " id,type,path,results,stats"
            ") VALUES("
            " :id,:type,:path,:results,:stats"
            ")"
        )
        params = {
            "id": analysis_id,
            "type": payload["type"],
            "path": payload.get("path"),
            "results": payload["results"],
            "stats": payload.get("stats"),
        }
        await db().execute(sql, params)
        return {"ok": True, "id": analysis_id}
    except Exception as e:
        logging.exception("create analysis failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.get("/admin/analyses")
async def get_analyses(x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    try:
        sql = "SELECT * FROM admin_analyses ORDER BY created_at DESC LIMIT 20"
        res = await db().execute(sql)

        def pick(row, name, idx):
            try:
                if isinstance(row, dict):
                    return row.get(name)
                try:
                    return row[name]
                except Exception:
                    return row[idx]
            except Exception:
                return None

        analyses = []
        for r in res.rows:
            analyses.append({
                "id": pick(r, "id", 0),
                "type": pick(r, "type", 1),
                "path": pick(r, "path", 2),
                "results": pick(r, "results", 3),
                "stats": pick(r, "stats", 4),
                "created_at": pick(r, "created_at", 5),
            })

        return {"ok": True, "analyses": analyses}
    except Exception as e:
        logging.exception("get analyses failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.post("/admin/chat/history")
async def save_chat_message(request: Request, payload: dict = Body(...)):
    rl(request.client.host)
    require_admin(request.headers.get("x_om_key"))

    for f in ["user_message", "assistant_response"]:
        if not payload.get(f):
            raise HTTPException(400, f"{f} required")

    chat_id = f"chat_{int(time.time()*1000)}_{int.from_bytes(os.urandom(3),'big')}"
    try:
        sql = (
            "INSERT INTO chat_history("
            " id,user_message,assistant_response,model,temperature"
            ") VALUES("
            " :id,:user_message,:assistant_response,:model,:temperature"
            ")"
        )
        params = {
            "id": chat_id,
            "user_message": payload["user_message"],
            "assistant_response": payload["assistant_response"],
            "model": payload.get("model"),
            "temperature": payload.get("temperature"),
        }
        await db().execute(sql, params)
        return {"ok": True, "id": chat_id}
    except Exception as e:
        logging.exception("save chat failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

@app.get("/admin/chat/history")
async def get_chat_history(limit: int = 50, x_om_key: Optional[str] = Header(None)):
    require_admin(x_om_key)
    try:
        sql = f"SELECT * FROM chat_history ORDER BY created_at DESC LIMIT {max(1, min(int(limit), 200))}"
        res = await db().execute(sql)

        def pick(row, name, idx):
            try:
                if isinstance(row, dict):
                    return row.get(name)
                try:
                    return row[name]
                except Exception:
                    return row[idx]
            except Exception:
                return None

        messages = []
        for r in res.rows:
            messages.append({
                "id": pick(r, "id", 0),
                "user_message": pick(r, "user_message", 1),
                "assistant_response": pick(r, "assistant_response", 2),
                "model": pick(r, "model", 3),
                "temperature": pick(r, "temperature", 4),
                "created_at": pick(r, "created_at", 5),
            })

        return {"ok": True, "messages": messages}
    except Exception as e:
        logging.exception("get chat history failed")
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

# ---------- Admin Interface ----------
from fastapi import Form

@app.get("/admin")
async def admin_home(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/chat")
async def admin_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/admin/educate")
async def admin_educate(request: Request):
    return templates.TemplateResponse("educate.html", {"request": request})

@app.get("/admin/tasks")
async def admin_tasks(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})

@app.get("/admin/reports")
async def admin_reports(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})

@app.get("/admin/analysis")
async def admin_analysis(request: Request):
    return templates.TemplateResponse("analysis.html", {"request": request})