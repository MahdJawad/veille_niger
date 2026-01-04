# Guide d'Utilisation du Scraping Thématique

## Vue d'Ensemble

Le système de scraping dispose maintenant de deux modes :
- **Mode Global (Admin)** : Utilise les mots-clés généraux de `keywords.py`
- **Mode Thématique (Membres)** : Utilise les mots-clés ciblés de `theme_configs.py`

## Modes de Scraping

### 1. Scraping Global (Admin)

Scrape tous les mots-clés généraux sans filtre thématique.

```bash
# Scraping unique
python scraper.py

# Scraping en boucle (toutes les 60 minutes)
python scraper.py --interval 60
```

### 2. Scraping d'un Thème Spécifique (Membre)

Scrape uniquement les mots-clés d'un thème particulier.

```bash
# Agriculture
python scraper.py --theme "Agriculture"

# Politique
python scraper.py --theme "Politique"

# Santé
python scraper.py --theme "Santé"
```

### 3. Scraping de Tous les Thèmes

Scrape séquentiellement tous les 13 thèmes.

```bash
python scraper.py --all-themes
```

## Thèmes Disponibles

1. Agriculture
2. Culture
3. Diplomatie
4. Économie
5. Éducation
6. Environnement
7. Gouvernance
8. Numérique / TIC
9. Politique
10. Santé
11. Sécurité
12. Sport
13. Société / Genre

## Exemples d'Utilisation

### Pour un Membre "Agriculture"

```bash
# Scraper uniquement les articles agricoles
python scraper.py --theme "Agriculture"
```

**Résultat** :
- Utilise 20+ mots-clés agricoles ciblés
- Articles pré-assignés au thème "Agriculture"
- Le membre voit immédiatement ces articles dans son dashboard

### Pour un Membre "Politique"

```bash
# Scraper uniquement les articles politiques
python scraper.py --theme "Politique"
```

**Résultat** :
- Utilise 25+ mots-clés politiques
- Priorité "critical" (plus d'articles collectés)
- Articles pré-assignés au thème "Politique"

### Pour l'Admin

```bash
# Scraping global classique
python scraper.py

# Ou scraper tous les thèmes
python scraper.py --all-themes
```

## Configuration des Thèmes

Chaque thème dans `theme_configs.py` a :

```python
{
    "keywords": [...],  # 15-25 mots-clés ciblés
    "scraping_params": {
        "max_articles": 15,  # Nombre d'articles par mot-clé
        "priority": "high",  # critical, high, medium
        "update_frequency": "daily"  # hourly, daily
    }
}
```

## Workflow Recommandé

### Pour les Membres

1. L'admin assigne un thème au membre (ex: "Santé")
2. Le membre lance : `python scraper.py --theme "Santé"`
3. Les articles sont scrapés avec les mots-clés santé
4. Les articles apparaissent automatiquement dans le dashboard du membre
5. Le membre valide et enrichit les articles de son thème

### Pour l'Admin

1. Lance le scraping global : `python scraper.py`
2. Ou lance tous les thèmes : `python scraper.py --all-themes`
3. Voit tous les articles de tous les thèmes
4. Peut ajuster les configurations dans `theme_configs.py`

## Avantages

✅ **Pertinence** : Mots-clés ultra-ciblés par thème
✅ **Efficacité** : Moins de bruit, plus de signal
✅ **Autonomie** : Chaque membre peut scraper son thème
✅ **Flexibilité** : Configurations ajustables par thème
✅ **Scalabilité** : Facile d'ajouter de nouveaux thèmes

## Personnalisation

Pour ajuster les mots-clés d'un thème, éditer `theme_configs.py` :

```python
"Agriculture": {
    "keywords": [
        "agriculture Niger",
        "mil Niger",
        # Ajouter vos mots-clés ici
    ],
    ...
}
```

## Logs

Les logs indiquent clairement le mode utilisé :

```
🌐 MODE SCRAPING GLOBAL (ADMIN)
🎯 MODE SCRAPING THÉMATIQUE: Agriculture
🌍 MODE SCRAPING TOUS LES THÈMES: 13 thèmes
```
