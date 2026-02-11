"""
Script de réinitialisation de la base de données
Supprime tous les articles pour repartir à zéro
"""
import sqlite3
from config import DATABASE_PATH

def reset_articles():
    """Supprime tous les articles de la base de données"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Compter les articles avant suppression
        cursor.execute("SELECT COUNT(*) FROM articles")
        count_before = cursor.fetchone()[0]
        print(f"📊 Articles actuels dans la base : {count_before}")
        
        # Supprimer tous les articles
        cursor.execute("DELETE FROM articles")
        conn.commit()
        
        # Réinitialiser l'auto-increment
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
        conn.commit()
        
        print(f"✅ Base de données réinitialisée !")
        print(f"   - {count_before} articles supprimés")
        print(f"   - Compteur ID remis à 1")
        print(f"\n🚀 Vous pouvez maintenant lancer le scraper pour collecter de nouvelles données (2 semaines)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation : {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    confirmation = input("⚠️  ATTENTION : Cette action va supprimer TOUS les articles. Continuer ? (oui/non) : ")
    if confirmation.lower() in ['oui', 'yes', 'o', 'y']:
        reset_articles()
    else:
        print("❌ Opération annulée")
