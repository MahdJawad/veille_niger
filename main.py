"""
Système de Veille Niger - API FastAPI
Version refactorisée avec SQLite, logging structuré, et google-auth
"""
import datetime
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends, Response, Cookie
import subprocess
import sys
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import gspread
from google.oauth2.service_account import Credentials
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from passlib.context import CryptContext
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
from database import db
from keywords import MOTS_CLES_NIGER
from theme_configs import get_all_themes
import requests

# Configuration
logger = setup_logger(__name__)
app = FastAPI(title="Système de Veille Niger")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

templates = Jinja2Templates(directory="templates")

# --- AUTHENTIFICATION & SÉCURITÉ ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_user(request: Request):
    """
    Vérifie si l'utilisateur est connecté via session_id cookie (username).
    Retourne l'objet user (dict) complet ou None.
    """
    username = request.cookies.get("session_user")
    if not username:
        return None
        
    user = db.get_user_by_username(username)
    if not user:
        return None
        
    return user

@app.get("/")
async def root():
    """Redirection racine vers dashboard"""
    return RedirectResponse(url="/dashboard")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Affiche la page de connexion"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Gère la soumission du formulaire de connexion avec vérification DB"""
    user = db.get_user_by_username(username)
    
    if not user or not verify_password(password, user['password_hash']):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Identifiants invalides"
        })
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    # Définit un cookie de session (valable pour la session navigateur)
    response.set_cookie(key="session_user", value=user['username'], httponly=True)
    return response

@app.get("/theme-selection", response_class=HTMLResponse)
async def theme_selection_page(request: Request, user: dict = Depends(get_current_user)):
    """Page de sélection de thématique pour les membres"""
    if not user:
        return RedirectResponse(url="/login")
    if user['role'] == 'admin':
        return RedirectResponse(url="/dashboard")
        
    return templates.TemplateResponse("theme_selection.html", {
        "request": request, 
        "user": user,
        "themes": get_all_themes()
    })

def launch_theme_scraper(theme: str):
    """Lance un scraper dédié pour le thème en arrière-plan (subprocess)"""
    try:
        logger.info(f"🚀 Lancement sous-scraper pour le thème: {theme}")
        # Lancer scraper.py --theme "Theme Name" dans un processus séparé
        # On utilise sys.executable pour garantir qu'on utilise le même venv
        subprocess.Popen(
            [sys.executable, "scraper.py", "--theme", theme],
            cwd=os.getcwd(),
            # On laisse stdout/stderr gérés par le système ou redirigés si besoin de debug
            # Pour la prod, on pourrait mettre subprocess.DEVNULL
        )
    except Exception as e:
        logger.error(f"Erreur lancement sous-scraper: {e}")

@app.post("/theme-selection")
async def set_theme(request: Request, background_tasks: BackgroundTasks, theme: List[str] = Form(...), user: dict = Depends(get_current_user)):
    """Enregistre les thèmes choisis dans un cookie et lance les scrapers dédiés"""
    if not user:
        return RedirectResponse(url="/login")

    # Lancer le scraper spécifique pour chaque thème en background
    for t in theme:
        background_tasks.add_task(launch_theme_scraper, t)
        
    response = RedirectResponse(url="/dashboard", status_code=303)
    # Stocker sous forme de liste séparée par des virgules
    response.set_cookie(key="user_theme", value=",".join(theme), httponly=True)
    return response

@app.get("/logout")
async def logout():
    """Déconnecte l'utilisateur"""
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_user")
    response.delete_cookie("user_theme")
    return response

# --- LAZY LOADING DU MODÈLE IA ---
_sentiment_pipeline = None

