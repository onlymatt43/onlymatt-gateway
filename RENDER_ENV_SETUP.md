# 🛠️ Configuration des Variables d'Environnement Render

## Variables Requises pour l'AI Backend

Voici les variables d'environnement à configurer dans votre dashboard Render :

### **1. Clé d'Administration**
```
OM_ADMIN_KEY = VOTRE_CLE_ADMIN_ICI
```

### **2. Configuration AI Backend**
```
AI_BACKEND = groq
```

### **3. API Groq (IA)**
```
GROQ_API_KEY = VOTRE_CLE_API_GROQ_ICI
```

### **4. Ollama (Optionnel)**
```
OLLAMA_URL = (laisser vide si vous utilisez Groq)
```

### **5. Base de Données Turso**
```
TURSO_DB_URL = VOTRE_URL_TURSO_ICI
TURSO_DB_AUTH_TOKEN = VOTRE_TOKEN_TURSO_ICI
```

## 📋 Instructions pour Render

1. **Allez sur votre dashboard Render** : https://dashboard.render.com/
2. **Sélectionnez votre service** : `onlymatt-gateway`
3. **Allez dans l'onglet "Environment"**
4. **Ajoutez chaque variable** une par une :
   - Cliquez sur "Add Environment Variable"
   - Entrez le nom (ex: `GROQ_API_KEY`)
   - Entrez la valeur
   - Cliquez sur "Save"
5. **Redémarrez le service** : Allez dans l'onglet "Manual Deploy" et cliquez sur "Manual Deploy"

## 🔍 Autres Endroits à Vérifier

Voici d'autres endroits où vous pourriez vouloir mettre à jour des informations :

### **1. Clés API et URLs dans la Documentation**
- `CONFIGURATION_GUIDE.md` - Guide de configuration
- `README.md` - Documentation principale
- `test_render.sh` - Script de test

### **2. Clés API dans les Tests**
- `test_groq.py` - Tests spécifiques Groq
- `test_website.py` - Tests fonctionnels
- `test_upload.py` - Tests d'upload

### **3. URLs et Endpoints**
- URLs de callback WordPress
- URLs d'API externes
- URLs de base de données

### **4. Informations de Contact**
- Adresses email dans les templates HTML
- Numéros de téléphone
- Liens vers les réseaux sociaux

### **5. Configuration des Services Externes**
- **Groq API** : https://console.groq.com/
- **Turso Database** : https://turso.tech/
- **Render Dashboard** : https://dashboard.render.com/

## ⚠️ Sécurité Importante

- **Ne partagez jamais** vos vraies clés API dans le code ou GitHub
- **Utilisez toujours** les variables d'environnement
- **Vérifiez régulièrement** vos clés API pour éviter les fuites

## 🧪 Test Après Configuration

Après avoir ajouté les variables sur Render, testez avec :

```bash
# Test de santé AI
curl -H "x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f" \
     https://onlymatt-gateway.onrender.com/ai/health

# Test de génération de site (devrait maintenant fonctionner avec l'AI)
curl -X POST https://onlymatt-gateway.onrender.com/ai/website/generate \
     -H "Content-Type: application/json" \
     -H "x-om-key: sk_admin_e0e7fbda4b440ad82606c940d6fa084f" \
     -d '{"site_data": {"name": "Test AI", "industry": "tech"}, "references": ["https://example.com"]}'
```

Voulez-vous que je vous aide à identifier d'autres endroits spécifiques où mettre à jour des informations ?