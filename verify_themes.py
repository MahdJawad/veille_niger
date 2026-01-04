"""
Script de vérification pour tester l'assignation des thèmes et le filtrage membre.
"""
import sqlite3
from config import DATABASE_PATH

def verify_themes():
    """Vérifie l'état de l'assignation des thèmes dans la base de données."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"\n📊 VÉRIFICATION DE LA BASE DE DONNÉES: {DATABASE_PATH}\n")
    print("=" * 70)
    
    # Total d'articles
    cursor.execute("SELECT COUNT(*) FROM articles")
    total = cursor.fetchone()[0]
    print(f"\n✅ Total d'articles: {total}")
    
    # Articles avec thème
    cursor.execute("SELECT COUNT(*) FROM articles WHERE assigned_theme IS NOT NULL AND assigned_theme != ''")
    with_theme = cursor.fetchone()[0]
    print(f"✅ Articles avec thème assigné: {with_theme}")
    print(f"❌ Articles sans thème: {total - with_theme}")
    
    # Répartition par thème
    print(f"\n📈 RÉPARTITION PAR THÈME:")
    print("-" * 70)
    cursor.execute('''
        SELECT assigned_theme, COUNT(*) as count
        FROM articles
        WHERE assigned_theme IS NOT NULL
        GROUP BY assigned_theme
        ORDER BY count DESC
    ''')
    
    for row in cursor.fetchall():
        theme = row['assigned_theme']
        count = row['count']
        bar = "█" * min(count, 50)
        print(f"{theme:25} | {count:4} | {bar}")
    
    # Exemples d'articles par thème
    print(f"\n📝 EXEMPLES D'ARTICLES PAR THÈME:")
    print("-" * 70)
    cursor.execute('''
        SELECT assigned_theme, content, author
        FROM articles
        WHERE assigned_theme IS NOT NULL
        GROUP BY assigned_theme
        LIMIT 5
    ''')
    
    for row in cursor.fetchall():
        theme = row['assigned_theme']
        content = (row['content'] or '')[:100]
        author = row['author'] or 'Inconnu'
        print(f"\n🏷️  {theme}")
        print(f"   Auteur: {author}")
        print(f"   Contenu: {content}...")
    
    conn.close()
    print("\n" + "=" * 70)
    print("✨ Vérification terminée!\n")

if __name__ == "__main__":
    verify_themes()