def get_sentiment_pipeline():
    """Charge le modèle IA uniquement à la première utilisation (lazy loading)"""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Chargement du modèle IA de sentiment (BERT)...")
        # Fallback pour les systèmes avec peu de RAM
        try:
            model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Essai de chargement
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                low_cpu_mem_usage=False,
                device_map=None
            )
            model.to("cpu")
            
            _sentiment_pipeline = pipeline(
                "sentiment-analysis", 
                model=model,
                tokenizer=tokenizer,
                device=-1
            )
            logger.info("Modèle IA chargé avec succès")
            
        except (OSError, MemoryError, RuntimeError) as e:
            logger.error(f"ERREUR MÉMOIRE: Impossible de charger le modèle IA complet ({e}). Passage en mode 'Lite'.")
            logger.warning("Le système utilisera une analyse de sentiment simplifiée (Mock).")
            
            # Mock pipeline compatible avec l'interface de transformers
            # Retourne un score neutre par défaut pour éviter le crash
            def mock_pipeline(text, **kwargs):
                return [{'label': '3 stars', 'score': 0.5}] # 3 stars = Neutre
                
            _sentiment_pipeline = mock_pipeline
            
        except Exception as e:
            logger.error(f"FATAL: Erreur inattendue modèle IA: {e}")
            # On relance si c'est une autre erreur inconnue, ou on fallback aussi ?
            # Pour la stabilité, on fallback aussi.
            logger.warning("Activation du mode secours (pas d'IA).")
            def mock_pipeline_err(text, **kwargs):
                return [{'label': '3 stars', 'score': 0.0}]
            _sentiment_pipeline = mock_pipeline_err

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
    sentiment: Optional[str] = None
    # Nouveaux champs pour alignement CCDP
    veilleur_initials: Optional[str] = None
    canal: Optional[str] = None
    source_media: Optional[str] = None
    sub_theme: Optional[str] = None
    content_summary: Optional[str] = None
    audience: Optional[str] = None
    publication_date: Optional[str] = None
    recommended_action: Optional[str] = None
    priority: Optional[str] = "Modéré"
    observation: Optional[str] = None

class ArticleUpdate(BaseModel):
    author: Optional[str] = None
    content: Optional[str] = None
    sentiment: Optional[str] = None
    url: Optional[str] = None
    # Nouveaux champs pour alignement CCDP
    veilleur_initials: Optional[str] = None
    canal: Optional[str] = None
    source_media: Optional[str] = None
    sub_theme: Optional[str] = None
    content_summary: Optional[str] = None
    audience: Optional[str] = None
    publication_date: Optional[str] = None
    recommended_action: Optional[str] = None
    priority: Optional[str] = None
    observation: Optional[str] = None

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

# Dictionnaire de mots-clés pour la détection automatique de thème
THEME_KEYWORDS = {
    "Agriculture": ["agriculture", "agricole", "cultivateur", "récolte", "paysan", "fermier", "irrigation", "semence", "bétail", "élevage"],
    "Culture": ["culture", "culturel", "art", "artiste", "musique", "cinéma", "festival", "théâtre", "patrimoine", "spectacle"],
    "Diplomatie": ["diplomatie", "diplomatique", "ambassade", "ambassadeur", "relations", "international", "coopération", "bilatéral"],
    "Économie": ["économie", "économique", "finance", "financier", "budget", "investissement", "commerce", "marché", "entreprise", "croissance"],
    "Éducation": ["éducation", "éducatif", "école", "université", "étudiant", "enseignement", "formation", "académique", "apprentissage"],
    "Environnement": ["environnement", "environnemental", "climat", "climatique", "pollution", "écologie", "biodiversité", "durable", "écosystème"],
    "Gouvernance": ["gouvernance", "gouvernement", "administration", "administratif", "réforme", "institution", "public", "décentralisation"],
    "Numérique / TIC": ["numérique", "digital", "internet", "technologie", "informatique", "tic", "cyber", "innovation", "tech", "données"],
    "Politique": ["politique", "parti", "élection", "électoral", "président", "ministre", "parlement", "député", "opposition", "coalition"],
    "Santé": ["santé", "médical", "hôpital", "maladie", "vaccination", "soins", "patient", "médecin", "épidémie", "sanitaire"],
    "Sécurité": ["sécurité", "sécuritaire", "police", "armée", "militaire", "terrorisme", "criminalité", "défense", "conflit", "attaque"],
    "Sport": ["sport", "sportif", "football", "athlète", "compétition", "championnat", "équipe", "match", "joueur", "entraîneur"],
    "Société / Genre": ["société", "social", "femme", "genre", "égalité", "communauté", "jeunesse", "famille", "droits", "citoyen"]
}

def detect_theme(content: str, author: str = "") -> str:
    """
    Détecte automatiquement le thème d'un article basé sur son contenu.
    Utilise une approche par mots-clés pour classifier parmi les 13 thèmes disponibles.
    
    Args:
        content: Le contenu de l'article
        author: L'auteur (optionnel, pour contexte supplémentaire)
    
    Returns:
        Le thème détecté parmi les options CCDP
    """
    # Normaliser le texte pour la recherche
    text = f"{content} {author}".lower()
    
    # Compter les occurrences de mots-clés pour chaque thème
    theme_scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            theme_scores[theme] = score
    
    # Retourner le thème avec le score le plus élevé
    if theme_scores:
        detected_theme = max(theme_scores, key=theme_scores.get)
        logger.info(f"Thème détecté: {detected_theme} (score: {theme_scores[detected_theme]})")
        return detected_theme
    
    # Par défaut, retourner "Société / Genre" (thème le plus général)
    logger.info("Aucun thème spécifique détecté, assignation à 'Société / Genre'")
    return "Société / Genre"


