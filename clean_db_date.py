"""
Script pour mettre à jour la base de données et nettoyer les anciennes données.
1. Ajoute les colonnes manquantes (publication_date, comments_count).
2. Supprime les articles antérieurs à 2023.
"""
import sqlite3
import os
from datetime import datetime
from config import DATABASE_PATH

def migrate_and_clean():
    print(f"Checking database at: {DATABASE_PATH}")
    if not os.path.exists(DATABASE_PATH):
        print("Database not found!")
        return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 1. Migration : Ajout des colonnes manquantes
        print("--- Migration Schema ---")
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN publication_date TEXT")
            print("Colonne 'publication_date' ajoutée.")
        except sqlite3.OperationalError:
            print("Colonne 'publication_date' existe déjà.")

        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN comments_count INTEGER DEFAULT 0")
            print("Colonne 'comments_count' ajoutée.")
        except sqlite3.OperationalError:
            print("Colonne 'comments_count' existe déjà.")

        # 2. Nettoyage : Suppression articles < 2023
        print("\n--- Nettoyage Dates ---")
        # On suppose que le champ 'date' est celui de l'insertion ou de la publication si disponible
        # On va baser le nettoyage sur le champ 'date' principal pour l'instant
        
        # Récupérer le nombre total d'articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_before = cursor.fetchone()[0]
        print(f"Articles avant nettoyage : {total_before}")
        
        # Supprimer articles dont la date commence par 2020, 2021, 2022
        years_to_remove = ['2020%', '2021%', '2022%']
        deleted_count = 0
        
        for year in years_to_remove:
            cursor.execute("DELETE FROM articles WHERE date LIKE ?", (year,))
            deleted_count += cursor.rowcount
            
        # Supprimer aussi ceux qui auraient une date vide ou invalide (si besoin)
        # cursor.execute("DELETE FROM articles WHERE date IS NULL OR date = ''")
        
        print(f"Articles supprimés (< 2023) : {deleted_count}")
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_after = cursor.fetchone()[0]
        print(f"Articles restants : {total_after}")

        conn.close()
        print("\nOpération terminée avec succès.")

    except Exception as e:
        print(f"Erreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_and_clean()
