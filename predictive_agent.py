import sqlite3
import time
import logging
from datetime import datetime, timedelta

# Configuration
DB_NAME = 'veille.db'
CHECK_INTERVAL_SECONDS = 30
VELOCITY_THRESHOLD = 3 # Alerte si plus de X commentaires
SENTIMENT_THRESHOLD = 60 # Alerte si plus de X% sont négatifs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PredictiveAgent")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def analyze_comments():
    """Analyse les commentaires récents pour détecter des bad buzz"""
    logger.info("Début du cycle d'analyse des commentaires...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Analyser la toute dernière fenêtre de 5 minutes
        time_window = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Obtenir les thèmes ayant des commentaires récents
        cursor.execute('''
            SELECT theme, COUNT(*) as count, 
                   SUM(CASE WHEN sentiment = 'Négatif' THEN 1 ELSE 0 END) as negative_count
            FROM comments
            WHERE scraped_at >= ?
            GROUP BY theme
        ''', (time_window,))
        
        recent_activity = cursor.fetchall()
        
        for row in recent_activity:
            theme = row['theme']
            total = row['count']
            negative = row['negative_count']
            
            if total > 0:
                neg_ratio = (negative / total) * 100
                logger.info(f"Theme '{theme}': {total} commentaires dans les 5 dernières min ({neg_ratio:.1f}% négatifs)")
                
                # Condition d'Agent Prédictif (Bad Buzz en cours)
                if total >= VELOCITY_THRESHOLD and neg_ratio >= SENTIMENT_THRESHOLD:
                    logger.warning(f"⚠️ ALERTE PREDICTIVE ⚠️ Activité anormale sur le thème: {theme}")
                    
                    # Vérifier si on a déjà un incident ouvert pour ce thème récemment
                    cursor.execute('''
                        SELECT id FROM incidents 
                        WHERE theme = ? AND status = 'Active' 
                        AND created_at >= datetime('now', '-1 hour')
                    ''', (theme,))
                    
                    if not cursor.fetchone():
                        # Déclarer un nouvel Incident
                        title = f"Potentiel Bad Buzz : {theme}"
                        desc = f"Une augmentation anormale de commentaires négatifs a été détectée ({total} commentaires en 5 min, dont {neg_ratio:.0f}% négatifs)."
                        severity = "High" if neg_ratio > 80 else "Medium"
                        
                        cursor.execute('''
                            INSERT INTO incidents (title, description, severity, theme, related_platform)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (title, desc, severity, theme, 'Multiple'))
                        
                        logger.error(f"🔴 NOUVEL INCIDENT CRÉÉ DANS LA BASE : {title}")
                        conn.commit()
                    else:
                        logger.info(f"Incident déjà existant pour {theme}. Pas de doublon.")
                        
    except Exception as e:
        logger.error(f"Erreur Predictive Agent: {e}", exc_info=True)
    finally:
        conn.close()

def main():
    logger.info("Agent Prédictif Démarré.")
    while True:
        analyze_comments()
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
