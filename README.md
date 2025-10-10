# OnlyMatt Gateway v2.2

Unified API Gateway for OnlyMatt AI ecosystem, connecting to ai.onlymatt.ca backend and integrating Turso database for ai-coach-admin and ai-public-avatar services.

## Features

- **Proxy to Hostinger Backend**: Routes `/ai/chat` and `/ai/admin` to ai.onlymatt.ca
- **Turso Database Integration**: Connected database for coaches and avatars data
- **New Endpoints**:
  - `/ai/coach/admin`: Admin operations for coaches (create, list)
  - `/ai/avatar/public`: Public avatar data and interactions
- **Diagnostic Route**: `/diagnostic` for health checks
- **CORS Support**: Allows *.onlymatt.ca, *.om43.com, localhost:3000
- **Legacy Compatibility**: `/api/chat` and `/api/admin` routes

## Environment Variables

- `AI_BACKEND`: URL of the AI backend (default: https://ai.onlymatt.ca)
- `OM_ADMIN_KEY`: Admin key for secure endpoints
- `OLLAMA_URL`: Local Ollama URL (default: http://localhost:11434/api/chat)
- `TURSO_URL`: Turso database URL
- `TURSO_AUTH_TOKEN`: Turso authentication token

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env` or Render dashboard
3. For Turso: Create database and run schema:

```sql
CREATE TABLE coaches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE avatars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    public INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0
);
```

4. Run locally: `uvicorn gateway:app --reload`
5. Deploy to Render with Procfile

## Routes

- `GET /`: API info and available routes
- `GET /healthz`: Health check
- `GET /diagnostic`: Connection diagnostics
- `POST /ai/chat`: Chat with AI
- `POST /ai/admin`: Admin actions
- `POST /ai/coach/admin`: Coach management
- `GET /ai/avatar/public`: Get public avatars
- `POST /ai/avatar/public`: Interact with avatars
- `POST /api/chat`: Legacy chat
- `POST /api/admin`: Legacy admin
- `POST /local/chat`: Local Ollama chat

## Deployment

Deployed on Render at api.onlymatt.ca. Push changes to GitHub for auto-deploy.