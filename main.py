"""
Système de Veille Niger - API FastAPI
Version refactorisée avec SQLite, logging structuré, et google-auth
"""
import datetime
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials
from transformers import pipeline
import json
import os
import secrets
from fastapi import Form


# Imports locaux
from config import (
    API_HOST, API_PORT, GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_NAME,
    GA_MEASUREMENT_ID, GA_API_SECRET, ADMIN_USERNAME, ADMIN_PASSWORD
)
from logger import setup_logger
from database import db
import requests

# Configuration
logger = setup_logger(__name__)
app = FastAPI(title="Système de Veille Niger")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- AUTHENTIFICATION ---
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Vérifie les identifiants Basic Auth"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# --- LAZY LOADING DU MODÈLE IA ---
_sentiment_pipeline = None

def get_sentiment_pipeline():
    """Charge le modèle IA uniquement à la première utilisation (lazy loading)"""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Chargement du modèle de sentiment léger (DistilBERT)...")
        _sentiment_pipeline = pipeline(
            "sentiment-analysis", 
            model="lxyuan/distilbert-base-multilingual-cased-sentiments-student"
        )
        logger.info("Modèle IA chargé avec succès")
    return _sentiment_pipeline

# --- GOOGLE SHEETS (avec google-auth) ---
def get_sheet():
    """Connexion à Google Sheets avec google-auth (remplace oauth2client)"""
    try:
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE,
            scopes=scopes
        )
        client = gspread.authorize(creds)
        
        try:
            sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        except gspread.SpreadsheetNotFound:
            logger.info(f"Création de la feuille {GOOGLE_SHEET_NAME}")
            sheet = client.create(GOOGLE_SHEET_NAME).sheet1
            sheet.append_row(["Date", "Plateforme", "Auteur", "Contenu", "Type Média", "Tonalité", "URL"])
        
        return sheet
    except FileNotFoundError:
        logger.warning(f"Fichier credentials non trouvé: {GOOGLE_CREDENTIALS_FILE}")
        return None
    except Exception as e:
        logger.error(f"Erreur connexion Google Sheets: {e}", exc_info=True)
        return None

# --- MODÈLES DE DONNÉES ---
class SocialPost(BaseModel):
    platform: str
    author: str
    content: str
    media_type: str
    url: str

class ArticleUpdate(BaseModel):
    author: Optional[str] = None
    content: Optional[str] = None
    sentiment: Optional[str] = None
    url: Optional[str] = None

# --- LOGIQUE MÉTIER ---

def send_to_ga4(platform: str, sentiment: str, media_type: str):
    """Envoie un événement à Google Analytics 4"""
    if not GA_MEASUREMENT_ID or not GA_API_SECRET:
        return
    
    url = f"https://www.google-analytics.com/mp/collect?measurement_id={GA_MEASUREMENT_ID}&api_secret={GA_API_SECRET}"
    payload = {
        "client_id": "scraper_bot",
        "events": [{
            "name": "social_post_detected",
            "params": {
                "platform": platform,
                "sentiment": sentiment,
                "content_type": media_type
            }
        }]
    }
    
    try:
        requests.post(url, json=payload, timeout=2)
    except Exception as e:
        logger.warning(f"Erreur envoi GA4: {e}")

