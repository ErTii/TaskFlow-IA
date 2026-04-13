import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def _envoyer_vers_notion(properties):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }
    return requests.post(url, headers=headers, json=data, timeout=15)


def creer_tache_notion(nom_tache, priorite, assigne, date_str=None, statut="À faire"):
    if not nom_tache or not str(nom_tache).strip():
        return False, "Nom de tâche vide."

    properties = {
        "Name": {
            "title": [{"text": {"content": str(nom_tache).strip()}}]
        },
        "Priorité": {
            "rich_text": [{"text": {"content": str(priorite or 'Moyenne').strip()}}]
        },
        "Assigné": {
            "rich_text": [{"text": {"content": str(assigne or 'Non assigné').strip()}}]
        },
        "Statut": {
            "rich_text": [{"text": {"content": str(statut or 'À faire').strip()}}]
        }
    }

    try:
        response = _envoyer_vers_notion(properties)

        if response.status_code in (200, 201):
            return True, "Tâche créée avec succès dans Notion."

        if response.status_code == 400:
            properties_sans_statut = {
                "Name": properties["Name"],
                "Priorité": properties["Priorité"],
                "Assigné": properties["Assigné"],
            }
            response_retry = _envoyer_vers_notion(properties_sans_statut)

            if response_retry.status_code in (200, 201):
                return True, "Tâche créée dans Notion (sans colonne Statut)."

            try:
                erreur = response_retry.json()
            except Exception:
                erreur = response_retry.text

            return False, f"Erreur Notion ({response_retry.status_code}) : {erreur}"

        try:
            erreur = response.json()
        except Exception:
            erreur = response.text

        return False, f"Erreur Notion ({response.status_code}) : {erreur}"

    except requests.RequestException as e:
        return False, f"Erreur réseau Notion : {str(e)}"


def _extraire_rich_text(property_value):
    if not property_value:
        return ""
    elements = property_value.get("rich_text", [])
    return "".join([item.get("plain_text", "") for item in elements]).strip()


def _extraire_title(property_value):
    if not property_value:
        return ""
    elements = property_value.get("title", [])
    return "".join([item.get("plain_text", "") for item in elements]).strip()


def recuperer_taches_notion():
    if not DATABASE_ID:
        return False, "NOTION_DATABASE_ID manquant.", []

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    has_more = True
    next_cursor = None
    toutes_les_taches = []

    try:
        while has_more:
            payload = {}
            if next_cursor:
                payload["start_cursor"] = next_cursor

            response = requests.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code != 200:
                try:
                    erreur = response.json()
                except Exception:
                    erreur = response.text
                return False, f"Erreur Notion ({response.status_code}) : {erreur}", []

            data = response.json()
            results = data.get("results", [])

            for page in results:
                properties = page.get("properties", {})

                nom = _extraire_title(properties.get("Name", {}))
                priorite = _extraire_rich_text(properties.get("Priorité", {}))
                assigne = _extraire_rich_text(properties.get("Assigné", {}))
                statut = _extraire_rich_text(properties.get("Statut", {}))

                if not statut:
                    statut = "Sans statut"
                if not priorite:
                    priorite = "Non définie"
                if not assigne:
                    assigne = "Non assigné"

                toutes_les_taches.append({
                    "id": page.get("id"),
                    "Tâche": nom,
                    "Priorité": priorite,
                    "Assigné": assigne,
                    "Statut": statut,
                    "Créé le": page.get("created_time", "")
                })

            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")

        return True, "OK", toutes_les_taches

    except requests.RequestException as e:
        return False, f"Erreur réseau Notion : {str(e)}", []


def mettre_a_jour_statut_tache(page_id, nouveau_statut):
    if not page_id:
        return False, "ID de page Notion manquant."

    url = f"https://api.notion.com/v1/pages/{page_id}"

    data = {
        "properties": {
            "Statut": {
                "rich_text": [{"text": {"content": str(nouveau_statut).strip()}}]
            }
        }
    }

    try:
        response = requests.patch(url, headers=headers, json=data, timeout=15)

        if response.status_code == 200:
            return True, "Statut mis à jour avec succès."

        try:
            erreur = response.json()
        except Exception:
            erreur = response.text

        return False, f"Erreur Notion ({response.status_code}) : {erreur}"

    except requests.RequestException as e:
        return False, f"Erreur réseau Notion : {str(e)}"