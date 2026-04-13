import os
import re
from datetime import datetime, timedelta
from typing import List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def _get_credentials():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "Le fichier credentials.json est introuvable. "
                    "Télécharge les identifiants OAuth Google Calendar et place-les à la racine du projet."
                )

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def _normaliser_heure(heure_str: str) -> str:
    heure_str = str(heure_str).strip().lower()

    # 18h -> 18:00
    match = re.fullmatch(r"(\d{1,2})h", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:00"

    # 18h30 -> 18:30
    match = re.fullmatch(r"(\d{1,2})h(\d{1,2})", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    # 18:30 -> 18:30
    match = re.fullmatch(r"(\d{1,2}):(\d{1,2})", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    # 18 -> 18:00
    match = re.fullmatch(r"(\d{1,2})", heure_str)
    if match:
        return f"{int(match.group(1)):02d}:00"

    return heure_str


def creer_evenement_calendar(
    titre: str,
    date_str: str,
    heure_str: str,
    participants: List[str] | None = None,
    duree_minutes: int = 60,
    description: str = ""
) -> Tuple[bool, str]:
    try:
        creds = _get_credentials()
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
            "attendees": [{"email": email.strip()} for email in (participants or []) if email.strip()],
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