def process_data(post: SocialPost):
    """Traite un post: analyse sentiment, sauvegarde DB, sync Sheets optionnel"""
    try:
        # A. Analyse de Sentiment (lazy loading)
        sentiment_model = get_sentiment_pipeline()
        result = sentiment_model(post.content[:512])[0]
        label = result['label'].lower()
        
        if 'negative' in label:
            tonality = "Négatif"
        elif 'positive' in label:
            tonality = "Positif"
        else:
            tonality = "Neutre"
        
        # B. Sauvegarde SQLite (thread-safe avec transactions)
        try:
            article_id = db.insert_article(
                platform=post.platform,
                author=post.author,
                content=post.content,
                media_type=post.media_type,
                sentiment=tonality,
                url=post.url
            )
            logger.info(f"Article sauvegardé: ID={article_id}, Platform={post.platform}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde DB: {e}", exc_info=True)
            return
        
        # C. Sauvegarde Google Sheets (désactivée par défaut, utiliser le bouton manuel)
        # Pour activer : configurer un vrai credentials.json depuis Google Cloud Console
        # Voir GOOGLE_SHEETS_SETUP.md pour les instructions
        """
        sheet = get_sheet()
        if sheet:
            try:
                row_data = [
                    datetime.datetime.now().isoformat(),
                    post.platform,
                    post.author,
                    post.content,
                    post.media_type,
                    tonality,
                    post.url
                ]
                sheet.append_row(row_data)
                logger.debug("Article synchronisé vers Google Sheets")
            except Exception as e:
                logger.warning(f"Erreur sync Sheets: {e}")
        """
        
        # D. Analytics
        send_to_ga4(post.platform, tonality, post.media_type)
        
    except Exception as e:
        logger.error(f"Erreur process_data: {e}", exc_info=True)

# --- ENDPOINTS API ---

@app.post("/ingest")
async def ingest_post(post: SocialPost, background_tasks: BackgroundTasks):
    """Reçoit les données du Scraper"""
    background_tasks.add_task(process_data, post)
    return {"status": "Processing", "author": post.author}

@app.get("/api/article/{article_id}")
async def get_article(article_id: int, user: str = Depends(authenticate)):
    """Récupère un article par son ID pour édition"""
    article = db.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article

@app.put("/api/article/{article_id}")
async def update_article(article_id: int, update: ArticleUpdate, user: str = Depends(authenticate)):
    """Met à jour un article après vérification par l'agent de veille"""

    # Filtrer les champs non-None
    updates = {k: v for k, v in update.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune mise à jour fournie")
    
    success = db.update_article(article_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    return {"success": True, "message": "Article mis à jour"}

@app.post("/api/sync-to-sheets")
async def sync_to_sheets(user: str = Depends(authenticate)):
    """Synchronise tous les articles validés vers Google Sheets (batch update optimisé)"""

    try:
        sheet = get_sheet()
        if not sheet:
            raise HTTPException(
                status_code=503,
                detail="Google Sheets non configuré. Consultez GOOGLE_SHEETS_SETUP.md"
            )
        
        # Récupérer toutes les données
        df = db.export_to_dataframe()
        
        # Batch update optimisé (1 seule requête au lieu de N)
        sheet.clear()
        
        # Préparer les données
        headers = ["Date", "Plateforme", "Auteur", "Contenu", "Type Média", "Tonalité", "URL"]
        values = [headers] + df.values.tolist()
        
        # Update en une seule fois
        sheet.update('A1', values)
        
        logger.info(f"Synchronisation Sheets réussie: {len(df)} articles")
        
        return {
            "success": True,
            "message": f"{len(df)} articles synchronisés vers Google Sheets",
            "count": len(df)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur sync Sheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request, user: str = Depends(authenticate)):
    """Affiche le Dashboard depuis SQLite avec tableaux par plateforme"""

    try:
        # Statistiques globales
        stats = db.get_statistics()
        
        # Récupérer tous les articles récents
        all_articles = db.get_articles(limit=200)
        
        # Grouper par plateforme
        platforms = {}
        platform_stats = {}
        
        for article in all_articles:
            platform = article.get('platform', 'Unknown')
            
            # Initialiser la plateforme si nécessaire
            if platform not in platforms:
                platforms[platform] = []
                platform_stats[platform] = {'total': 0, 'positif': 0, 'negatif': 0, 'neutre': 0}
            
            # Formater pour le template
            formatted_article = {
                'id': article['id'],
                'Date': article['date'],
                'Plateforme': platform,
                'Auteur': article['author'],
                'Contenu': article['content'],
                'Type Média': article['media_type'],
                'Tonalité': article['sentiment'],
                'URL': article['url']
            }
            
            platforms[platform].append(formatted_article)
            
            # Statistiques par plateforme
            platform_stats[platform]['total'] += 1
            sentiment = article['sentiment']
            if sentiment == 'Positif':
                platform_stats[platform]['positif'] += 1
            elif sentiment == 'Négatif':
                platform_stats[platform]['negatif'] += 1
            else:
                platform_stats[platform]['neutre'] += 1
        
        # Limiter à 20 articles par plateforme pour l'affichage
        for platform in platforms:
            platforms[platform] = platforms[platform][:20]
        
        # Récupérer les tendances de sentiment (7 derniers jours)
        trends = db.get_sentiment_trends(days=7)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": stats,
            "platforms": platforms,
            "platform_stats": platform_stats,
            "sentiment_trends": trends,  # Nouvelles données pour les graphiques
            "posts": all_articles[:50]  # Pour compatibilité
        })
    except Exception as e:
        logger.error(f"Erreur Dashboard: {e}", exc_info=True)
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": {"total": 0, "positif": 0, "negatif": 0, "neutre": 0},
            "platforms": {},
            "platform_stats": {},
            "posts": [],
            "error": str(e)
        })