def process_data(post: SocialPost):
    """Traite un post: analyse sentiment, sauvegarde DB, sync Sheets optionnel"""
    try:
        # A. Analyse de Sentiment (lazy loading)
        sentiment_model = get_sentiment_pipeline()
        result = sentiment_model(post.content[:512])[0]
        label = result['label']
        score = int(label.split()[0])
        
        if score <= 2:
            tonality = "Négatif"
        elif score == 3:
            tonality = "Neutre"
        else:
            tonality = "Positif"
        
        # B. Détection automatique du thème
        detected_theme = detect_theme(post.content, post.author)
        
        # C. Sauvegarde SQLite (thread-safe avec transactions)
        try:
            article_id = db.insert_article(
                platform=post.platform,
                author=post.author,
                content=post.content,
                media_type=post.media_type,
                sentiment=post.sentiment if post.sentiment else tonality,
                url=post.url,
                veilleur_initials=post.veilleur_initials,
                canal=post.canal,
                source_media=post.source_media,
                sub_theme=post.sub_theme,
                content_summary=post.content_summary,
                audience=post.audience,
                publication_date=post.publication_date,
                recommended_action=post.recommended_action,
                priority=post.priority,
                observation=post.observation,
                assigned_theme=detected_theme  # Thème détecté automatiquement
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
async def get_article(article_id: int, user: dict = Depends(get_current_user)):
    """Récupère un article par son ID pour édition"""
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")
    article = db.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article

@app.put("/api/article/{article_id}")
async def update_article(request: Request, article_id: int, update: ArticleUpdate, user: dict = Depends(get_current_user)):
    """Met à jour un article après vérification par l'agent de veille"""
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")

    # Filtrer les champs non-None
    updates = {k: v for k, v in update.dict().items() if v is not None}
    
    # Si c'est un membre qui modifie, assigner automatiquement son thème
    if user['role'] == 'member':
        user_theme = request.cookies.get("user_theme")
        if user_theme:
            updates['assigned_theme'] = user_theme
    
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune mise à jour fournie")
    
    success = db.update_article(article_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    return {"success": True, "message": "Article mis à jour"}

@app.post("/api/article/{article_id}/validate")
async def validate_article(request: Request, article_id: int, status: str = Form(...), user: dict = Depends(get_current_user)):
    """
    Change le statut de validation d'un article.
    Membres -> peuvent mettre 'member_validated' ou 'rejected'
    Admin -> peut mettre 'validated' ou 'rejected'
    """
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")
        
    # Vérification des droits simplifiée
    if user['role'] == 'member' and status == 'validated':
        raise HTTPException(status_code=403, detail="Seul l'admin peut valider définitivement")
        
    # Si membre valide, on passe en attente admin
    final_status = status
    user_theme = None
    
    if user['role'] == 'member':
        user_theme = request.cookies.get("user_theme")
        if status == 'validated_request':
            final_status = 'member_validated'
    
    success = db.update_validation_status(article_id, final_status, user['id'], assigned_theme=user_theme)
    if not success:
        raise HTTPException(status_code=404, detail="Article non trouvé")
        
    return {"success": True, "status": final_status}

# --- USER MANAGEMENT START ---

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, user: dict = Depends(get_current_user)):
    """Page de gestion des utilisateurs (Admin only)"""
    if not user or user['role'] != 'admin':
         return RedirectResponse(url="/dashboard", status_code=303)
    
    users = db.get_all_users()
    return templates.TemplateResponse("admin_users.html", {"request": request, "user": user, "users": users})

@app.post("/api/users")
async def create_new_user(
    username: str = Form(...), 
    password: str = Form(...), 
    role: str = Form(...), 
    user: dict = Depends(get_current_user)
):
    """API Crée un utilisateur"""
    if not user or user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    hashed_pwd = get_password_hash(password)
    user_id = db.create_user(username, hashed_pwd, role)
    
    if user_id == -1:
        return JSONResponse(status_code=400, content={"success": False, "error": "Utilisateur existe déjà"})
        
    return {"success": True, "id": user_id}

@app.put("/api/users/{user_id}")
async def update_existing_user(
    user_id: int,
    password: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """API Met à jour un utilisateur"""
    if not user or user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    pwd_hash = get_password_hash(password) if password else None
    
    success = db.update_user(user_id, pwd_hash, role)
    if not success:
         return JSONResponse(status_code=400, content={"success": False, "error": "Erreur update"})
         
    return {"success": True}

@app.delete("/api/users/{user_id}")
async def delete_existing_user(user_id: int, user: dict = Depends(get_current_user)):
    """API Supprime un utilisateur"""
    if not user or user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    # Prevent deleting self
    if user['id'] == user_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "Impossible de se supprimer soi-même"})

    success = db.delete_user(user_id)
    return {"success": success}

