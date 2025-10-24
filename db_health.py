from fastapi import APIRouter
import os

router = APIRouter(prefix="/db", tags=["db"])

@router.get("/health")
def db_health():
    return {
        "ok": True,
        "turso_env": {
            "TURSO_DATABASE_URL": bool(os.getenv("TURSO_DATABASE_URL")),
            "TURSO_AUTH_TOKEN": bool(os.getenv("TURSO_AUTH_TOKEN")),
        }
    }
