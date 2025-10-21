# ONLYMATT Gateway — prod-1.6 (Render, libsql-client 0.3.x stable)
import os, time, logging, httpx
from typing import Optional, Deque, Dict
from collections import defaultdict, deque
from fastapi import FastAPI, Request, HTTPException, Body, Header, Response, UploadFile, File, Form
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
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
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

    # Support for Groq API
    if GROQ_API_KEY and (AI_BACKEND == "groq" or not (OLLAMA_URL or AI_BACKEND)):
        try:
            # Convert payload to Groq format
            groq_payload = {
                "model": payload.get("model", "llama3-8b-8192"),
                "messages": payload.get("messages", []),
                "temperature": payload.get("temperature", 0.7),
                "max_tokens": payload.get("max_tokens", 1024),
                "stream": payload.get("stream", False)
            }

            timeout = httpx.Timeout(60.0, read=60.0, write=30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as hx:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                r = await hx.post("https://api.groq.com/openai/v1/chat/completions", json=groq_payload, headers=headers)
                if r.status_code == 200:
                    groq_response = r.json()
                    # Convert Groq response to expected format
                    return {
                        "ok": True,
                        "response": groq_response["choices"][0]["message"]["content"],
                        "model": groq_response["model"],
                        "usage": groq_response.get("usage", {})
                    }
                else:
                    return JSONResponse({"ok": False, "error": r.text}, status_code=r.status_code)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    # Fallback to existing proxy logic
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

# ---------- File upload and sync endpoints ----------
import aiofiles
import mimetypes
from bs4 import BeautifulSoup
import json

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/ai/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    x_om_key: Optional[str] = Header(None),
    auto_publish: bool = Form(False),
    wordpress_url: Optional[str] = Form(None),
    wordpress_user: Optional[str] = Form(None),
    wordpress_password: Optional[str] = Form(None)
):
    require_admin(x_om_key)
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(400, "No file provided")
        
        # Generate unique filename
        timestamp = int(time.time())
        file_ext = Path(file.filename).suffix
        unique_filename = f"{timestamp}_{int.from_bytes(os.urandom(4), 'big'):08x}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        file_info = {
            "original_name": file.filename,
            "saved_name": unique_filename,
            "size": len(content),
            "mime_type": file.content_type or mimetypes.guess_type(file.filename)[0],
            "path": str(file_path)
        }
        
        # Auto-publish to WordPress if requested
        if auto_publish and wordpress_url and wordpress_user and wordpress_password:
            try:
                publish_result = await publish_to_wordpress(
                    file_info, content, wordpress_url, wordpress_user, wordpress_password
                )
                file_info["wordpress_publish"] = publish_result
            except Exception as e:
                file_info["wordpress_error"] = str(e)
        
        # Analyze file content with AI
        try:
            analysis = await analyze_file_content(file_info, content)
            file_info["ai_analysis"] = analysis
        except Exception as e:
            file_info["analysis_error"] = str(e)
        
        return {"ok": True, "file": file_info}
        
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

