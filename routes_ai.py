import os, time, httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from libsql_client import create_client

router = APIRouter(prefix="/ai")

AI_BACKEND  = os.getenv("AI_BACKEND", "groq").lower()  # "groq" | "ollama"
GROQ_KEY    = os.getenv("GROQ_API_KEY", "")
OLLAMA_URL  = os.getenv("OLLAMA_URL", "http://localhost:11434")
TURSO_URL   = os.getenv("TURSO_DB_URL", "")
TURSO_TOKEN = os.getenv("TURSO_DB_AUTH_TOKEN", "")

db = create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)

def ensure_schema():
    db.execute("""
    CREATE TABLE IF NOT EXISTS ai_threads(
      thread_id TEXT PRIMARY KEY,
      user_id   TEXT,
      created_at INTEGER
    );""")
    db.execute("""
    CREATE TABLE IF NOT EXISTS ai_messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      thread_id TEXT,
      role TEXT,
      content TEXT,
      ts INTEGER
    );""")
ensure_schema()

class ChatReq(BaseModel):
    user_id: str = "matt"
    thread_id: str
    message: str
    system: str | None = None
    max_tokens: int | None = 512
    temperature: float | None = 0.3
    remember: bool | None = True

def _history(thread_id: str, limit: int = 20):
    rows = db.execute(
        "SELECT role, content FROM ai_messages WHERE thread_id=? ORDER BY id DESC LIMIT ?",
        (thread_id, limit)
    ).rows
    return list(reversed(rows))

def _save(thread_id: str, role: str, content: str):
    db.execute(
        "INSERT INTO ai_messages(thread_id, role, content, ts) VALUES(?,?,?,?)",
        (thread_id, role, content, int(time.time()))
    )

async def _call_groq(messages, temperature, max_tokens):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}"}
    body = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": temperature or 0.3,
        "max_tokens": max_tokens or 512,
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, headers=headers, json=body)
        if r.status_code != 200:
            raise HTTPException(502, f"Groq {r.status}: {r.text[:400]}")
        return r.json()["choices"][0]["message"]["content"].strip()

async def _call_ollama(messages, temperature, max_tokens):
    url = f"{OLLAMA_URL}/v1/chat/completions"
    body = {
        "model": "qwen2.5:7b-instruct",
        "messages": messages,
        "temperature": temperature or 0.3,
        "max_tokens": max_tokens or 512,
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=body)
        if r.status_code != 200:
            raise HTTPException(502, f"Ollama {r.status_code}: {r.text[:400]}")
        j = r.json()
        return j["choices"][0]["message"]["content"].strip()

@router.post("/chat")
async def chat(req: ChatReq):
    db.execute(
        "INSERT OR IGNORE INTO ai_threads(thread_id, user_id, created_at) VALUES(?,?,?)",
        (req.thread_id, req.user_id, int(time.time()))
    )

    msgs = []
    if req.system:
        msgs.append({"role": "system", "content": req.system})
    for r in _history(req.thread_id):
        msgs.append({"role": r["role"], "content": r["content"]})
    msgs.append({"role": "user", "content": req.message})

    if AI_BACKEND == "groq":
        reply = await _call_groq(msgs, req.temperature, req.max_tokens)
    else:
        reply = await _call_ollama(msgs, req.temperature, req.max_tokens)

    if req.remember:
        _save(req.thread_id, "user", req.message)
        _save(req.thread_id, "assistant", reply)

    return {"reply": reply}
