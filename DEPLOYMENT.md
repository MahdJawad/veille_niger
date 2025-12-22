# Guide de Déploiement - Veille Niger

Ce document explique comment déployer l'application pour des tests ou pour la production.

## 1. Déploiement Local (Rapide)
C'est la méthode que vous utilisez actuellement.
```bash
# Lancer l'API
uvicorn main:app --reload

# Lancer le scraper (dans un autre terminal)
python scraper.py
```

## 2. Déploiement avec Docker (Recommandé pour le client)
Cette méthode garantit que l'application fonctionnera exactement de la même manière chez votre client.

### Prérequis
- Docker et Docker Compose installés sur la machine cible.

### Procédure
1. Copiez tous les fichiers du projet sur le serveur/PC cible.
2. Assurez-vous d'avoir votre fichier `.env` configuré.
3. Lancez la commande suivante à la racine du projet :
```bash
docker-compose up -d --build
```

### Avantages de Docker :
- **Isolation** : Pas besoin d'installer Python ou Chrome sur le PC client. Everything is inside.
- **Persistance** : Les données (`veille.db`) sont conservées même si le conteneur est arrêté.
- **Automatisation** : Le scraper tourne en boucle (toutes les 60 min par défaut).

## 3. Options d'Hébergement Cloud

### Option A : Render.com (Simple & Moderne)
1. Créez un compte sur [Render](https://render.com).
2. Créez un nouveau "Web Service" et connectez votre dépôt GitHub.
3. Render détectera automatiquement le `Dockerfile`.
4. Ajoutez vos variables d'environnement dans l'onglet "Environment" sur Render.
5. **Note** : Pour la base de données SQLite, utilisez un "Disk" (Volume) persistent sur Render pour ne pas perdre les données.

### Option B : Railway.app
1. Créez un projet sur [Railway](https://railway.app).
2. Liez votre GitHub et lancez le déploiement.
3. **Important :** Si vous avez une erreur "Railpack", allez dans **Settings** -> **Build** -> **Builder** et choisissez **DOCKER** manuellement.
4. L'application utilisera automatiquement le fichier `railway.json` que j'ai ajouté pour configurer le port `$PORT`.

#### Erreurs fréquentes sur Railway :
- **Build Plan Error** : Assurez-vous que le "Builder" est réglé sur **DOCKER** dans les paramètres Railway.
- **Port Error** : L'application doit écouter sur `$PORT`. J'ai mis à jour le `Dockerfile` et le `railway.json` pour cela.
- **Mémoire** : Le modèle d'analyse de sentiment (Bert) peut être gourmand. Si le build échoue par manque de mémoire (OOM), il faudra peut-être augmenter la mémoire du service sur Railway (plan payant requis parfois pour > 512Mo).

## 4. Configuration Post-Déploiement
Une fois déployé, n'oubliez pas de :
1. Accéder au dashboard via l'URL fournie (ex: `https://votre-app.render.com/dashboard`).
2. Aller dans **Paramètres** pour configurer Google Sheets si nécessaire.
3. Vérifier les logs pour s'assurer que le scraper collecte bien les données.

---
*Note : Pour un déploiement public, assurez-vous de sécuriser l'accès au dashboard (authentification basique recommandée).*
