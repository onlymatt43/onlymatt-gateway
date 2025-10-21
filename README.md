# ONLYMATT Gateway

Gateway API pour l'assistant AI, déployé sur Render avec Turso et Cloudflare.

## Configuration

### 1. Render
- Créez un service Web sur Render
- Connectez le repo GitHub
- Définissez les variables d'environnement :
  - `OM_ADMIN_KEY`: Clé admin (générez une clé sécurisée)
  - `AI_BACKEND`: URL du backend AI (optionnel)
  - `OLLAMA_URL`: URL Ollama (optionnel)
  - `TURSO_DB_URL`: URL de la base Turso (libsql:// ou https://)
  - `TURSO_DB_AUTH_TOKEN`: Token d'auth Turso

### 2. Turso
- Créez une base de données sur Turso
- Obtenez l'URL et le token
- Assurez-vous que l'URL commence par `libsql://` ou `https://`

### 3. Cloudflare
- Ajoutez le domaine om43.com à Cloudflare
- Configurez le DNS :
  - Type: CNAME
  - Name: @
  - Target: [votre-app].onrender.com
  - Proxy: Activé
- Dans Render, ajoutez le domaine personnalisé om43.com

### 4. Test
- Vérifiez `/health` pour la santé
- Vérifiez `/ai/tursocheck` pour Turso
- Vérifiez `/ai/libcheck` pour libsql-client

## Dépannage

### Problèmes courants
- **Turso connection failed**: Vérifiez TURSO_DB_URL et TURSO_DB_AUTH_TOKEN. L'URL doit être au format `libsql://` ou `https://`.
- **Domain not working**: Assurez-vous que le CNAME pointe vers [app].onrender.com et que le proxy Cloudflare est activé.
- **CORS errors**: Le domaine doit être dans la liste CORS (onlymatt.ca, om43.com, etc.).
- **Rate limit**: L'API a un rate limit de 60 req/min par IP.

### Logs Render
- Vérifiez les logs dans le dashboard Render pour les erreurs de démarrage.

## Développement local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # et remplissez
uvicorn gateway:app --reload
```

## Test
```bash
python test.py
```

## Fonctionnalités
- Proxy AI chat
- Stockage mémoire dans Turso
- Rate limiting
- CORS pour onlymatt.ca, om43.com, etc.