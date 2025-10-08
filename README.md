# Résumé du Projet OnlyMatt Gateway & Prochaines Étapes

Ce document résume le travail accompli pour la mise en place de la passerelle AI et les actions restantes pour le déploiement en production.

---

## ✅ Ce qui a été fait (dans cet environnement de développement)

Nous avons entièrement configuré l'application de la passerelle et préparé l'intégration avec WordPress.

### 1. Passerelle AI (`onlymatt-gateway`)
- **Création du code source (`gateway.py`)** :
    - Utilisation du framework **FastAPI**.
    - Ajout des routes principales : `/chat`, `/history`, et `/settings`.
    - Mise en place d'une base de données **SQLite** (`memory.db`) pour gérer l'historique des conversations.
    - Sécurisation des points d'accès via une clé API (`X-OM-KEY`).
    - Configuration **CORS** pour autoriser les requêtes depuis tous les sous-domaines de `onlymatt.ca` et `localhost`.
- **Gestion des dépendances** :
    - Création du fichier `requirements.txt` listant toutes les librairies Python nécessaires.
    - Création d'un **environnement virtuel** (`.venv`) pour isoler le projet.
    - Installation de toutes les dépendances.
- **Fichiers de configuration** :
    - Création du fichier `.env` pour stocker les secrets et les URLs de configuration.
- **Lancement local** :
    - Le serveur de la passerelle a été lancé et tourne actuellement en arrière-plan sur cette machine.

### 2. Intégration WordPress (`ai-onlymatt-all`)
- **Mise à jour du script de l'avatar (`avatar.js`)** :
    - Le fichier a été modifié pour appeler la nouvelle passerelle à l'adresse `https://api.onlymatt.ca/chat`.
    - La logique pour envoyer le texte de l'utilisateur et déclencher la lecture de la réponse est en place.

### 3. Préparation pour la Production
- **Fichier de service (`onlymatt-gateway.service`)** :
    - Un fichier de configuration pour `systemd` a été créé. Il permettra de lancer la passerelle comme un service stable sur votre serveur.
- **Fichier de configuration Nginx (`nginx.conf`)** :
    - Un fichier de configuration pour Nginx a été créé pour agir comme reverse proxy, gérer le domaine `api.onlymatt.ca` et le sécuriser via HTTPS.

---

## 🚀 Ce qu'il reste à faire (sur votre serveur de production)

Les étapes suivantes doivent être réalisées manuellement sur votre serveur pour mettre le système en ligne.

### 1. Configuration du Nom de Domaine (DNS)
- Chez votre fournisseur de nom de domaine (là où vous avez acheté `onlymatt.ca`), créez un nouvel enregistrement de type **`A`**.
- **Sous-domaine** : `api`
- **Valeur** : L'adresse IP de votre serveur de production.

### 2. Déploiement des Fichiers
- Connectez-vous à votre serveur.
- Copiez l'intégralité du dossier `onlymatt-gateway` de votre machine locale vers le dossier `/opt/onlymatt-gateway` sur le serveur.

### 3. Mise en place du Service `systemd`
- Déplacez le fichier de service :
  ```bash
  sudo mv /opt/onlymatt-gateway/onlymatt-gateway.service /etc/systemd/system/
  ```
- Rechargez `systemd` et lancez le service :
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now onlymatt-gateway
  ```
- Vérifiez que le service tourne bien :
  ```bash
  sudo systemctl status onlymatt-gateway
  ```

### 4. Configuration de Nginx
- Déplacez le fichier de configuration Nginx :
  ```bash
  sudo mv /opt/onlymatt-gateway/nginx.conf /etc/nginx/sites-available/api.onlymatt.ca
  ```
- Activez le site en créant un lien symbolique :
  ```bash
  sudo ln -s /etc/nginx/sites-available/api.onlymatt.ca /etc/nginx/sites-enabled/
  ```
- Testez la configuration Nginx :
  ```bash
  sudo nginx -t
  ```

### 5. Sécurisation avec HTTPS (Let's Encrypt)
- Si ce n'est pas déjà fait, installez Certbot :
  ```bash
  sudo apt update && sudo apt install certbot python3-certbot-nginx
  ```
- Lancez Certbot pour obtenir et installer automatiquement un certificat SSL :
  ```bash
  sudo certbot --nginx -d api.onlymatt.ca
  ```
- Suivez les instructions. Certbot modifiera votre configuration Nginx pour activer le HTTPS.

### 6. Finalisation
- Rechargez Nginx pour appliquer toutes les modifications :
  ```bash
  sudo systemctl reload nginx
  ```
- Votre passerelle devrait maintenant être accessible et sécurisée à l'adresse `https://api.onlymatt.ca`. Vous pouvez tester avec `curl https://api.onlymatt.ca/settings -H "X-OM-KEY: change_me_super_secret"`.
