import asyncio
import httpx
import os
import sqlite3
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import libsql_client
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from fastapi.security import APIKeyHeader
import requests
import uvicorn

# Charger les variables d'environnement du fichier .env
load_dotenv()

# --- Débogage au démarrage : Afficher les empreintes des clés ---
print("--- Initialisation du Gateway : Vérification des clés ---")
keys_to_check = ["GROK_API_KEY", "TURSO_AUTH_TOKEN", "TURSO_DATABASE_URL", "OM_API_KEY", "OM_CONFIG_BASE_URL"]
for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # Affiche le nom de la clé, les 4 premiers et les 4 derniers caractères
        print(f"{key}: {value[:4]}...{value[-4:]}")
    else:
        print(f"{key}: NON TROUVÉE !")
print("----------------------------------------------------")
# --- Fin du débogage ---


# Création de l'application FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """
    Ensure the database and table exist on startup.
    """
    print("--- Exécution de l'événement de démarrage : Vérification de la base de données ---")
    try:
        async with create_db_client() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        print("--- Vérification de la base de données terminée avec succès ---")
    except Exception as e:
        print(f"!!! ERREUR lors de l'initialisation de la base de données : {e} !!!")

# --- Configuration ---
OM_API_KEY = os.getenv("OM_API_KEY")
OM_CONFIG_BASE_URL = os.getenv("OM_CONFIG_BASE_URL")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
GROK_API_KEY = os.getenv("GROK_API_KEY")
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

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
async def create_db_client():
    """Creates a Turso DB client."""
    # When running locally for tests without Turso vars, use a local sync SQLite connection.
    # The main logic will still use async calls, but they work with the sync driver.
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        print("⚠️ WARNING: Turso environment variables not set. Using local in-memory SQLite.")
        # We connect synchronously here, but the functions below will use it asynchronously.
        # The `libsql_client` is designed to handle this gracefully for simple cases.
        return libsql_client.create_client(":memory:")

    return libsql_client.create_client(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )

async def init_db():
    """Initializes the database and creates the history table if it doesn't exist."""
    db = await create_db_client()
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    finally:
        await db.close()

@app.on_event("startup")
async def startup_event():
    """Run initialization on startup."""
    await init_db()

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

async def get_config(site_id: str = "onlymatt"):
    """
    Fetches and returns settings.json and clips.json from the WordPress upload directory.
    This function is now more robust and handles URL construction correctly.
    """
    if not OM_CONFIG_BASE_URL:
        raise HTTPException(status_code=500, detail="OM_CONFIG_BASE_URL is not configured.")

    # Construire l'URL de base pour les fichiers de configuration
    base_url = OM_CONFIG_BASE_URL.rstrip('/')
    
    # Logique pour éviter les doublons dans le chemin (ex: /onlymatt/onlymatt/)
    # Si le site_id est déjà à la fin de l'URL de base, on ne l'ajoute pas.
    if not base_url.endswith(site_id):
        config_url_base = f"{base_url}/{site_id}"
    else:
        config_url_base = base_url

    settings_url = f"{config_url_base}/settings.json"
    clips_url = f"{config_url_base}/clips.json"
    
    print(f"Attempting to fetch settings from: {settings_url}")
    print(f"Attempting to fetch clips from: {clips_url}")

    async with httpx.AsyncClient() as client:
        try:
            settings_resp = await client.get(settings_url)
            settings_resp.raise_for_status()
            settings_json = settings_resp.json()

            clips_resp = await client.get(clips_url)
            clips_resp.raise_for_status()
            clips_json = clips_resp.json()

            return settings_json, clips_json

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Configuration files not found for site_id '{site_id}' at {config_url_base}")
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error fetching settings: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request error fetching settings: {e}")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse JSON from settings URLs.")

@app.post("/chat", summary="Process a Chat Request", dependencies=[Depends(get_api_key)])
async def chat(req: ChatRequest):
    """
    Main chat endpoint. Routes to the specified AI provider, manages memory, and returns the response.
    """
    # 1. Get config for the site
    try:
        settings, clips = await get_config(req.site_id)
        # Extraire le system_prompt des paramètres chargés
        system_prompt = settings.get("system_prompt", "You are a helpful assistant.")
    except HTTPException as e:
        # Si la configuration échoue, on renvoie l'erreur immédiatement
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    # 2. Retrieve history
    db = await create_db_client()
    try:
        result = await db.execute(
            "SELECT role, content FROM history WHERE session = ? ORDER BY timestamp DESC LIMIT ?",
            (req.session, req.keep)
        )
        history = [{"role": row[0], "content": row[1]} for row in reversed(result.rows)]
    finally:
        await db.close()

    # 3. Combine system prompt, history, and new message
    full_conversation = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": req.message}]
    
    # 4. Store user message in history
    db = await create_db_client()
    try:
        await db.execute("INSERT INTO history (session, role, content) VALUES (?, ?, ?)", (req.session, "user", req.message))
    finally:
        await db.close()

    # 5. Route to provider
    ai_reply_content = ""
    if req.provider == "grok":
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

    # 6. Store AI response in history
    if ai_reply_content:
        db = await create_db_client()
        try:
            await db.execute("INSERT INTO history (session, role, content) VALUES (?, ?, ?)", (req.session, "assistant", ai_reply_content))
        finally:
            await db.close()

    # 7. Return response
    return {"reply": ai_reply_content}

if __name__ == "__main__":
    # This part is for local execution only and doesn't need to be async
    # as uvicorn.run is a blocking call.
    # The startup event in the app will handle async initialization.
    uvicorn.run(app, host="0.0.0.0", port=5059)
