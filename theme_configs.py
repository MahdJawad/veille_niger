"""
Configurations de scraping thématique pour Veille Niger.
Chaque thème dispose de mots-clés ciblés, sources spécialisées et paramètres optimisés.

Les membres utilisent ces configurations pour un scraping ultra-pertinent de leur thématique.
L'admin conserve le scraping global avec keywords.py.
"""

# Configuration complète par thème
THEME_SCRAPING_CONFIGS = {
    "Agriculture": {
        "keywords": [
            # Général
            "agriculture Niger", "agriculture nigérienne", "secteur agricole Niger",
            # Cultures principales
            "mil Niger", "sorgho Niger", "niébé", "arachide Niger", "riz Niger",
            "maïs Niger", "manioc Niger", "oignon Niger",
            # Pratiques et techniques
            "irrigation Niger", "semences améliorées", "fertilisant Niger",
            "culture pluviale", "maraîchage Niger", "agriculture irriguée",
            # Élevage
            "élevage Niger", "bétail Niger", "pastoralisme", "transhumance",
            # Acteurs
            "paysan Niger", "agriculteur Niger", "coopérative agricole",
            "chambre agriculture Niger",
            # Institutions
            "ministère agriculture Niger", "RECA Niger", "INRAN Niger",
            # Problématiques
            "sécurité alimentaire Niger", "famine Niger", "résilience agricole"
        ],
        "scraping_params": {
            "max_articles": 15,
            "priority": "high",
            "update_frequency": "daily"
        }
    },
    
    "Culture": {
        "keywords": [
            # Général
            "culture Niger", "patrimoine Niger", "art Niger",
            # Arts
            "musique Niger", "cinéma Niger", "théâtre Niger",
            "danse Niger", "artiste nigérien",
            # Événements
            "festival Niger", "FESPACO Niger", "biennale Niger",
            "concert Niger", "exposition Niger",
            # Patrimoine
            "patrimoine culturel Niger", "UNESCO Niger", "monument Niger",
            "musée Niger", "bibliothèque Niger",
            # Langues et traditions
            "langue haoussa", "langue zarma", "tradition Niger",
            "griots Niger", "conte Niger",
            # Institutions
            "ministère culture Niger", "centre culturel Niger"
        ],
        "scraping_params": {
            "max_articles": 12,
            "priority": "medium",
            "update_frequency": "daily"
        }
    },
    
    "Diplomatie": {
        "keywords": [
            # Relations internationales
            "diplomatie Niger", "relations internationales Niger",
            "coopération Niger", "partenariat Niger",
            # Organisations
            "CEDEAO Niger", "Union Africaine Niger", "ONU Niger",
            "G5 Sahel", "UEMOA Niger",
            # Relations bilatérales
            "France Niger", "USA Niger", "Chine Niger", "Russie Niger",
            "Nigeria Niger", "Algérie Niger", "Burkina Niger",
            # Événements
            "sommet Niger", "visite officielle Niger", "ambassade Niger",
            "ambassadeur Niger", "consul Niger",
            # Institutions
            "ministère affaires étrangères Niger", "MAE Niger"
        ],
        "scraping_params": {
            "max_articles": 15,
            "priority": "high",
            "update_frequency": "daily"
        }
    },
    
    "Économie": {
        "keywords": [
            # Général
            "économie Niger", "finance Niger", "budget Niger",
            # Secteurs
            "commerce Niger", "investissement Niger", "entreprise Niger",
            "industrie Niger", "mines Niger", "pétrole Niger",
            "uranium Niger", "or Niger",
            # Institutions financières
            "BCEAO Niger", "banque Niger", "microfinance Niger",
            "bourse Niger",
            # Indicateurs
            "PIB Niger", "croissance économique Niger", "inflation Niger",
            "dette Niger", "déficit budgétaire Niger",
            # Commerce
            "exportation Niger", "importation Niger", "balance commerciale",
            # Institutions
            "ministère économie Niger", "chambre commerce Niger",
            "patronat Niger"
        ],
        "scraping_params": {
            "max_articles": 18,
            "priority": "high",
            "update_frequency": "daily"
        }
    },
    
    "Éducation": {
        "keywords": [
            # Général
            "éducation Niger", "école Niger", "enseignement Niger",
            # Niveaux
            "primaire Niger", "secondaire Niger", "université Niger",
            "formation professionnelle Niger",
            # Établissements
            "UAM Niger", "université Niamey", "lycée Niger",
            "collège Niger", "école primaire Niger",
            # Acteurs
            "enseignant Niger", "professeur Niger", "étudiant Niger",
            "élève Niger", "syndicat enseignant Niger",
            # Examens
            "BEPC Niger", "baccalauréat Niger", "CEP Niger",
            # Problématiques
            "alphabétisation Niger", "décrochage scolaire",
            "cantines scolaires Niger",
            # Institutions
            "ministère éducation Niger", "MESS Niger"
        ],
        "scraping_params": {
            "max_articles": 15,
            "priority": "high",
            "update_frequency": "daily"
        }
    },
    
    "Environnement": {
        "keywords": [
            # Général
            "environnement Niger", "écologie Niger", "climat Niger",
            # Problématiques
            "désertification Niger", "déforestation Niger",
            "changement climatique Niger", "sécheresse Niger",
            "inondation Niger", "érosion Niger",
            # Biodiversité
            "faune Niger", "flore Niger", "parc national Niger",
            "réserve naturelle Niger", "girafe Niger",
            # Ressources
            "eau Niger", "fleuve Niger", "lac Tchad",
            "nappe phréatique", "gestion eau Niger",
            # Énergie
            "énergie renouvelable Niger", "solaire Niger",
            "barrage Niger", "électricité Niger",
            # Institutions
            "ministère environnement Niger", "CNEDD Niger"
        ],
        "scraping_params": {
            "max_articles": 12,
            "priority": "medium",
            "update_frequency": "daily"
        }
    },
    
    "Gouvernance": {
        "keywords": [
            # Général
            "gouvernance Niger", "administration Niger",
            "réforme Niger", "décentralisation Niger",
            # Institutions
            "institution Niger", "fonction publique Niger",
            "administration publique Niger",
            # Justice
            "justice Niger", "tribunal Niger", "cour Niger",
            "magistrat Niger", "avocat Niger",
            # Lutte contre corruption
            "corruption Niger", "HALCIA Niger", "transparence Niger",
            "bonne gouvernance Niger",
            # Collectivités
            "commune Niger", "région Niger", "maire Niger",
            "conseil régional Niger",
            # Réformes
            "réforme administrative Niger", "modernisation État Niger"
        ],
        "scraping_params": {
            "max_articles": 12,
            "priority": "medium",
            "update_frequency": "daily"
        }
    },
    
    "Numérique / TIC": {
        "keywords": [
            # Général
            "numérique Niger", "digital Niger", "TIC Niger",
            "technologie Niger", "innovation Niger",
            # Internet et télécoms
            "internet Niger", "téléphonie Niger", "4G Niger",
            "5G Niger", "fibre optique Niger",
            "Orange Niger", "Airtel Niger", "Moov Niger",
            # Services numériques
            "e-gouvernement Niger", "administration numérique",
            "paiement mobile Niger", "mobile money Niger",
            # Startups et innovation
            "startup Niger", "incubateur Niger", "tech Niger",
            "développeur Niger", "programmeur Niger",
            # Cybersécurité
            "cybersécurité Niger", "protection données Niger",
            # Institutions
            "ARCEP Niger", "ministère numérique Niger"
        ],
        "scraping_params": {
            "max_articles": 12,
            "priority": "medium",
            "update_frequency": "daily"
        }
    },
    
    "Politique": {
        "keywords": [
            # Général
            "politique Niger", "gouvernement Niger",
            # Institutions
            "présidence Niger", "président Niger", "premier ministre Niger",
            "assemblée nationale Niger", "parlement Niger",
            "député Niger", "sénateur Niger",
            # Partis politiques
            "PNDS Niger", "MNSD Niger", "MODEN Niger",
            "RDR Niger", "parti politique Niger",
            "opposition Niger", "majorité présidentielle Niger",
            # Élections
            "élection Niger", "présidentielle Niger", "législative Niger",
            "municipale Niger", "scrutin Niger", "vote Niger",
            # Événements politiques
            "conseil ministres Niger", "remaniement Niger",
            "motion censure Niger", "crise politique Niger",
            # Acteurs
            "homme politique Niger", "leader politique Niger"
        ],
        "scraping_params": {
            "max_articles": 20,
            "priority": "critical",
            "update_frequency": "hourly"
        }
    },
    
    "Santé": {
        "keywords": [
            # Général
            "santé Niger", "médical Niger", "sanitaire Niger",
            # Établissements
            "hôpital Niger", "centre santé Niger", "clinique Niger",
            "hôpital national Niamey", "CHU Niger",
            # Maladies
            "paludisme Niger", "méningite Niger", "rougeole Niger",
            "choléra Niger", "COVID Niger", "épidémie Niger",
            "vaccination Niger", "campagne vaccination Niger",
            # Personnel
            "médecin Niger", "infirmier Niger", "sage-femme Niger",
            "pharmacien Niger",
            # Programmes
            "santé maternelle Niger", "santé infantile Niger",
            "planning familial Niger", "nutrition Niger",
            "malnutrition Niger",
            # Institutions
            "ministère santé Niger", "OMS Niger"
        ],
        "scraping_params": {
            "max_articles": 15,
            "priority": "high",
            "update_frequency": "daily"
        }
    },
    
    "Sécurité": {
        "keywords": [
            # Général
            "sécurité Niger", "défense Niger", "armée Niger",
            # Forces de sécurité
            "FAN Niger", "gendarmerie Niger", "police Niger",
            "garde nationale Niger",
            # Terrorisme
            "terrorisme Niger", "djihadisme Niger", "Boko Haram Niger",
            "EIGS Niger", "JNIM Niger", "attaque terroriste Niger",
            # Zones sensibles
            "Diffa Niger", "Tillabéri Niger", "Tahoua Niger",
            "frontière Niger", "zone trois frontières",
            # Opérations
            "opération militaire Niger", "Barkhane Niger",
            "G5 Sahel opération",
            # Criminalité
            "criminalité Niger", "banditisme Niger",
            "trafic Niger", "kidnapping Niger"
        ],
        "scraping_params": {
            "max_articles": 20,
            "priority": "critical",
            "update_frequency": "hourly"
        }
    },
    
    "Sport": {
        "keywords": [
            # Général
            "sport Niger", "sportif Niger", "athlète Niger",
            # Football
            "football Niger", "Mena Niger", "championnat Niger",
            "CAN Niger", "équipe nationale Niger",
            "sélection Niger", "Lions Ténéré",
            # Autres sports
            "basketball Niger", "handball Niger", "athlétisme Niger",
            "lutte Niger", "taekwondo Niger",
            # Compétitions
            "compétition Niger", "championnat Niger",
            "coupe Niger", "tournoi Niger",
            # Infrastructures
            "stade Niger", "stade général Seyni Kountché",
            "complexe sportif Niger",
            # Institutions
            "fédération sport Niger", "comité olympique Niger",
            "ministère sport Niger"
        ],
        "scraping_params": {
            "max_articles": 10,
            "priority": "medium",
            "update_frequency": "daily"
        }
    },
    
    "Société / Genre": {
        "keywords": [
            # Général
            "société Niger", "social Niger", "population Niger",
            # Genre et femmes
            "femme Niger", "genre Niger", "égalité Niger",
            "droits femmes Niger", "autonomisation femmes Niger",
            "violences femmes Niger", "mariage précoce Niger",
            # Jeunesse
            "jeunesse Niger", "jeune Niger", "emploi jeunes Niger",
            "formation jeunes Niger",
            # Famille
            "famille Niger", "enfant Niger", "protection enfant Niger",
            "droits enfant Niger",
            # Société civile
            "ONG Niger", "association Niger", "société civile Niger",
            "mouvement citoyen Niger",
            # Problématiques sociales
            "pauvreté Niger", "exode rural Niger",
            "migration Niger", "déplacés Niger", "réfugiés Niger"
        ],
        "scraping_params": {
            "max_articles": 15,
            "priority": "medium",
            "update_frequency": "daily"
        }
    }
}

def get_theme_config(theme: str) -> dict:
    """
    Récupère la configuration de scraping pour un thème donné.
    
    Args:
        theme: Nom du thème (ex: "Agriculture", "Politique")
    
    Returns:
        Configuration du thème ou None si non trouvé
    """
    return THEME_SCRAPING_CONFIGS.get(theme)

def get_all_themes() -> list:
    """Retourne la liste de tous les thèmes disponibles."""
    return list(THEME_SCRAPING_CONFIGS.keys())

def get_theme_keywords(theme: str) -> list:
    """Récupère les mots-clés d'un thème spécifique."""
    config = get_theme_config(theme)
    return config["keywords"] if config else []
