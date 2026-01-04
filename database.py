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
                    validation_status TEXT DEFAULT 'pending', -- pending, validated, rejected
                    assigned_theme TEXT,
                    validator_id INTEGER,
                    veilleur_initials TEXT,
                    canal TEXT,
                    source_media TEXT,
                    sub_theme TEXT,
                    content_summary TEXT,
                    audience TEXT,
                    publication_date TEXT,
                    recommended_action TEXT,
                    priority TEXT DEFAULT 'Modéré',
                    observation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'member', -- admin, member
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migration: Ajout des colonnes pour les bases existantes
            new_columns = [
                ("validation_status", "TEXT DEFAULT 'pending'"),
                ("assigned_theme", "TEXT"),
                ("validator_id", "INTEGER"),
                ("veilleur_initials", "TEXT"),
                ("canal", "TEXT"),
                ("source_media", "TEXT"),
                ("sub_theme", "TEXT"),
                ("content_summary", "TEXT"),
                ("audience", "TEXT"),
                ("publication_date", "TEXT"),
                ("recommended_action", "TEXT"),
                ("priority", "TEXT DEFAULT 'Modéré'"),
                ("observation", "TEXT")
            ]
            
            for col_name, col_type in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass # Colonne existe déjà
            
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_validation ON articles(validation_status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_theme ON articles(assigned_theme)
            ''')
            
            logger.info(f"Base de données initialisée: {self.db_path}")
    
    def insert_article(self, platform: str, author: str, content: str, 
                      media_type: str, sentiment: str, url: str,
                      veilleur_initials: str = None, canal: str = None, 
                      source_media: str = None, sub_theme: str = None,
                      content_summary: str = None, audience: str = None,
                      publication_date: str = None, recommended_action: str = None,
                      priority: str = 'Modéré', observation: str = None,
                      assigned_theme: str = None) -> int:
        """
        Insère un nouvel article avec les champs enrichis CCDP
        
        Returns:
            ID de l'article inséré
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO articles (
                    date, platform, author, content, media_type, sentiment, url,
                    veilleur_initials, canal, source_media, sub_theme, content_summary,
                    audience, publication_date, recommended_action, priority, observation, assigned_theme
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(), platform, author, content, media_type, sentiment, url,
                veilleur_initials, canal, source_media, sub_theme, content_summary,
                audience, publication_date, recommended_action, priority, observation, assigned_theme
            ))
            
            article_id = cursor.lastrowid
            logger.info(f"Article inséré: ID={article_id}, Platform={platform}, Thème={assigned_theme}")
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
                SELECT id, date, platform, author, content, media_type, sentiment, url, validation_status,
                       veilleur_initials, canal, source_media, sub_theme, content_summary, audience, 
                       publication_date, recommended_action, priority, observation
                FROM articles
                ORDER BY date DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_articles_by_platform(self, limit_per_platform: int = 50, theme: str = None) -> List[Dict]:
        """
        Récupère les N articles les plus récents pour CHAQUE plateforme.
        Évite que les plateformes à gros volume n'écrasent les autres dans une limite globale.
        
        Args:
            limit_per_platform: Nombre d'articles par plateforme
            theme: Filtre optionnel par thème (pour les membres)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if theme:
                # Avec filtre thématique
                cursor.execute('''
                    WITH RankedArticles AS (
                        SELECT id, date, platform, author, content, media_type, sentiment, url, validation_status,
                               veilleur_initials, canal, source_media, sub_theme, content_summary, audience, 
                               publication_date, recommended_action, priority, observation, assigned_theme,
                               ROW_NUMBER() OVER (PARTITION BY platform ORDER BY date DESC) as rank
                        FROM articles
                        WHERE assigned_theme = ?
                    )
                    SELECT id, date, platform, author, content, media_type, sentiment, url, validation_status,
                           veilleur_initials, canal, source_media, sub_theme, content_summary, audience, 
                           publication_date, recommended_action, priority, observation
                    FROM RankedArticles
                    WHERE rank <= ?
                    ORDER BY platform, date DESC
                ''', (theme, limit_per_platform))
            else:
                # Sans filtre (admin)
                cursor.execute('''
                    WITH RankedArticles AS (
                        SELECT id, date, platform, author, content, media_type, sentiment, url, validation_status,
                               veilleur_initials, canal, source_media, sub_theme, content_summary, audience, 
                               publication_date, recommended_action, priority, observation,
                               ROW_NUMBER() OVER (PARTITION BY platform ORDER BY date DESC) as rank
                        FROM articles
                    )
                    SELECT id, date, platform, author, content, media_type, sentiment, url, validation_status,
                           veilleur_initials, canal, source_media, sub_theme, content_summary, audience, 
                           publication_date, recommended_action, priority, observation
                    FROM RankedArticles
                    WHERE rank <= ?
                    ORDER BY platform, date DESC
                ''', (limit_per_platform,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """Récupère un article par son ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, date, platform, author, content, media_type, sentiment, url,
                       veilleur_initials, canal, source_media, sub_theme, content_summary, 
                       audience, publication_date, recommended_action, priority, observation
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
        allowed_fields = {
            'author', 'content', 'sentiment', 'url', 
            'veilleur_initials', 'canal', 'source_media', 'sub_theme', 
            'content_summary', 'audience', 'publication_date', 
            'recommended_action', 'priority', 'observation', 'assigned_theme'
        }
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
    
    def get_statistics(self, theme: str = None) -> Dict:
        """
        Calcule les statistiques globales
        
        Args:
            theme: Filtre optionnel par thème (pour les membres)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clause WHERE conditionnelle
            where_clause = 'WHERE assigned_theme = ?' if theme else ''
            params = (theme,) if theme else ()
            
            # Total
            cursor.execute(f'SELECT COUNT(*) FROM articles {where_clause}', params)
            total = cursor.fetchone()[0]
            
            # Par sentiment
            cursor.execute(f'''
                SELECT sentiment, COUNT(*) as count
                FROM articles
                {where_clause}
                GROUP BY sentiment
            ''', params)
            sentiment_counts = {row['sentiment']: row['count'] for row in cursor.fetchall()}
            
            # Par type de média
            cursor.execute(f'''
                SELECT media_type, COUNT(*) as count
                FROM articles
                {where_clause}
                GROUP BY media_type
            ''', params)
            media_counts = {row['media_type']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total': total,
                'positif': sentiment_counts.get('Positif', 0),
                'negatif': sentiment_counts.get('Négatif', 0),
                'neutre': sentiment_counts.get('Neutre', 0),
                'mixte': sentiment_counts.get('Mixte', 0),
                'media_types': media_counts
            }
    
    def get_sentiment_trends(self, period: str = 'day', limit: int = 30, theme: str = None) -> List[Dict]:
        """
        Récupère les tendances de sentiment par période
        
        Args:
            period: Période de groupement (day, week, month, year)
            limit: Nombre de périodes à retourner
            theme: Filtre optionnel par thème (pour les membres)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Définir le format de date et le filtre de temps pour SQLite
            if period == 'week':
                date_fmt = '%Y-%W' # Année-Semaine
                time_filter = f'-{limit} weeks' 
            elif period == 'month':
                date_fmt = '%Y-%m' # Année-Mois
                time_filter = f'-{limit} months'
            elif period == 'year':
                date_fmt = '%Y'    # Année
                time_filter = f'-{limit} years'
            else: # day par défaut
                date_fmt = '%Y-%m-%d'
                time_filter = f'-{limit} days'

            # Clause WHERE avec filtre thématique si nécessaire
            where_clause = 'WHERE date >= date(\'now\', ?)'
            params = [time_filter]
            
            if theme:
                where_clause += ' AND assigned_theme = ?'
                params.append(theme)
            
            # On utilise strftime pour le groupement
            query = f'''
                SELECT strftime('{date_fmt}', date) as time_label, sentiment, COUNT(*) as count
                FROM articles
                {where_clause}
                GROUP BY time_label, sentiment
                ORDER BY time_label ASC
            '''
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]

    def get_executive_summary(self) -> Dict:
        """Récupère les KPIs de haut niveau pour le dashboard décideurs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            cursor.execute('''
                SELECT canal, COUNT(*) as count 
                FROM articles 
                WHERE canal IS NOT NULL AND canal != ''
                GROUP BY canal
            ''')
            canal_counts = {row['canal']: row['count'] for row in cursor.fetchall()}
            return {
                "total": total,
                "canaux": canal_counts,
                "social": canal_counts.get("Réseaux Sociaux", 0),
                "web": canal_counts.get("Presse en ligne", 0),
                "tv": canal_counts.get("Télévision", 0),
                "radio": canal_counts.get("Radio", 0),
                "press": canal_counts.get("Presse écrite", 0)
            }

    def get_theme_analysis(self) -> List[Dict]:
        """Récupère le volume et la tonalité par thématique"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT assigned_theme, sentiment, COUNT(*) as count
                FROM articles
                WHERE assigned_theme IS NOT NULL AND assigned_theme != ''
                GROUP BY assigned_theme, sentiment
                ORDER BY assigned_theme
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_weekly_evolution(self, weeks: int = 8) -> List[Dict]:
        """Récupère l'évolution du volume sur les N dernières semaines"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT strftime('%Y-W%W', date) as week, COUNT(*) as count
                FROM articles
                WHERE date >= date('now', '-{weeks * 7} days')
                GROUP BY week
                ORDER BY week ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_top_sources_distribution(self, limit: int = 15) -> List[Dict]:
        """Récupère les sources les plus fréquentes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT author as source, COUNT(*) as count
                FROM articles
                WHERE author IS NOT NULL AND author != ''
                GROUP BY source
                ORDER BY count DESC
                LIMIT ?
            ''', (limit,))
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

    # --- GESTION UTILISATEURS ---

    def create_user(self, username: str, password_hash: str, role: str = 'member') -> int:
        """Crée un nouvel utilisateur"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role)
                    VALUES (?, ?, ?)
                ''', (username, password_hash, role))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Tentative de création d'utilisateur existant: {username}")
            return -1

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Récupère un utilisateur par son username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_users(self) -> List[Dict]:
        """Récupère tous les utilisateurs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    def update_user(self, user_id: int, password_hash: Optional[str] = None, role: Optional[str] = None) -> bool:
        """Met à jour un utilisateur (mdp ou rôle)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if password_hash and role:
                cursor.execute('UPDATE users SET password_hash = ?, role = ? WHERE id = ?', (password_hash, role, user_id))
            elif password_hash:
                cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
            elif role:
                cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user_id))
            else:
                return False
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            return cursor.rowcount > 0

    # --- VALIDATION FLOW ---

    def update_validation_status(self, article_id: int, status: str, validator_id: int, assigned_theme: Optional[str] = None) -> bool:
        """Met à jour le statut de validation d'un article et potentiellement sa thématique"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                UPDATE articles
                SET validation_status = ?, validator_id = ?, updated_at = CURRENT_TIMESTAMP
            '''
            params = [status, validator_id]
            
            if assigned_theme:
                query += ', assigned_theme = ?'
                params.append(assigned_theme)
                
            query += ' WHERE id = ?'
            params.append(article_id)
            
            cursor.execute(query, tuple(params))
            return cursor.rowcount > 0

    def get_articles_by_theme(self, theme: str, limit: int = 50) -> List[Dict]:
        """Récupère les articles pour une thématique donnée (pour un membre)"""
        # Note: Pour l'instant, le thème est soit assigné en base, soit on filtre par mot-clé
        # Ici on simule un filtre basique, à affiner selon comment les thèmes sont définis (keywords ?)
        # Pour le MVP, on suppose que theme == keyword présent dans le contenu
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Recherche textuelle simple pour le MVP si theme n'est pas assigné explicitement
            search_term = f"%{theme}%"
            cursor.execute('''
                SELECT * FROM articles
                WHERE (assigned_theme = ? OR content LIKE ?)
                ORDER BY date DESC
                LIMIT ?
            ''', (theme, search_term, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_validation_articles(self) -> List[Dict]:
        """Récupère les articles en attente de validation admin"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM articles
                WHERE validation_status = 'member_validated'
                ORDER BY updated_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

# Instance globale
db = Database()
