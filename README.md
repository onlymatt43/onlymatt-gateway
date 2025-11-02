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

## WordPress Plugin

- Le plugin WordPress officiel vit dans `onlymatt-wp-plugin-main-6/` (fichier principal `onlymatt-ai.php`). Modifiez toujours cette copie pour éviter les divergences.
- Pour synchroniser vers une instance WordPress locale (par défaut `~/Downloads/public_html/wp-content/plugins/onlymatt-wp-plugin`), exécutez `./onlymatt-wp-plugin-main-6/sync-to-wordpress.sh`. Ajoutez `--dry-run` pour voir les opérations et `--safe` pour éviter de supprimer les fichiers supplémentaires côté WordPress.
- Passez un chemin personnalisé avec `--dest /chemin/vers/wp-content/plugins/onlymatt-wp-plugin` si votre installation n'est pas sous `Downloads/`.
- La copie située dans `Downloads/public_html/wp-content/plugins/onlymatt-wp-plugin/` est la version déployée sur votre WordPress local : ne l'éditez pas directement, relancez plutôt la synchronisation après toute modification.
- Après chaque modification du backend (`gateway.py`) qui impacte les appels AJAX (`/ai/chat`, `/admin/tasks`, `/ai/memory/*`, `/ai/website/*`), synchronisez le plugin puis rafraîchissez le cache WordPress pour vérifier les flux.
- Pour om43.com, un helper `./onlymatt-wp-plugin-main-6/configure-om43.sh [chemin_wordpress]` met à jour automatiquement l'API Base (`https://api.om43.com`) et les options principales via WP-CLI.

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

## 🌐 Génération de sites web

L'AI peut analyser des sites web de référence et générer des sites web personnalisés.

### Analyser un site web de référence

```bash
curl -X POST https://api.om43.com/ai/website/analyze \
  -H "x-om-key: ta-cle-admin" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com"}'
```

### Générer un site web complet

```bash
curl -X POST https://api.om43.com/ai/website/generate \
  -H "x-om-key: ta-cle-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "site_data": {
      "name": "Ma Société",
      "industry": "technology",
      "description": "Solutions innovantes",
      "services": ["Web", "Mobile", "IA"],
      "contact": {"email": "contact@site.com"}
    },
    "references": ["https://site1.com", "https://site2.com"],
    "template": "modern",
    "target_platform": "wordpress",
    "wordpress_config": {
      "url": "https://mon-site.com",
      "username": "admin",
      "password": "motdepasse"
    }
  }'
```