async def analyze_file_content(file_info: dict, content: bytes) -> dict:
    """Analyze file content using Groq AI"""
    if not GROQ_API_KEY:
        return {"error": "No AI backend configured"}
    
    # Prepare content preview (limit size)
    content_preview = content[:4000].decode('utf-8', errors='ignore')
    if len(content) > 4000:
        content_preview += "... (truncated)"
    
    analysis_prompt = f"""
    Analyze this file and provide:
    1. File type and purpose
    2. Key content summary
    3. Suggested actions (publish, archive, process)
    4. SEO optimization suggestions if applicable
    
    File: {file_info['original_name']}
    Size: {file_info['size']} bytes
    Type: {file_info['mime_type']}
    
    Content preview:
    {content_preview}
    """
    
    try:
        timeout = httpx.Timeout(30.0, read=30.0, write=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as hx:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": analysis_prompt}],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            r = await hx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if r.status_code == 200:
                response = r.json()
                return {
                    "analysis": response["choices"][0]["message"]["content"],
                    "model": response["model"]
                }
            else:
                return {"error": f"AI analysis failed: {r.text}"}
    except Exception as e:
        return {"error": f"AI analysis error: {str(e)}"}

async def publish_to_wordpress(file_info: dict, content: bytes, wp_url: str, wp_user: str, wp_password: str) -> dict:
    """Publish file content to WordPress"""
    try:
        # Prepare WordPress REST API call
        api_url = f"{wp_url}/wp-json/wp/v2/posts"
        
        # Create post content based on file type
        if file_info['mime_type'] and file_info['mime_type'].startswith('text/'):
            post_content = content.decode('utf-8', errors='ignore')
            post_title = Path(file_info['original_name']).stem
        else:
            post_content = f"[Fichier uploadé: {file_info['original_name']}]"
            post_title = f"Fichier: {file_info['original_name']}"
        
        post_data = {
            "title": post_title,
            "content": post_content,
            "status": "draft",  # Publish as draft first
            "categories": [1],  # Default category
            "tags": ["ai-upload", "onlymatt"]
        }
        
        # Make API call
        auth = (wp_user, wp_password)
        async with httpx.AsyncClient() as client:
            r = await client.post(api_url, json=post_data, auth=auth)
            if r.status_code in [200, 201]:
                post_data = r.json()
                return {
                    "success": True,
                    "post_id": post_data.get("id"),
                    "post_url": post_data.get("link"),
                    "status": "draft"
                }
            else:
                return {"error": f"WordPress API error: {r.text}"}
                
    except Exception as e:
        return {"error": f"WordPress publish error: {str(e)}"}

@app.get("/ai/files/uploads")
async def list_uploads(x_om_key: Optional[str] = Header(None)):
    """List uploaded files"""
    require_admin(x_om_key)
    try:
        files = []
        for f in UPLOAD_DIR.glob("*"):
            if f.is_file():
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "path": str(f)
                })
        return {"ok": True, "files": files}
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

