from fastapi import APIRouter
import os

router = APIRouter(prefix="/db", tags=["db"])

@router.get("/health")
def db_health():
    url  = os.getenv("TURSO_DATABASE_URL")
    tok  = os.getenv("TURSO_AUTH_TOKEN")
    return {
        "ok": True,
        "turso_env": {
            "TURSO_DATABASE_URL": bool(url),
            "TURSO_AUTH_TOKEN": bool(tok),
        }
    }
