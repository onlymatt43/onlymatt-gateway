# 🧪 Commandes de test pour OnlyMatt Gateway sur Render
# Remplacez VOTRE_APP_RENDER par l'URL réelle de votre app
# Exemple: https://onlymatt-gateway.onrender.com

echo "=== HEALTH CHECKS ==="

# Health check de base
echo "1. Health check de base:"
curl https://onlymatt-gateway.onrender.com/health

echo -e "\n2. Health check AI (avec clé admin):"
curl -H "x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f" \
     https://VOTRE_APP_RENDER/ai/health

echo -e "\n=== TESTS FONCTIONNELS ==="

# Test d'analyse de site web
echo -e "\n3. Test d'analyse de site web:"
curl -X POST https://VOTRE_APP_RENDER/ai/website/analyze \
     -H "Content-Type: application/json" \
     -H "x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f" \
     -d '{"url": "https://example.com"}'

# Test de génération de site
echo -e "\n4. Test de génération de site:"
curl -X POST https://VOTRE_APP_RENDER/ai/website/generate \
     -H "Content-Type: application/json" \
     -H "x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f" \
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

echo -e "\n=== INSTRUCTIONS ==="
echo "1. Remplacez VOTRE_APP_RENDER par votre URL Render réelle"
echo "2. Vérifiez que l'app est déployée et en ligne"
echo "3. Tous les tests devraient retourner du JSON valide"