# ---------- Website analysis and generation endpoints ----------
@app.post("/ai/website/analyze")
async def analyze_website(request: Request, x_om_key: Optional[str] = Header(None)):
    """Analyze a reference website for design and content inspiration"""
    require_admin(x_om_key)
    
    try:
        payload = await request.json()
        url = payload.get("url")
        
        if not url:
            raise HTTPException(400, "URL is required")
        
        # Fetch website content
        timeout = httpx.Timeout(30.0, read=30.0, write=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            html_content = response.text
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract key elements
        analysis = {
            "url": url,
            "title": soup.title.string if soup.title else "No title",
            "meta_description": "",
            "headings": [],
            "images": [],
            "colors": [],
            "structure": {},
            "content_type": "unknown"
        }
        
        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            analysis["meta_description"] = meta_desc.get("content", "")
        
        # Headings
        for i in range(1, 7):
            headings = soup.find_all(f"h{i}")
            if headings:
                analysis["headings"].append({
                    "level": i,
                    "count": len(headings),
                    "texts": [h.get_text().strip()[:100] for h in headings[:5]]  # First 5 headings
                })
        
        # Images
        images = soup.find_all("img")
        analysis["images"] = [
            {
                "src": img.get("src", ""),
                "alt": img.get("alt", ""),
                "width": img.get("width"),
                "height": img.get("height")
            } for img in images[:10]  # First 10 images
        ]
        
        # Basic structure analysis
        analysis["structure"] = {
            "has_header": bool(soup.find("header")),
            "has_nav": bool(soup.find("nav")),
            "has_main": bool(soup.find("main")),
            "has_footer": bool(soup.find("footer")),
            "has_sidebar": bool(soup.find("aside")),
            "forms_count": len(soup.find_all("form")),
            "links_count": len(soup.find_all("a"))
        }
        
        # Determine content type
        if soup.find("article"):
            analysis["content_type"] = "blog/article"
        elif soup.find("product"):
            analysis["content_type"] = "ecommerce"
        elif len(soup.find_all("form")) > 2:
            analysis["content_type"] = "business/contact"
        else:
            analysis["content_type"] = "corporate"
        
        # AI-powered analysis
        ai_analysis = await analyze_website_with_ai(analysis, html_content[:5000])
        analysis["ai_insights"] = ai_analysis
        
        return {"ok": True, "analysis": analysis}
        
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

async def analyze_website_with_ai(analysis: dict, content_sample: str) -> dict:
    """Use AI to analyze website design and content strategy"""
    if not GROQ_API_KEY:
        return {"error": "No AI backend configured"}
    
    prompt = f"""
    Analyze this website and provide insights for creating a similar site:
    
    URL: {analysis['url']}
    Title: {analysis['title']}
    Description: {analysis['meta_description']}
    Content Type: {analysis['content_type']}
    
    Structure: {json.dumps(analysis['structure'], indent=2)}
    
    Content Sample: {content_sample[:2000]}
    
    Provide:
    1. Overall design style (modern, minimalist, corporate, creative, etc.)
    2. Color scheme suggestions
    3. Content strategy insights
    4. Key features to replicate
    5. SEO optimization suggestions
    6. User experience recommendations
    """
    
    try:
        timeout = httpx.Timeout(30.0, read=30.0, write=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as hx:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            r = await hx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if r.status_code == 200:
                response = r.json()
                return {
                    "insights": response["choices"][0]["message"]["content"],
                    "model": response["model"]
                }
            else:
                return {"error": f"AI analysis failed: {r.text}"}
    except Exception as e:
        return {"error": f"AI analysis error: {str(e)}"}

@app.post("/ai/website/generate")
async def generate_website(request: Request, x_om_key: Optional[str] = Header(None)):
    """Generate a complete website based on data and references"""
    require_admin(x_om_key)
    
    try:
        payload = await request.json()
        
        # Extract parameters
        site_data = payload.get("site_data", {})
        references = payload.get("references", [])
        template = payload.get("template", "corporate")
        target_platform = payload.get("target_platform", "wordpress")  # wordpress, static, etc.
        
        # Generate website structure
        website_structure = await generate_website_structure(site_data, references, template)
        
        # Generate content
        content = await generate_website_content(site_data, references)
        
        # Generate HTML/CSS if needed
        if target_platform == "static":
            html_output = await generate_static_html(website_structure, content)
            website_structure["static_html"] = html_output
        
        # WordPress integration
        if target_platform == "wordpress" and payload.get("wordpress_config"):
            wp_config = payload["wordpress_config"]
            wordpress_result = await create_wordpress_site(
                website_structure, content, wp_config
            )
            website_structure["wordpress_deployment"] = wordpress_result
        
        return {
            "ok": True,
            "website": website_structure,
            "content": content,
            "target_platform": target_platform
        }
        
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

async def generate_website_structure(site_data: dict, references: list, template: str) -> dict:
    """Generate website structure based on data and references"""
    if not GROQ_API_KEY:
        return {"error": "No AI backend configured"}
    
    prompt = f"""
    Create a complete website structure for: {site_data.get('name', 'Website')}
    
    Business Info: {json.dumps(site_data, indent=2)}
    Template Style: {template}
    Reference Sites: {', '.join(references)}
    
    Generate:
    1. Site map (pages and navigation)
    2. Content sections for each page
    3. SEO structure (meta tags, headings)
    4. Call-to-action placements
    5. User flow optimization
    6. Mobile responsiveness considerations
    
    Return as structured JSON with pages, sections, and metadata.
    """
    
    try:
        timeout = httpx.Timeout(30.0, read=30.0, write=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as hx:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 2000
            }
            r = await hx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if r.status_code == 200:
                response = r.json()
                ai_response = response["choices"][0]["message"]["content"]
                
                # Try to parse as JSON, fallback to text structure
                try:
                    return json.loads(ai_response)
                except:
                    return {
                        "structure": ai_response,
                        "pages": ["home", "about", "services", "contact"],
                        "template": template,
                        "generated": True
                    }
            else:
                return {"error": f"Structure generation failed: {r.text}"}
    except Exception as e:
        return {"error": f"Structure generation error: {str(e)}"}

async def generate_website_content(site_data: dict, references: list) -> dict:
    """Generate website content based on business data"""
    if not GROQ_API_KEY:
        return {"error": "No AI backend configured"}
    
    prompt = f"""
    Generate compelling website content for: {site_data.get('name', 'Business')}
    
    Business Data: {json.dumps(site_data, indent=2)}
    Industry: {site_data.get('industry', 'general')}
    Target Audience: {site_data.get('audience', 'general')}
    
    Create:
    1. Homepage hero section with headline and subheadline
    2. About section with company story
    3. Services/products descriptions
    4. Call-to-action copy
    5. SEO-optimized meta descriptions
    6. Social proof content
    
    Make it engaging, conversion-focused, and professional.
    """
    
    try:
        timeout = httpx.Timeout(30.0, read=30.0, write=10.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as hx:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": 2500
            }
            r = await hx.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            if r.status_code == 200:
                response = r.json()
                return {
                    "content": response["choices"][0]["message"]["content"],
                    "generated": True,
                    "timestamp": int(time.time())
                }
            else:
                return {"error": f"Content generation failed: {r.text}"}
    except Exception as e:
        return {"error": f"Content generation error: {str(e)}"}

async def generate_static_html(structure: dict, content: dict) -> str:
    """Generate static HTML from structure and content"""
    # Simple HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{structure.get('title', 'Site Web')}</title>
        <meta name="description" content="{structure.get('description', '')}">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            .hero {{ background: #f0f0f0; padding: 50px; text-align: center; }}
            .section {{ margin: 40px 0; }}
        </style>
    </head>
    <body>
        <div class="hero">
            <h1>{structure.get('hero_title', 'Bienvenue')}</h1>
            <p>{structure.get('hero_subtitle', 'Découvrez notre site web')}</p>
        </div>
        
        <div class="section">
            <h2>À propos</h2>
            <p>{content.get('about', 'Contenu à propos...')}</p>
        </div>
        
        <div class="section">
            <h2>Services</h2>
            <p>{content.get('services', 'Nos services...')}</p>
        </div>
        
        <div class="section">
            <h2>Contact</h2>
            <p>{content.get('contact', 'Contactez-nous...')}</p>
        </div>
    </body>
    </html>
    """
    
    return html_template

async def create_wordpress_site(structure: dict, content: dict, wp_config: dict) -> dict:
    """Create a complete WordPress site with pages and content"""
    try:
        wp_url = wp_config.get("url")
        wp_user = wp_config.get("username")
        wp_password = wp_config.get("password")
        
        if not all([wp_url, wp_user, wp_password]):
            return {"error": "WordPress config incomplete"}
        
        results = []
        
        # Create homepage
        home_result = await create_wordpress_page({
            "title": "Accueil",
            "content": content.get("homepage", "Contenu d'accueil..."),
            "status": "publish"
        }, wp_url, wp_user, wp_password)
        results.append({"homepage": home_result})
        
        # Create about page
        about_result = await create_wordpress_page({
            "title": "À propos",
            "content": content.get("about", "Contenu à propos..."),
            "status": "publish"
        }, wp_url, wp_user, wp_password)
        results.append({"about": about_result})
        
        # Create services page
        services_result = await create_wordpress_page({
            "title": "Services",
            "content": content.get("services", "Nos services..."),
            "status": "publish"
        }, wp_url, wp_user, wp_password)
        results.append({"services": services_result})
        
        return {
            "success": True,
            "pages_created": results,
            "site_url": wp_url
        }
        
    except Exception as e:
        return {"error": f"WordPress site creation failed: {str(e)}"}

async def create_wordpress_page(page_data: dict, wp_url: str, wp_user: str, wp_password: str) -> dict:
    """Create a single WordPress page"""
    try:
        api_url = f"{wp_url}/wp-json/wp/v2/pages"
        
        auth = (wp_user, wp_password)
        async with httpx.AsyncClient() as client:
            r = await client.post(api_url, json=page_data, auth=auth)
            if r.status_code in [200, 201]:
                result = r.json()
                return {
                    "success": True,
                    "page_id": result.get("id"),
                    "page_url": result.get("link"),
                    "status": result.get("status")
                }
            else:
                return {"error": f"WordPress API error: {r.text}"}
                
    except Exception as e:
        return {"error": f"Page creation error: {str(e)}"}

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