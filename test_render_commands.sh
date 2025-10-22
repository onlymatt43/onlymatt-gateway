# Commandes de test pour votre app Render

# Remplacez VOTRE_APP_RENDER par l'URL réelle de votre app
# Exemple: https://onlymatt-gateway-xyz.onrender.com

# Health check de base
curl https://VOTRE_APP_RENDER/health

# Health check AI (avec clé admin)
curl -H 'x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f' \
     https://VOTRE_APP_RENDER/ai/health

# Test d'analyse de site web
curl -X POST https://VOTRE_APP_RENDER/ai/website/analyze \
     -H 'Content-Type: application/json' \
     -H 'x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f' \
     -d '{"url": "https://example.com"}'

# Test de génération de site
curl -X POST https://VOTRE_APP_RENDER/ai/website/generate \
     -H 'Content-Type: application/json' \
     -H 'x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f' \
     -d '{
       "site_data": {
         "name": "Test Company",
         "industry": "technology",
         "description": "AI-powered solutions"
       },
       "references": ["https://example.com"],
       "template": "modern",
       "target_platform": "static"
     }'
