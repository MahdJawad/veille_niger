"""
Script de migration pour assigner automatiquement des thèmes aux articles existants.
Ce script analyse tous les articles sans thème assigné et leur attribue un thème basé sur leur contenu.

Usage: python migrate_themes.py
"""

import sqlite3
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dictionnaire de mots-clés (identique à main.py)
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
    """
    text = f"{content} {author}".lower()
    
    theme_scores = {}
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            theme_scores[theme] = score
    
    if theme_scores:
        return max(theme_scores, key=theme_scores.get)
    
    return "Société / Genre"

def migrate_themes():
    """
    Migre tous les articles existants sans thème assigné.
    """
    # Importer le chemin depuis config
    try:
        from config import DATABASE_PATH
        db_path = DATABASE_PATH
    except ImportError:
        db_path = "veille.db"  # Fallback
    
    logger.info(f"Utilisation de la base de données: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer tous les articles sans thème
        cursor.execute('''
            SELECT id, content, author
            FROM articles
            WHERE assigned_theme IS NULL OR assigned_theme = ''
        ''')
        
        articles = cursor.fetchall()
        total = len(articles)
        
        logger.info(f"Trouvé {total} articles sans thème assigné")
        
        if total == 0:
            logger.info("Aucune migration nécessaire")
            return
        
        # Traiter chaque article
        updated = 0
        for article in articles:
            article_id = article['id']
            content = article['content'] or ""
            author = article['author'] or ""
            
            # Détecter le thème
            theme = detect_theme(content, author)
            
            # Mettre à jour l'article
            cursor.execute('''
                UPDATE articles
                SET assigned_theme = ?, updated_at = ?
                WHERE id = ?
            ''', (theme, datetime.now().isoformat(), article_id))
            
            updated += 1
            
            if updated % 10 == 0:
                logger.info(f"Progression: {updated}/{total} articles traités")
        
        # Commit des changements
        conn.commit()
        logger.info(f"✅ Migration terminée: {updated} articles mis à jour")
        
        # Afficher les statistiques
        cursor.execute('''
            SELECT assigned_theme, COUNT(*) as count
            FROM articles
            WHERE assigned_theme IS NOT NULL
            GROUP BY assigned_theme
            ORDER BY count DESC
        ''')
        
        logger.info("\n📊 Répartition des thèmes:")
        for row in cursor.fetchall():
            logger.info(f"  - {row['assigned_theme']}: {row['count']} articles")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("🚀 Démarrage de la migration des thèmes...")
    migrate_themes()
    logger.info("✨ Migration terminée!")
