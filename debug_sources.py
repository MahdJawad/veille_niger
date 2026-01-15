from database import db
import pandas as pd

def check_data_quality():
    with open("debug_output_canal.txt", "w", encoding="utf-8") as f:
        f.write("--- Database Data Quality Check ---\n")
        
        # Check total articles
        stats = db.get_statistics()
        f.write(f"Total Articles: {stats['total']}\n\n")
        
        # Check Canal Distribution
        f.write("--- distribution 'canal' ---\n")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT canal, COUNT(*) as c FROM articles GROUP BY canal")
            rows = cursor.fetchall()
            for r in rows:
                f.write(f"'{r['canal']}': {r['c']}\n")
                
        # Check Media Type Distribution (Alternative to Canal)
        f.write("\n--- distribution 'media_type' ---\n")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT media_type, COUNT(*) as c FROM articles GROUP BY media_type")
            rows = cursor.fetchall()
            for r in rows:
                f.write(f"'{r['media_type']}': {r['c']}\n")

        # Check Platform Distribution
        f.write("\n--- distribution 'platform' ---\n")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT platform, COUNT(*) as c FROM articles GROUP BY platform")
            rows = cursor.fetchall()
            for r in rows:
                f.write(f"'{r['platform']}': {r['c']}\n")

if __name__ == "__main__":
    check_data_quality()
