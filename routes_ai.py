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

# Initialize DB only if credentials are available
db = None
if TURSO_URL and TURSO_TOKEN:
    try:
        db = create_client(url=TURSO_URL, auth_token=TURSO_TOKEN)
    except Exception as e:
        print(f"Turso init failed: {e}")
        db = None

async def ensure_schema():
    if db is None:
        return
    await db.execute("""
    CREATE TABLE IF NOT EXISTS ai_threads(
      thread_id TEXT PRIMARY KEY,
      user_id   TEXT,
      created_at INTEGER
    );""")
    await db.execute("""
    CREATE TABLE IF NOT EXISTS ai_messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      thread_id TEXT,
      role TEXT,
      content TEXT,
      ts INTEGER
    );""")

# Schema creation is handled by gateway.py startup event
# if db is not None:
#     import asyncio
#     asyncio.run(ensure_schema())

class ChatReq(BaseModel):
    user_id: str = "matt"
    thread_id: str
    message: str
    system: str | None = None
    max_tokens: int | None = 512
    temperature: float | None = 0.3
    remember: bool | None = True

async def _history(thread_id: str, limit: int = 20):
    if db is None:
        return []
    result = await db.execute(
        "SELECT role, content FROM ai_messages WHERE thread_id=? ORDER BY id DESC LIMIT ?",
        (thread_id, limit)
    )
    return list(reversed(result.rows))

async def _save(thread_id: str, role: str, content: str):
    if db is None:
        return
    await db.execute(
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
            raise HTTPException(502, f"Groq {r.status_code}: {r.text[:400]}")
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
