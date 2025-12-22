# Veille Niger - Système de Surveillance Médiatique

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Système automatisé de veille médiatique pour le Niger, collectant et analysant des articles depuis Google News et les réseaux sociaux avec analyse de sentiment IA.

## 🚀 Fonctionnalités

- **Deep Scraping** : Extraction complète du contenu des articles (pas seulement les snippets)
- **Multi-plateformes** : Google News, Twitter/X, Instagram, LinkedIn, Facebook
- **Analyse IA** : Sentiment analysis multilingue avec BERT
- **Visualisation de données** : Graphiques interactifs (disque et courbe) avec Chart.js
- **Dashboard sécurisé** : Authentification Basic Auth configurable
- **Paramétrage dynamique** : Configuration Google Sheets simplifiée via l'interface
- **Stockage robuste** : SQLite + synchronisation Google Sheets batch
- **Logging structuré** : Rotation automatique des logs
- **Conteneurisation** : Docker & Docker Compose prêts pour le déploiement

## 📋 Prérequis

- Python 3.9+
- Chromium (installé automatiquement par Playwright)
- (Optionnel) Compte Google Cloud pour Google Sheets

## 🔧 Installation

### 1. Cloner le projet
```bash
git clone <votre-repo>
cd veille_niger
```

### 2. Créer un environnement virtuel
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate  # Linux/Mac
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configuration
```bash
# Copier le template de configuration
copy .env.example .env

# Éditer .env avec vos paramètres
notepad .env
```

**Variables importantes** :
- `API_URL` : URL de l'API (défaut: http://localhost:8000/ingest)
- `SCRAPER_HEADLESS` : true pour mode invisible, false pour debug
- `DATABASE_PATH` : Chemin de la base SQLite (défaut: veille.db)

### 5. (Optionnel) Configurer Google Sheets
Suivez le guide détaillé dans `GOOGLE_SHEETS_SETUP.md`

## 🎯 Utilisation

### Lancer le serveur FastAPI
```bash
uvicorn main:app --reload
```
Dashboard accessible sur : http://localhost:8000/dashboard

### Lancer le scraper Google News
```bash
python scraper.py
```

### Lancer le scraper réseaux sociaux
```bash
python scraper_social.py
```

### Déploiement Docker
```bash
docker-compose up -d --build
```
Consultez `DEPLOYMENT.md` pour plus de détails.

## 📊 Architecture

```
veille_niger/
├── main.py              # API FastAPI
├── scraper.py           # Scraper Google News
├── scraper_social.py    # Scraper réseaux sociaux
├── database.py          # Gestion SQLite
├── logger.py            # Configuration logging
├── config.py            # Variables d'environnement
├── keywords.py          # Mots-clés de surveillance
├── templates/           # Templates HTML
│   └── dashboard.html
├── static/              # Assets statiques
│   └── images/
├── logs/                # Fichiers de logs
└── .env                 # Configuration (non versionné)
```

## 🔐 Sécurité

- ✅ Credentials dans `.env` (non versionné)
- ✅ Migration vers `google-auth` (oauth2client déprécié)
- ✅ Validation des entrées avec Pydantic
- ✅ Transactions SQLite (ACID)

## 🧪 Tests

```bash
pytest tests/
```

## 📝 Workflow de Validation

1. Agents consultent le dashboard
2. Cliquent "Éditer" pour corriger/enrichir les articles
3. Vérifient les liens avec "Voir la source"
4. Clic "Synchroniser vers Google Sheets" après validation

## 🐛 Dépannage

### Le scraper ne trouve pas d'articles
- Vérifiez `debug_page.html` pour analyser la structure HTML
- Google peut servir différentes mises en page selon le user-agent

### Erreur "Module not found"
```bash
pip install -r requirements.txt --upgrade
```

### Base de données corrompue
```bash
# Sauvegarder les données
python -c "from database import db; df = db.export_to_dataframe(); df.to_csv('backup.csv')"

# Supprimer et recréer
rm veille.db
python main.py  # Recrée la DB
```

## 📈 Performance

- **SQLite** : Jusqu'à 100k articles sans ralentissement
- **Lazy loading IA** : Modèle chargé uniquement à la première utilisation
- **Batch updates** : Google Sheets sync en 1 requête au lieu de N

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - voir `LICENSE`

## 👥 Auteurs

Projet Veille Niger - Système de surveillance médiatique

## 🙏 Remerciements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Playwright](https://playwright.dev/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