@app.get("/settings", response_class=HTMLResponse)
async def get_settings(request: Request, user: str = Depends(authenticate)):
    """Affiche la page de paramètres"""
    from config import GOOGLE_SHEET_NAME, GOOGLE_CREDENTIALS_FILE
    
    credentials_content = ""
    client_email = ""
    if os.path.exists(GOOGLE_CREDENTIALS_FILE):
        try:
            with open(GOOGLE_CREDENTIALS_FILE, 'r') as f:
                credentials_content = f.read()
                # Extraire le client_email pour aider l'utilisateur
                try:
                    data = json.loads(credentials_content)
                    client_email = data.get("client_email", "")
                except:
                    pass
        except:
            pass
            
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": {
            "GOOGLE_SHEET_NAME": GOOGLE_SHEET_NAME,
            "CLIENT_EMAIL": client_email
        },
        "credentials_content": credentials_content
    })

@app.post("/settings")
async def save_settings(
    request: Request,
    google_sheet_name: str = Form(...),
    credentials_json: str = Form(...),
    user: str = Depends(authenticate)
):
    """Sauvegarde les paramètres et met à jour le fichier .env et credentials.json"""
    from config import GOOGLE_CREDENTIALS_FILE
    
    try:
        # 1. Sauvegarder credentials.json
        if credentials_json.strip():
            # Valider que c'est du JSON valide
            json.loads(credentials_json)
            with open(GOOGLE_CREDENTIALS_FILE, 'w') as f:
                f.write(credentials_json)
        
        # 2. Mettre à jour .env
        env_lines = []
        found_sheet = False
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("GOOGLE_SHEET_NAME="):
                        env_lines.append(f"GOOGLE_SHEET_NAME={google_sheet_name}\n")
                        found_sheet = True
                    else:
                        env_lines.append(line)
        
        if not found_sheet:
            env_lines.append(f"GOOGLE_SHEET_NAME={google_sheet_name}\n")
            
        with open(".env", "w") as f:
            f.writelines(env_lines)
            
        # 3. Mettre à jour les variables globales (recharge manuelle car reload=True en dev)
        import config
        config.GOOGLE_SHEET_NAME = google_sheet_name
        
        logger.info(f"Paramètres mis à jour. Nouvelle feuille: {google_sheet_name}")
        return RedirectResponse(url="/dashboard", status_code=303)
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde paramètres: {e}")
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "config": {"GOOGLE_SHEET_NAME": google_sheet_name},
            "credentials_content": credentials_json,
            "message": f"Erreur: {str(e)}",
            "messageType": "error"
        })

# --- MIGRATION CSV → SQLite au démarrage ---
@app.on_event("startup")
async def startup_event():
    """Migre les données CSV existantes vers SQLite si nécessaire"""
    import os
    csv_path = "data.csv"
    
    if os.path.exists(csv_path):
        # Vérifier si la DB est vide
        stats = db.get_statistics()
        if stats['total'] == 0:
            logger.info("Migration des données CSV vers SQLite...")
            count = db.migrate_from_csv(csv_path)
            logger.info(f"Migration terminée: {count} articles")
        else:
            logger.info(f"Base de données déjà peuplée: {stats['total']} articles")
    
    logger.info("Application démarrée avec succès")

# Pour lancer : uvicorn main:app --reload
