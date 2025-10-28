#!/bin/bash
echo "=== Vérification des logs WordPress ==="
echo "Fichier debug.log:"
ls -la wp-content/debug.log
echo ""
echo "Contenu récent du log:"
tail -20 wp-content/debug.log
echo ""
echo "=== Vérification des permissions ==="
echo "Permissions du dossier plugins:"
ls -la wp-content/plugins/onlymatt-wp-plugin/
echo ""
echo "=== Test de syntaxe PHP ==="
php -l wp-content/plugins/onlymatt-wp-plugin/onlymatt-ai.php
echo ""
echo "=== Vérification des options WordPress ==="
wp option get onlymatt_api_base 2>/dev/null || echo "WP-CLI non disponible"
