import requests
import time
import random

API_URL = "http://localhost:8000/api/comments"
THEME = "Gouvernance"

# Simulation d'un "bad buzz"
negative_comments = [
    "C'est un véritable scandale ! Démission immédiate.",
    "Inacceptable, nous allons manifester demain.",
    "Encore de la corruption, honteux.",
    "Comment peut-on laisser passer ça ? Boycott total !",
    "La situation empire de jour en jour.",
    "C'est la goutte d'eau qui fait déborder le vase.",
    "Ils nous prennent vraiment pour des idiots."
]

positive_comments = [
    "Bonne initiative, à poursuivre.",
    "On constate une belle amélioration.",
    "Soutien total aux équipes."
]

def send_comment(content, author):
    payload = {
        "post_id": f"mock_post_{int(time.time())}",
        "platform": "Twitter",
        "author": author,
        "content": content,
        "theme": THEME
    }
    try:
        response = requests.post(API_URL, json=payload)
        print(f"[{response.status_code}] Comment envoyé : {content[:30]}...")
    except Exception as e:
        print(f"Erreur : {e}")

print("🚀 Démarrage de la simulation de Bad Buzz (Volume élevé, très négatif)...")

# Envoi de 10 commentaires rapidement (8 négatifs, 2 positifs)
for i in range(10):
    if i < 8:
        content = random.choice(negative_comments)
    else:
        content = random.choice(positive_comments)
        
    author = f"user_{random.randint(1000, 9999)}"
    send_comment(content, author)
    time.sleep(1) # Simule une forte vélocité

print("✅ Simulation terminée.")
print("👉 Vérifiez que 'predictive_agent.py' tourne en parallèle.")
print("👉 Après environ 30 secondes, l'agent devrait lever une Alerte et elle apparaîtra sur le Dashboard Exécutif.")
