# Veille Niger - Système de Surveillance Médiatique

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Tailwind](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Système automatisé de veille médiatique pour le Niger, collectant et analysant des articles depuis Google News et les réseaux sociaux avec analyse de conscience IA et branding national aux couleurs du drapeau du Niger.

## 🚀 Fonctionnalités Majeures

- **🇳🇪 Branding National** : Interface entièrement refondue avec **Tailwind CSS** adoptant les couleurs du drapeau du Niger (Orange, Blanc, Vert).
- **📊 Dashboard Exécutif (Nouveau)** : Vue stratégique pour les décideurs avec 6 graphiques analytiques (Volume thématique, Sentiment, Évolution hebdomadaire).
- **🏢 Workflow Multi-Rôles** : Distinction claire entre **Administrateurs** (contrôle total) et **Membres** (focus par thématique).
- **🧩 Filtrage Thématique** : Auto-assignation intelligente des articles parmi 13 thématiques (Sécurité, Économie, Santé, etc.).
- **Deep Scraping** : Extraction complète du contenu des articles multi-plateformes (Google News, Facebook, X, LinkedIn, Instagram).
- **Analyse IA** : Analyse de tonalité (Sentiment) multilingue intégrée.
- **Paramétrage Dynamique** : Configuration simplifiée de Google Sheets et des thématiques via l'interface.
- **Conteneurisation** : Prêt pour la production avec Docker & Docker Compose.

## 📋 Prérequis

- Python 3.9+
- Chromium (installé automatiquement par Playwright)
- (Optionnel) Compte Google Cloud pour la synchronisation Sheets

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

# Éditer .env avec vos paramètres (Admin credentials, DB path, etc.)
notepad .env
```

## 🎯 Utilisation

### Lancer le serveur FastAPI
```bash
uvicorn main:app --reload
```
- **Dashboard Opérationnel** : http://localhost:8000/dashboard
- **Dashboard Décideurs** : http://localhost:8000/executive-dashboard (Admin uniquement)

### Lancer les Scrapers
```bash
# Scraping global
python scraper.py

# Scraping thématique ciblé (ex: Agriculture)
python scraper.py --theme "Agriculture"
```

## 📊 Architecture

```
veille_niger/
├── main.py                  # Serveur FastAPI & API
├── scraper.py               # Moteur de scraping thématique
├── database.py              # Gestion SQLite (ACID)
├── logger.py                # Logging avec rotation
├── keywords.py              # Mots-clés par thématique (13 thèmes)
├── templates/               # UI avec Tailwind CSS
│   ├── dashboard.html       # Dashboard Opérationnel 🇳🇪
│   ├── executive_dashboard.html # Dashboard Décideurs 📊
│   ├── login.html           # Interface de connexion
│   └── admin_users.html     # Gestion des utilisateurs
├── static/                  # Assets (Images, UI design)
└── .env                     # Secrets & Config
```

## 🔐 Sécurité & Rôles

- **Administrateur** : Gestion des utilisateurs, accès à la vue exécutive, validation finale.
- **Membre** : Consultation et validation des articles restreinte à leur thématique assignée.
- **Protection** : Sessions sécurisées, mots de passe hashés, isolation des credentials.

## 📝 Workflow de Validation

1. **Collecte** : Le scraper ingère les articles et auto-détecte la thématique.
2. **Revue** : Les membres filtrent et éditent les articles via le modal unifié.
3. **Certification** : Validation en un clic (Soumission par membre / Validation par admin).
4. **Diffusion** : Export automatique vers Google Sheets pour les articles certifiés.

## 📈 Performance

- **SQLite Optimized** : Indexation pour une recherche rapide sur > 100k articles.
- **Tailwind Ready** : UI légère, ultra-rapide et responsive.
- **Batch Processing** : Synchronisation Google API optimisée.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`feature/amelioration`)
3. Commit avec des messages descriptifs
4. Ouvrir une Pull Request

## 📄 Licence

MIT License - Projet Veille Niger

## 🙏 Remerciements

- [FastAPI](https://fastapi.tiangolo.com/) & [Tailwind CSS](https://tailwindcss.com/)
- [Playwright](https://playwright.dev/) & [Chart.js](https://www.chartjs.org/)
- République du Niger (Inspiration visuelle)
