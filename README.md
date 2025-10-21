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
- Configurez le DNS pour le sous-domaine API :
  - Type: CNAME
  - Name: api
  - Target: [votre-app].onrender.com
  - Proxy: Activé
- Dans Render, ajoutez le domaine personnalisé api.om43.com

### 4. Architecture finale
- `om43.com` → Votre site web principal
- `api.om43.com` → OnlyMatt Gateway API (Render)
- `www.api.om43.com` → Redirection vers api.om43.com

### 4. Test
- Vérifiez `/health` pour la santé
- Vérifiez `/ai/tursocheck` pour Turso
- Vérifiez `/ai/libcheck` pour libsql-client

## Dépannage

### Problèmes courants
- **Turso connection failed**: Vérifiez TURSO_DB_URL et TURSO_DB_AUTH_TOKEN. L'URL doit être au format `libsql://` ou `https://`.
- **Domain not working**: Assurez-vous que le CNAME pour `api` pointe vers [app].onrender.com et que le proxy Cloudflare est activé.
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

## 🏗️ Architecture

### Domaines et sous-domaines

| Domaine | Usage | Hébergement |
|---------|-------|-------------|
| `om43.com` | Site web principal | Votre hébergement (WordPress, etc.) |
| `api.om43.com` | OnlyMatt Gateway API | Render |
| `www.api.om43.com` | Redirection API | Render |

### Flux de données
```
Site web (om43.com) → API (api.om43.com) → Groq AI → Turso DB
```

## 🗂️ Gestion des fichiers

L'AI peut analyser et publier automatiquement vos fichiers desktop vers votre site web.

### Lister les fichiers desktop

```bash
curl "https://api.om43.com/ai/files/list?path=/Users/ton-nom/Desktop"
```

### Uploader et analyser un fichier

```bash
curl -X POST https://api.om43.com/ai/files/upload \
  -H "x-om-key: ta-cle-admin" \
  -F "file=@/chemin/vers/ton/fichier.txt" \
  -F "auto_publish=true" \
  -F "wordpress_url=https://om43.com" \
  -F "wordpress_user=ton-user" \
  -F "wordpress_password=ton-mdp"
```

### Lister les fichiers uploadés

```bash
curl https://api.om43.com/ai/files/uploads \
  -H "x-om-key: ta-cle-admin"
```