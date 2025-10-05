import os
import sqlite3
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import requests
import dotenv
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware
import libsql_client
from groq import Groq

# Load environment variables from .env file
dotenv.load_dotenv()

# --- Configuration ---
OM_API_KEY = os.getenv("OM_API_KEY")
OM_CONFIG_BASE_URL = os.getenv("OM_CONFIG_BASE_URL")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
GROK_API_KEY = os.getenv("GROK_API_KEY")
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="OnlyMatt Gateway",
    description="Centralized AI gateway for chat, memory, and settings.",
    version="1.0.0"
)

# --- CORS Middleware ---
# Allow all subdomains of onlymatt.ca, plus localhost for development
origins_regex = r"https?://(.*\.)?onlymatt\.ca(:\d+)?|https?://localhost(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origins_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Setup ---
def create_db_client():
    """Creates a Turso DB client."""
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        # This allows the app to run locally for testing without a cloud DB
        # It will use a local, temporary in-memory DB.
        print("⚠️ WARNING: Turso environment variables not set. Using local in-memory SQLite.")
        return sqlite3.connect(":memory:", check_same_thread=False)
    
    return libsql_client.create_client(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

def init_db():
    """Initializes the database and creates the history table if it doesn't exist."""
    db = create_db_client()
    db.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.close()

init_db()

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session: str = "default"
    provider: str = "ollama"
    model: str
    messages: List[ChatMessage]
    keep: int = 10 # Number of past messages to keep in memory
    site_id: Optional[str] = "global" # Add site_id for multi-site support

class HistoryResponse(BaseModel):
    history: List[ChatMessage]

# --- Security ---
api_key_header = APIKeyHeader(name="X-OM-KEY", auto_error=True)

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Dependency to validate the API key."""
    if api_key != OM_API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key

# --- API Endpoints ---

@app.get("/settings", summary="Get WordPress Settings", dependencies=[Depends(get_api_key)])
async def get_settings(site_id: str = "global"):
    """
    Fetches and returns settings.json and clips.json from the WordPress upload directory,
    based on the provided site_id.
    """
    if not OM_CONFIG_BASE_URL:
        raise HTTPException(status_code=500, detail="OM_CONFIG_BASE_URL is not configured in the environment.")

    settings_url = f"{OM_CONFIG_BASE_URL.rstrip('/')}/{site_id}/settings.json"
    clips_url = f"{OM_CONFIG_BASE_URL.rstrip('/')}/{site_id}/clips.json"

    try:
        settings_resp = requests.get(settings_url)
        settings_resp.raise_for_status()
        settings_json = settings_resp.json()

        clips_resp = requests.get(clips_url)
        clips_resp.raise_for_status()
        clips_json = clips_resp.json()

        return {
            "settings": settings_json,
            "clips": clips_json
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Configuration files not found for site_id '{site_id}' at {settings_url} or {clips_url}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {e}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {e}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse JSON from settings URLs.")


@app.post("/history", summary="Manage Conversation History", dependencies=[Depends(get_api_key)])
async def manage_history(session: str, action: str, message: Optional[ChatMessage] = None):
    """
    Read, write, or reset conversation history for a given session.
    - action='get': Returns the history.
    - action='add': Adds a message to the history.
    - action='clear': Deletes the history.
    """
    db = create_db_client()
    try:
        if action == "get":
            result = db.execute("SELECT role, content FROM history WHERE session = ? ORDER BY timestamp ASC", (session,))
            history = [{"role": row[0], "content": row[1]} for row in result.rows]
            return {"history": history}
        elif action == "add" and message:
            db.execute("INSERT INTO history (session, role, content) VALUES (?, ?, ?)", (session, message.role, message.content))
            return {"status": "message added"}
        elif action == "clear":
            db.execute("DELETE FROM history WHERE session = ?", (session,))
            return {"status": "history cleared"}
        else:
            raise HTTPException(status_code=400, detail="Invalid action or missing message.")
    finally:
        db.close()


@app.post("/chat", summary="Process a Chat Request", dependencies=[Depends(get_api_key)])
async def chat(req: ChatRequest):
    """
    Main chat endpoint. Routes to the specified AI provider, manages memory, and returns the response.
    """
    # 1. Retrieve history
    db = create_db_client()
    try:
        result = db.execute(
            "SELECT role, content FROM history WHERE session = ? ORDER BY timestamp DESC LIMIT ?",
            (req.session, req.keep)
        )
        # The history is fetched in reverse, so we need to reverse it back to chronological order
        history = [{"role": row[0], "content": row[1]} for row in reversed(result.rows)]
    finally:
        db.close()

    # 2. Combine history with new messages
    full_conversation = history + [msg.dict() for msg in req.messages]
    
    # 3. Store user message in history
    db = create_db_client()
    try:
        for msg in req.messages:
             db.execute("INSERT INTO history (session, role, content) VALUES (?, ?, ?)", (req.session, msg.role, msg.content))
    finally:
        db.close()

    # 4. Route to provider
    ai_reply_content = ""
    if req.provider == "ollama":
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json={"model": req.model, "messages": full_conversation, "stream": False},
                timeout=120
            )
            response.raise_for_status()
            ai_reply_data = response.json()
            ai_reply_content = ai_reply_data.get("message", {}).get("content", "")

        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Error contacting Ollama: {e}")
    
    elif req.provider == "grok":
        if not GROK_API_KEY:
            raise HTTPException(status_code=500, detail="GROK_API_KEY is not configured.")
        try:
            client = Groq(api_key=GROK_API_KEY)
            chat_completion = client.chat.completions.create(
                messages=full_conversation,
                model=req.model,
            )
            ai_reply_content = chat_completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error contacting Groq: {e}")

    else:
        raise HTTPException(status_code=400, detail=f"Provider '{req.provider}' not supported.")

    # 5. Store AI response in history
    if ai_reply_content:
        db = create_db_client()
        try:
            db.execute("INSERT INTO history (session, role, content) VALUES (?, ?, ?)", (req.session, "assistant", ai_reply_content))
        finally:
            db.close()

    # 6. Return response
    return {"reply": ai_reply_content}

if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=5059)
