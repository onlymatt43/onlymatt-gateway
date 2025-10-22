# 🚀 OnlyMatt Gateway - Guide Complet de Configuration et Gestion

## 📋 CHECKLIST DES RÉGLAGES SYSTÈME

### 🔑 Services Externes (Obligatoires)

#### **1. API Groq (IA)**
- [ ] Créer un compte sur [groq.com](https://groq.com)
- [ ] Générer une clé API dans le dashboard
- [ ] Vérifier les crédits disponibles
- [ ] Tester l'API avec un appel simple

#### **2. Base de Données Turso**
- [ ] Créer un compte sur [turso.tech](https://turso.tech)
- [ ] Créer une nouvelle base de données
- [ ] Générer un token d'authentification
- [ ] Récupérer l'URL de la base de données
- [ ] Tester la connexion avec `libsql-client`

#### **3. Hébergement Render (Optionnel)**
- [ ] Créer un compte sur [render.com](https://render.com)
- [ ] Lier le compte GitHub
- [ ] Configurer les variables d'environnement
- [ ] Vérifier les limites du plan gratuit

#### **4. WordPress (Optionnel)**
- [ ] Installation WordPress fonctionnelle
- [ ] Plugin "Application Passwords" activé
- [ ] Génération d'un mot de passe d'application
- [ ] Permissions d'écriture sur l'API REST

### 🖥️ Configuration Système Local

#### **1. Environnement Python**
- [ ] Python 3.11+ installé
- [ ] `pip` à jour
- [ ] Virtualenv configuré
- [ ] Dépendances installées (`requirements.txt`)

#### **2. Variables d'Environnement**
- [ ] Fichier `.env` créé
- [ ] `OM_ADMIN_KEY` défini (clé d'admin)
- [ ] `GROQ_API_KEY` configuré
- [ ] `TURSO_DB_URL` défini
- [ ] `TURSO_DB_AUTH_TOKEN` configuré

#### **3. Permissions Système**
- [ ] Droits d'écriture sur le dossier `uploads/`
- [ ] Droits d'écriture sur le dossier `static/`
- [ ] Droits d'accès aux templates

---

## 🛠️ GUIDE PAS À PAS - NOUVELLE INSTALLATION

### **Étape 1: Préparation de l'Environnement**

```bash
# 1. Cloner le repository
git clone https://github.com/onlymatt43/onlymatt-gateway.git
cd onlymatt-gateway

# 2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Sur macOS/Linux
# ou venv\Scripts\activate sur Windows

# 3. Installer les dépendances
pip install -r requirements.txt
```

### **Étape 2: Configuration des Services Externes**

#### **Configuration Groq API**
```bash
# Créer le fichier .env
touch .env

# Ajouter la clé API Groq
echo "GROQ_API_KEY=votre_cle_api_groq" >> .env
```

#### **Configuration Turso Database**
```bash
# Ajouter les variables Turso
echo "TURSO_DB_URL=votre_url_turso" >> .env
echo "TURSO_DB_AUTH_TOKEN=votre_token_turso" >> .env
```

#### **Configuration Admin**
```bash
# Générer une clé d'admin sécurisée
python3 -c "import secrets; print(secrets.token_hex(16))"
# Copier la clé générée et l'ajouter :
echo "OM_ADMIN_KEY=votre_cle_admin" >> .env
```

### **Étape 3: Test Local**

```bash
# 1. Tester l'import
python3 -c "import gateway; print('✅ Import réussi')"

# 2. Lancer le serveur local
uvicorn gateway:app --host 127.0.0.1 --port 8000 --reload

# 3. Tester les endpoints dans un autre terminal
curl http://localhost:8000/health
curl -H "x-om-key: votre_cle_admin" http://localhost:8000/ai/health
```

### **Étape 4: Déploiement sur Render**

#### **Via GitHub (Recommandé)**
```bash
# 1. Pousser les changements
git add .
git commit -m "Configuration initiale"
git push origin main

# 2. Sur Render.com :
# - Créer un nouveau "Web Service"
# - Connecter le repository GitHub
# - Configurer les variables d'environnement
# - Déployer
```

#### **Variables d'Environnement sur Render**
```
OM_ADMIN_KEY = votre_cle_admin
GROQ_API_KEY = votre_cle_groq
TURSO_DB_URL = votre_url_turso
TURSO_DB_AUTH_TOKEN = votre_token_turso
AI_BACKEND = groq
```

### **Étape 5: Configuration WordPress (Optionnel)**

```bash
# 1. Dans WordPress Admin > Users > Your Profile
# 2. Activer "Application Passwords"
# 3. Générer un nouveau mot de passe d'application
# 4. L'ajouter aux variables d'environnement :
echo "WORDPRESS_URL=https://votresite.com" >> .env
echo "WORDPRESS_USER=votre_username" >> .env
echo "WORDPRESS_APP_PASSWORD=votre_mot_de_passe_app" >> .env
```

---

## 🔄 GESTION AU QUOTIDIEN

### **Démarrage Quotidien**

#### **1. Vérification du Statut**
```bash
# Vérifier que tout fonctionne
curl https://votre-app.render.com/health
curl -H "x-om-key: votre_cle" https://votre-app.render.com/ai/health
```

#### **2. Monitoring des Logs**
- **Sur Render**: Dashboard > Service > Logs
- **Local**: Terminal avec `uvicorn --log-level info`
- **Erreurs communes**:
  - API Groq épuisée → Vérifier crédits
  - DB Turso inaccessible → Vérifier token/URL
  - WordPress 401 → Régénérer Application Password

### **Maintenance Régulière**

#### **Hebdomadaire**
- [ ] Vérifier les logs pour erreurs
- [ ] Tester les endpoints principaux
- [ ] Vérifier l'espace disque (uploads/)
- [ ] Mettre à jour les dépendances si nécessaire

#### **Mensuel**
- [ ] Vérifier les crédits Groq
- [ ] Sauvegarder la configuration
- [ ] Tester la génération complète de site
- [ ] Vérifier les performances

### **Résolution des Problèmes Courants**

#### **Erreur 500 - Import Failed**
```bash
# Vérifier les dépendances
pip install -r requirements.txt
python3 -c "import gateway"
```

#### **Erreur 401 - Auth Failed**
```bash
# Vérifier la clé admin
curl -H "x-om-key: VOTRE_CLE" https://votre-app.com/ai/health
```

#### **Erreur 400 - AI Failed**
```bash
# Vérifier les crédits Groq
curl -H "Authorization: Bearer VOTRE_CLE_GROQ" \
  https://api.groq.com/openai/v1/models
```

#### **Erreur DB Connection**
```bash
# Tester la connexion Turso
python3 -c "
import os
from libsql_client import create_client
client = create_client(
    url=os.getenv('TURSO_DB_URL'),
    auth_token=os.getenv('TURSO_DB_AUTH_TOKEN')
)
result = client.execute('SELECT 1')
print('✅ DB OK' if result.rows else '❌ DB Failed')
"
```

### **Workflow de Développement**

#### **Ajouter une Nouvelle Fonctionnalité**
```bash
# 1. Créer une branche
git checkout -b feature/nouvelle-fonction

# 2. Développer et tester localement
# 3. Commiter les changements
git add .
git commit -m "feat: nouvelle fonctionnalité"

# 4. Tester sur staging si disponible
# 5. Merger dans main
git checkout main
git merge feature/nouvelle-fonction
git push origin main
```

#### **Mise à Jour de Production**
```bash
# Après push sur main, Render déploie automatiquement
# Vérifier les logs de déploiement
# Tester les nouvelles fonctionnalités
```

### **Sauvegarde et Sécurité**

#### **Données à Sauvegarder**
- [ ] Variables d'environnement (`.env`)
- [ ] Configuration Render
- [ ] Clés API (sécurisées)
- [ ] Données importantes en base

#### **Sécurité**
- [ ] Clés API jamais dans le code
- [ ] Variables d'environnement validées
- [ ] Logs ne contiennent pas d'informations sensibles
- [ ] Mises à jour de sécurité régulières

---

## 📞 Support et Dépannage

### **Ressources Utiles**
- **Documentation FastAPI**: https://fastapi.tiangolo.com/
- **API Groq**: https://console.groq.com/docs/
- **Turso Docs**: https://docs.turso.tech/
- **Render Guide**: https://docs.render.com/

### **Commandes Utiles**
```bash
# Redémarrer le service Render
# Dashboard Render > Manual Deploy

# Vérifier les variables d'environnement
env | grep -E "(GROQ|TURSO|OM_)"

# Tester tous les endpoints
python3 test_website.py
python3 test_upload.py
```

---

**🎯 Checklist Finale :**
- [ ] Services externes configurés
- [ ] Installation terminée
- [ ] Tests réussis
- [ ] Déploiement opérationnel
- [ ] Monitoring en place

**Votre OnlyMatt Gateway est prêt ! 🚀**</content>
<parameter name="filePath">/Users/mathieucourchesne/Downloads/onlymatt-gateway/CONFIGURATION_GUIDE.md