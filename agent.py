import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyser_texte_en_taches(texte):
    """
    Cette fonction utilise le LLM pour extraire des tâches structurées.
    C'est notre brique LLM/NLP.
    """
    prompt = f"""
    Analyse le texte suivant et extrais les actions concrètes à faire.
    Réponds UNIQUEMENT sous forme d'une liste d'objets JSON avec :
    - "task": le titre de la tâche
    - "priority": Haute, Moyenne ou Basse
    - "assignee": la personne responsable (si mentionnée, sinon "Inconnu")

    Texte : {texte}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # On récupère le résultat
    return response.choices[0].message.content