# 🧠 ONLYMATT GATEWAY — DEV GUIDE (LOCAL)

## 1️⃣ Rôle du Gateway
Le **OnlyMatt Gateway** agit comme une API locale entre ton IA (Ollama, OpenAI, etc.) et tes sites web (`onlymatt.ca`, `om43.com`, etc.).

Il :
- Reçoit les requêtes des sites web  
- Vérifie la clé `X-OM-KEY`  
- Transmet à ton modèle local (Ollama, etc.)  
- Retourne la réponse JSON  
- Peut démarrer automatiquement avec macOS via `launchctl`

---

## 2️⃣ Structure du dossier

📁 `/Users/mathieucourchesne/onlymatt-gateway/`

| Fichier / Dossier | Description | GitHub | Local |
|--------------------|-------------|:------:|:-----:|
| `gateway.py` | Code FastAPI principal | ✅ | ✅ |
| `requirements.txt` | Dépendances Python | ✅ | ✅ |
| `.gitignore` | Fichiers ignorés | ✅ | ✅ |
| `.dockerignore` | Pour future containerisation | ✅ | ✅ |
| `README.md` | Doc publique | ✅ | ✅ |
| `run_gateway.sh` | Script de lancement local | ❌ | ✅ |
| `.env` | Clés API sensibles | ❌ | ✅ |
| `.venv/` | Environnement Python | ❌ | ✅ |
| `gateway.log` | Log runtime | ❌ | ✅ |
| `gateway_error.log` | Log erreurs | ❌ | ✅ |
| `memory.db` | Base locale temporaire | ❌ | ✅ |
| `__pycache__/` | Cache Python | ❌ | ✅ |

---

## 3️⃣ Fichier `.env` (jamais versionné)

```bash
OM_GATEWAY_KEY=+1VRSn9FtM5iYoct99Lcf9EbTpSujPHsBAYRGJyitGc=
OM_ALLOWED_ORIGINS=https://onlymatt.ca,https://om43.com,https://api.onlymatt.ca,https://mattcourchesne.om43.com
OLLAMA_URL=http://127.0.0.1:11434
OPENAI_API_KEY=
GROK_API_KEY=
TURSO_DATABASE_URL=libsql://onlymatt-memory-onlymatt43.aws-us-east-2.turso.io
TURSO_AUTH_TOKEN=xxxxxx