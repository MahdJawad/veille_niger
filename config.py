"""
Configuration centralisée pour l'application Veille Niger
Charge les variables d'environnement et fournit des valeurs par défaut
"""
import os
from pathlib import Path
from typing import Optional

# Charger les variables d'environnement depuis .env si présent
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optionnel

# Chemins
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/ingest")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Google Sheets
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Veille_Niger_Data")

# Google Analytics
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")
GA_API_SECRET = os.getenv("GA_API_SECRET", "")

# Scraper
SCRAPER_HEADLESS = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "60000"))
ARTICLE_TIMEOUT = int(os.getenv("ARTICLE_TIMEOUT", "45000"))
MAX_ARTICLES_PER_KEYWORD = int(os.getenv("MAX_ARTICLES_PER_KEYWORD", "10"))

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "veille.db")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_DIR / "veille.log"))
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# User Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Authentication
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "veille2024") # À changer en production

