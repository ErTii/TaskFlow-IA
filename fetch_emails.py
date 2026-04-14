import base64
from typing import List, Dict, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _decoder_base64_urlsafe(data: str) -> str:
    if not data:
        return ""

    padding = '=' * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extraire_corps(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")

    if mime_type == "text/plain" and data:
        return _decoder_base64_urlsafe(data).strip()

    for part in payload.get("parts", []) or []:
        part_mime = part.get("mimeType", "")
        part_body = part.get("body", {})
        part_data = part_body.get("data")

        if part_mime == "text/plain" and part_data:
            texte = _decoder_base64_urlsafe(part_data).strip()
            if texte:
                return texte

    for part in payload.get("parts", []) or []:
        texte = _extraire_corps(part)
        if texte:
            return texte

    return ""


def _extraire_header(headers: List[Dict[str, str]], nom: str) -> str:
    for header in headers or []:
        if header.get("name", "").lower() == nom.lower():
            return header.get("value", "")
    return ""


def recuperer_derniers_emails_gmail(access_token: str, nb_emails: int = 3) -> List[Dict[str, Any]] | str:
    if not access_token:
        return "Token Gmail manquant."

    try:
        creds = Credentials(token=access_token)
        service = build("gmail", "v1", credentials=creds)

        result = service.users().messages().list(
            userId="me",
            maxResults=nb_emails,
            labelIds=["INBOX"]
        ).execute()

        messages = result.get("messages", [])
        emails = []

        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id:
                continue

            detail = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="full"
            ).execute()

            payload = detail.get("payload", {})
            headers = payload.get("headers", [])

            sujet = _extraire_header(headers, "Subject") or "Sans sujet"
            expediteur = _extraire_header(headers, "From") or "Inconnu"
            date_mail = _extraire_header(headers, "Date") or ""
            corps = _extraire_corps(payload)

            emails.append({
                "sujet": sujet,
                "corps": corps,
                "expediteur": expediteur,
                "date": date_mail,
            })

        return emails

    except Exception as e:
        return f"Erreur Gmail API : {str(e)}"