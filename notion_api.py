import os
import requests
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def creer_tache_notion(nom_tache, priorite, assigne):
    """
    Envoie une requête à l'API Notion pour créer une nouvelle page (tâche) dans une base de données.
    """
    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Structure de la donnée attendue par Notion
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": nom_tache}}]
            },
            "Priorité": {
                "rich_text": [{"text": {"content": priorite}}]
            },
            "Assigné": {
                "rich_text": [{"text": {"content": assigne}}]
            }
        }
    }
    
    reponse = requests.post(url, headers=headers, json=data)
    
    if reponse.status_code == 200:
        return True
    else:
        print(f"Erreur Notion : {reponse.text}")
        return False