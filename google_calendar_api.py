from datetime import datetime, timedelta
from typing import List, Tuple
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _normaliser_heure(heure_str: str) -> str:
    heure_str = str(heure_str).strip().lower()

    match = re.fullmatch(r"(\d{1,2})h", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:00"

    match = re.fullmatch(r"(\d{1,2})h(\d{1,2})", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    match = re.fullmatch(r"(\d{1,2}):(\d{1,2})", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    match = re.fullmatch(r"(\d{1,2})", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:00"

    return heure_str


def creer_evenement_calendar(
    access_token: str,
    titre: str,
    date_str: str,
    heure_str: str,
    participants: List[str] | None = None,
    duree_minutes: int = 60,
    description: str = ""
) -> Tuple[bool, str]:
    try:
        if not access_token:
            return False, "Token Google Calendar manquant. Déconnecte-toi puis reconnecte-toi."

        creds = Credentials(token=access_token)
        service = build("calendar", "v3", credentials=creds)

        heure_str = _normaliser_heure(heure_str)

        start_dt = datetime.strptime(f"{date_str} {heure_str}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duree_minutes)

        event = {
            "summary": titre,
            "description": description or "Événement créé depuis TaskFlow AI",
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Europe/Paris",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Europe/Paris",
            },
            "attendees": [
                {"email": email.strip()}
                for email in (participants or [])
                if email.strip()
            ],
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"
        ).execute()

        lien = created_event.get("htmlLink", "")
        return True, f"Réunion créée avec succès. {lien}"

    except Exception as e:
        return False, f"Erreur Google Calendar : {str(e)}"