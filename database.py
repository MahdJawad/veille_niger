"""
Gestion de la base de données SQLite pour Veille Niger
Remplace le stockage CSV pour de meilleures performances et concurrence
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import pandas as pd
from logger import setup_logger
from config import DATABASE_PATH

logger = setup_logger(__name__)

class Database:
    """Gestionnaire de base de données SQLite avec support des transactions"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager pour gérer les connexions avec auto-commit/rollback"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur base de données, rollback: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialise la base de données et crée les tables si nécessaire"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table articles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    author TEXT,
                    content TEXT NOT NULL,
                    media_type TEXT,
                    sentiment TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index pour améliorer les performances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_date ON articles(date DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_platform ON articles(platform)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sentiment ON articles(sentiment)
            ''')
            
            logger.info(f"Base de données initialisée: {self.db_path}")
    
    def insert_article(self, platform: str, author: str, content: str, 
                      media_type: str, sentiment: str, url: str) -> int:
        """
        Insère un nouvel article
        
        Returns:
            ID de l'article inséré
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO articles (date, platform, author, content, media_type, sentiment, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), platform, author, content, media_type, sentiment, url))
            
            article_id = cursor.lastrowid
            logger.info(f"Article inséré: ID={article_id}, Platform={platform}")
            return article_id
    
    def get_articles(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Récupère les articles avec pagination
        
        Args:
            limit: Nombre d'articles à retourner
            offset: Décalage pour la pagination
        
        Returns:
            Liste de dictionnaires représentant les articles
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, date, platform, author, content, media_type, sentiment, url
                FROM articles
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """Récupère un article par son ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, date, platform, author, content, media_type, sentiment, url
                FROM articles
                WHERE id = ?
            ''', (article_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_article(self, article_id: int, **kwargs) -> bool:
        """
        Met à jour un article
        
        Args:
            article_id: ID de l'article
            **kwargs: Champs à mettre à jour (author, content, sentiment, url)
        
        Returns:
            True si mis à jour, False sinon
        """
        allowed_fields = {'author', 'content', 'sentiment', 'url'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        set_clause += ', updated_at = ?'
        values = list(updates.values()) + [datetime.now().isoformat(), article_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE articles
                SET {set_clause}
                WHERE id = ?
            ''', values)
            
            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Article mis à jour: ID={article_id}")
            return updated
    
    def get_statistics(self) -> Dict:
        """Calcule les statistiques globales"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total
            cursor.execute('SELECT COUNT(*) FROM articles')
            total = cursor.fetchone()[0]
            
            # Par sentiment
            cursor.execute('''
                SELECT sentiment, COUNT(*) as count
                FROM articles
                GROUP BY sentiment
            ''')
            sentiment_counts = {row['sentiment']: row['count'] for row in cursor.fetchall()}
            
            # Par type de média
            cursor.execute('''
                SELECT media_type, COUNT(*) as count
                FROM articles
                GROUP BY media_type
            ''')
            media_counts = {row['media_type']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total': total,
                'positif': sentiment_counts.get('Positif', 0),
                'negatif': sentiment_counts.get('Négatif', 0),
                'neutre': sentiment_counts.get('Neutre', 0),
                'media_types': media_counts
            }
    
    def get_sentiment_trends(self, days: int = 7) -> List[Dict]:
        """
        Récupère les tendances de sentiment sur les derniers X jours
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # On utilise substr(date, 1, 10) car date est stocké en ISO (YYYY-MM-DDTHH:MM:SS)
            cursor.execute('''
                SELECT substr(date, 1, 10) as day, sentiment, COUNT(*) as count
                FROM articles
                WHERE date >= date('now', ?)
                GROUP BY day, sentiment
                ORDER BY day ASC
            ''', (f'-{days} days',))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Exporte tous les articles vers un DataFrame pandas"""
        with self.get_connection() as conn:
            return pd.read_sql_query('''
                SELECT date as "Date", platform as "Plateforme", author as "Auteur",
                       content as "Contenu", media_type as "Type Média", 
                       sentiment as "Tonalité", url as "URL"
                FROM articles
                ORDER BY date DESC
            ''', conn)
    
    def migrate_from_csv(self, csv_path: str) -> int:
        """
        Migre les données depuis un fichier CSV existant
        
        Returns:
            Nombre d'articles migrés
        """
        try:
            df = pd.read_csv(csv_path)
            count = 0
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for _, row in df.iterrows():
                    try:
                        cursor.execute('''
                            INSERT INTO articles (date, platform, author, content, media_type, sentiment, url)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row.get('Date', datetime.now().isoformat()),
                            row.get('Plateforme', 'Unknown'),
                            row.get('Auteur', ''),
                            row.get('Contenu', ''),
                            row.get('Type Média', ''),
                            row.get('Tonalité', ''),
                            row.get('URL', '')
                        ))
                        count += 1
                    except Exception as e:
                        logger.warning(f"Erreur migration ligne: {e}")
                        continue
            
            logger.info(f"Migration CSV terminée: {count} articles")
            return count
        
        except Exception as e:
            logger.error(f"Erreur migration CSV: {e}", exc_info=True)
            return 0

# Instance globale
db = Database()
