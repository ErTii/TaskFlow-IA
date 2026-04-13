import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configuration de Gemini
genai.configure(api_key="AIzaSyAKZBQWyqel12GpPpAWrTNs27GntV2x4tw")

def analyser_texte_en_taches(texte):
    """
    Utilise Gemini 1.5 Flash pour extraire les tâches.
    C'est ultra rapide et gratuit.
    """
    # On choisit le modèle le plus rapide (Flash)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Tu es un assistant expert en productivité. 
    Analyse ce texte (réunion ou e-mail) et extrais les actions concrètes.
    
    Réponds EXCLUSIVEMENT sous forme d'une liste JSON d'objets. 
    Chaque objet doit avoir :
    - "task": le nom de la tâche
    - "priority": "Haute", "Moyenne" ou "Basse"
    - "assignee": le nom de la personne
    
    Texte à analyser : {texte}
    """
    
    # On force Gemini à répondre en JSON pur
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    return response.text