# --- USER MANAGEMENT END ---

@app.post("/api/sync-to-sheets")
async def sync_to_sheets(user: str = Depends(get_current_user)):
    """Synchronise tous les articles validés vers Google Sheets (batch update optimisé)"""
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")


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
    except Exception as e:
        logger.error(f"Erreur sync Sheets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/trends")
async def get_stats_trends(request: Request, period: str = 'day', limit: int = 30, user: dict = Depends(get_current_user)):
    """API pour récupérer les données du graphique avec filtre temporel (filtré par thème pour les membres)"""
    if not user:
         raise HTTPException(status_code=401, detail="Non autorisé")
    
    # Récupérer le thème du membre si applicable
    user_theme = None
    if user['role'] == 'member':
        user_theme = request.cookies.get("user_theme")
    
    try:
        trends = db.get_sentiment_trends(period=period, limit=limit, theme=user_theme)
        return trends
    except Exception as e:
        logger.error(f"Erreur API Trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request, user: dict = Depends(get_current_user)):
    """Affiche le Dashboard depuis SQLite avec tableaux par plateforme"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    user_theme = None
    all_articles = []
    
    # Logique spécifique Membre vs Admin
    if user['role'] == 'member':
        user_theme = request.cookies.get("user_theme")
        if not user_theme:
            # Force la sélection du thème même si on voit tout le dashboard
            return RedirectResponse(url="/theme-selection", status_code=303)
        


    try:
        # Statistiques globales (filtrées par thème pour les membres)
        stats = db.get_statistics(theme=user_theme)
        
        # Récupération de tous les posts récents par plateforme (filtrés par thème pour les membres)
        limit = 50
        raw_articles = db.get_recent_articles_by_platform(limit_per_platform=limit, theme=user_theme)
        
        # Groupement par plateforme
        all_articles_by_platform = {}
        for article in raw_articles:
            p = article['platform']
            if p not in all_articles_by_platform:
                all_articles_by_platform[p] = []
            all_articles_by_platform[p].append(article)

        # Extraction pour les variables spécifiques (compatibilité template)
        # Note: on utilise des clés exactes qui matchent la DB
        google_news_posts = all_articles_by_platform.get('Google News', [])
        # Fallback pour 'Google News (Deep)' si le nom diffère
        if not google_news_posts:
             google_news_posts = all_articles_by_platform.get('Google News (Deep)', [])

        facebook_posts = all_articles_by_platform.get('Facebook', [])
        linkedin_posts = all_articles_by_platform.get('LinkedIn', [])
        twitter_posts = all_articles_by_platform.get('Twitter', [])
        if not twitter_posts: # Fallback
             twitter_posts = all_articles_by_platform.get('Twitter/X', [])

        instagram_posts = all_articles_by_platform.get('Instagram', [])

        # Pour la vue "Vue Générale - Toutes Plateformes" (le grand tableau)
        # On peut réutiliser raw_articles directement car c'est déjà la liste de tout
        posts = list(raw_articles)
        # Tri par date décroissante
        posts.sort(key=lambda x: x.get('Date', '') or x.get('date', ''), reverse=True)
        posts = posts[:100] # Limite globale pour l'affichage

        # Structure pour le template
        platforms = {
            'Google News (Deep)': google_news_posts,
            'Facebook': facebook_posts,
            'LinkedIn': linkedin_posts,
            'Twitter/X': twitter_posts,
            'Instagram': instagram_posts,
        }
        
        # Merge avec les autres plateformes trouvées (catch-all)
        for p_name, p_arts in all_articles_by_platform.items():
            # Attention au mapping des noms d'affichage vs noms DB
            # On ajoute si ce n'est pas déjà plus ou moins couvert
            display_names = ['Google News (Deep)', 'Facebook', 'LinkedIn', 'Twitter/X', 'Instagram']
            # On fait simple: si la clé exacte n'est pas dans notre dictionnaire final
            if p_name not in ['Google News', 'Google News (Deep)', 'Facebook', 'LinkedIn', 'Twitter', 'Twitter/X', 'Instagram']:
                     platforms[p_name] = p_arts

        platform_stats = {}
        for name, articles in platforms.items():
            p_stats = {'total': len(articles), 'positif': 0, 'negatif': 0, 'neutre': 0}
            for article in articles:
                val = article.get('Tonalité') or article.get('sentiment') or 'Neutre'
                sentiment = str(val).lower()
                if 'positif' in sentiment:
                    p_stats['positif'] += 1
                elif 'négatif' in sentiment or 'negatif' in sentiment:
                    p_stats['negatif'] += 1
                else:
                    p_stats['neutre'] += 1
            platform_stats[name] = p_stats

        context = {
            "request": request,
            "posts": posts,
            "stats": stats,
            "platforms": platforms,
            "platform_stats": platform_stats,
            "user": user,
            "user_theme": user_theme,
            "sentiment_trends": db.get_sentiment_trends(period='day', limit=7, theme=user_theme)
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception as e:
        logger.error(f"Erreur Dashboard: {e}", exc_info=True)
        # On passe 'user' et 'sentiment_trends' vide pour éviter le crash Jinja
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user, 
            "stats": {"total": 0, "positif": 0, "negatif": 0, "neutre": 0},
            "platforms": {},
            "platform_stats": {},
            "posts": [],
            "sentiment_trends": [], # Important pour éviter UndefinedError
            "error": str(e)
        })

@app.get("/executive-dashboard", response_class=HTMLResponse)
async def executive_dashboard(request: Request, user: dict = Depends(get_current_user)):
    """Affiche le Dashboard Exécutif pour les décideurs"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        # Récupération des données agrégées
        summary = db.get_executive_summary()
        theme_stats = db.get_theme_analysis()
        weekly_trends = db.get_weekly_evolution(weeks=8)
        top_sources = db.get_top_sources_distribution(limit=15)
        
        # Préparation des données pour les graphiques (formatage JSON)
        # 1. Occurrence Thématique (Bar Chart)
        themes = {}
        for row in theme_stats:
            themes[row['assigned_theme']] = themes.get(row['assigned_theme'], 0) + row['count']
        
        # 2. Tonalité par Thématique (Stacked Bar Chart)
        theme_sentiments = {}
        for row in theme_stats:
            th = row['assigned_theme']
            sent = row['sentiment']
            if th not in theme_sentiments:
                theme_sentiments[th] = {"Positif": 0, "Neutre": 0, "Négatif": 0}
            theme_sentiments[th][sent] = row['count']

        context = {
            "request": request,
            "user": user,
            "summary": summary,
            "themes": themes,
            "theme_sentiments": theme_sentiments,
            "weekly_trends": weekly_trends,
            "top_sources": top_sources
        }
        return templates.TemplateResponse("executive_dashboard.html", context)
    except Exception as e:
        logger.error(f"Erreur Dashboard Exécutif: {e}", exc_info=True)
        return templates.TemplateResponse("executive_dashboard.html", {
            "request": request,
            "user": user,
            "error": str(e)
        })

@app.get("/settings", response_class=HTMLResponse)
async def get_settings(request: Request, user: str = Depends(get_current_user)):
    """Affiche la page de paramètres"""
    if not user:
        return RedirectResponse(url="/login", status_code=303)

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
    user: str = Depends(get_current_user)
):
    """Sauvegarde les paramètres et met à jour le fichier .env et credentials.json"""
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")

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
    
    # --- SEED ADMIN USER ---
    admin_user = db.get_user_by_username(ADMIN_USERNAME)
    if not admin_user:
        logger.info(f"Création de l'utilisateur Admin par défaut: {ADMIN_USERNAME}")
        hashed_pwd = get_password_hash(ADMIN_PASSWORD)
        db.create_user(ADMIN_USERNAME, hashed_pwd, role='admin')
    else:
        logger.info(f"Admin user '{ADMIN_USERNAME}' existe déjà.")
    
    logger.info("Application démarrée avec succès")

# Pour lancer : uvicorn main:app --reload
