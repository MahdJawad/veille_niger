"""
Script pour nettoyer les URLs Google redirect dans la base de données.
Convertit les URLs de type /url?q=... en URLs directes.
"""
import sqlite3
import urllib.parse
import os
from datetime import datetime
from config import DATABASE_PATH

def clean_google_url(url):
    """Nettoie une URL Google redirect et retourne l'URL réelle."""
    if not url:
        return url
    
    # Si c'est un lien Google redirect
    if "/url?" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # Chercher le paramètre 'url' ou 'q'
            if 'url' in query_params:
                return query_params['url'][0]
            elif 'q' in query_params:
                return query_params['q'][0]
        except Exception as e:
            print(f"Erreur lors du parsing de {url}: {e}")
            return url
    
    return url

def main():
    print(f"Checking database at: {DATABASE_PATH}")
    print(f"Database exists: {os.path.exists(DATABASE_PATH)}")
    
    # Connexion à la base de données
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Vérifier que la table existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        if not cursor.fetchone():
            print("ERROR: Table 'articles' does not exist!")
            conn.close()
            return
        
        # Récupérer tous les articles avec des URLs Google redirect
        cursor.execute("SELECT id, url FROM articles WHERE url LIKE '%/url?%'")
        articles = cursor.fetchall()
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Trouvé {len(articles)} URLs à nettoyer")
        
        cleaned_count = 0
        for article_id, old_url in articles:
            new_url = clean_google_url(old_url)
            
            if new_url != old_url:
                cursor.execute("UPDATE articles SET url = ? WHERE id = ?", (new_url, article_id))
                cleaned_count += 1
                print(f"  [{article_id}] {old_url[:80]}... -> {new_url[:80]}...")
        
        conn.commit()
        conn.close()
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Nettoyage terminé : {cleaned_count} URLs mises à jour")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
