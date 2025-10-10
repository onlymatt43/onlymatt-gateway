# ONLYMATT — Render Gateway

Gateway public (Render) qui proxifie vers `ai.onlymatt.ca` (Hostinger).

## Routes
- `POST /ai/chat`   → `https://ai.onlymatt.ca/chat/ai-chat.php`
- `POST /ai/admin`  → `https://ai.onlymatt.ca/admin/ai-admin.php` (envoie `X-OM-ADMIN-KEY` depuis ENV)
- `GET  /healthz`   → statut du gateway
- `GET  /ai/health` → alias

## Déploiement (Render)
1. Crée un **Web Service** → Python
2. Fichiers à la racine :
   - `gateway.py`
   - `requirements.txt`
   - `Procfile`
3. **Environment Variables** :
   - `AI_BACKEND=https://ai.onlymatt.ca`
   - `OM_ADMIN_KEY=sk_admin_xxxxx`
   - (optionnel) `ALLOWED_ORIGINS=https://onlymatt.ca,https://om43.com`
4. Auto-build → Start Command par défaut via `Procfile`:
   ```
   web: uvicorn gateway:app --host 0.0.0.0 --port $PORT
   ```

## Test rapide
```bash
# public
curl -s https://api.onlymatt.ca/ai/chat -H 'Content-Type: application/json' -d '{"message":"hello"}' | jq

# admin
curl -s https://api.onlymatt.ca/ai/admin -H 'Content-Type: application/json' -d '{"message":"status?"}' | jq
```
> L’admin est protégé car le gateway envoie `X-OM-ADMIN-KEY` au backend. La clé n’est **pas exposée** côté client.

## Notes
- Les secrets (GROQ_API_KEY) restent **sur Hostinger** (backend). Le gateway ne connaît pas cette clé.
- CORS autorise par défaut onlymatt.ca & om43.com (+ sous-domaines communs). Personnalise via `ALLOWED_ORIGINS`.
