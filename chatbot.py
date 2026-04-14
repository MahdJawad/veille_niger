import os
import logging
import asyncio

# --- Configuration Chatbot ---
# Définir CHATBOT_MODE sur "API" pour utiliser OpenAI/Gemini
# Défaut sur "LOCAL" selon la demande utilisateur
CHATBOT_MODE = os.environ.get("CHATBOT_MODE", "LOCAL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

logger = logging.getLogger("ChatbotAgent")

# Variables Globales pour le Modèle Local
_local_pipeline = None
_model_failed = False

def get_db_context_summary(db):
    """
    Récupère un résumé texte de la base de données pour "nourrir" l'IA
    (RAG: Retrieval-Augmented Generation)
    """
    try:
        # Résumé général
        summary = db.get_executive_summary()
        stats_text = f"La base contient {summary['total']} articles, dont {summary['social']} posts réseaux sociaux et {summary['internet']} articles web."
        
        # Incidents actifs
        incidents = db.get_active_incidents()
        if incidents:
            inc_text = "Incidents Actifs: " + ", ".join([f"[{i['severity']}] {i['title']}" for i in incidents])
        else:
            inc_text = "Aucun incident actif en ce moment."
            
        context = f"Contexte actuel du système (Base de données):\n- {stats_text}\n- {inc_text}\n"
        return context
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du contexte RAG: {e}")
        return "Contexte système indisponible."

def init_local_llm():
    """Charge le modèle de langage local pour l'Option 2"""
    global _local_pipeline, _model_failed
    
    if _local_pipeline is not None or _model_failed:
        return
        
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        import torch
        
        logger.info("Chargement du grand modèle conversationnel Local (TinyLlama)... Cela peut prendre quelques minutes.")
        
        # Utiliser un modèle extrêmement léger pour tolérer le CPU local (-1 GPU)
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        # On essaie d'abord un pipeline standard
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, low_cpu_mem_usage=True)
        model.to("cpu")
        
        _local_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)
        logger.info("Modèle Conversationnel Local chargé avec succès.")
    
    except Exception as e:
        logger.error(f"Impossible de charger l'IA conversationnelle locale (Manque de RAM ou dépendance introuvable): {e}")
        _model_failed = True

async def generate_chatbot_response(user_message: str, db) -> str:
    """Génère la réponse de l'agent en fonction du choix architectural (API ou LOCAL)"""
    
    context = get_db_context_summary(db)
    
    # Prompt System
    prompt = (
        "En tant qu'Assistant IA expert de Veille Niger, réponds clairement "
        "à la question de l'utilisateur de manière concise.\n"
        f"{context}\n\n"
        f"Utilisateur: {user_message}\n"
        "Assistant:"
    )

    if CHATBOT_MODE == "API":
        # --- OPTION 1: API EXTERNE (OpenAI) ---
        if not OPENAI_API_KEY:
            return "Mode API sélectionné mais aucune clé OpenAI trouvée. Veuillez configurer OPENAI_API_KEY dans vos variables d'environnement."
            
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": f"Tu es l'assistant de Veille Niger.\n{context}"},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 150
            }
            # Simule l'appel asynchrone non-bloquant
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: requests.post(
                "https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10
            ))
            
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"Erreur API Externe : {resp.text}"
                
        except Exception as e:
            return f"Echec de connexion à l'API Externe: {str(e)}"
            
    else:
        # --- OPTION 2: IA LOCALE (HuggingFace CPU) ---
        init_local_llm()
        
        if _model_failed:
            # Fallback simulé élégant si la RAM a crashé
            return (
                "Mode Local Automatique : Oula ! Mon processeur réseau-neuronal (Modèle LLM Local) "
                "n'a pas pu se charger totalement en mémoire en raison des limitations matérielles "
                "actuelles de la machine. Cependant, voici les infos que j'ai comprises :\n" + context
            )
            
        try:
            # Lancement asynchrone pour ne pas bloquer le serveur FastAPI !
            loop = asyncio.get_event_loop()
            
            def run_inference():
                res = _local_pipeline(prompt, max_new_tokens=100, do_sample=True, temperature=0.7)
                generated_text = res[0]['generated_text']
                # Couper le prompt d'origine pour ne garder que la réponse
                answer = generated_text.replace(prompt, "").strip()
                return answer

            answer = await loop.run_in_executor(None, run_inference)
            return answer
            
        except Exception as e:
            logger.error(f"Crash inférence IA Locale : {e}")
            return "Une erreur est survenue lors de la réflexion de l'IA Locale. Requête trop complexe pour la machine."
