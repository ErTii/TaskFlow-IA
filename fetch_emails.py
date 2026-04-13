import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()


EXPEDITEURS_A_IGNORER = [
    "google",
    "no-reply",
    "noreply",
    "donotreply",
    "do-not-reply",
    "notification",
    "notifications",
    "accounts.google",
    "mailer-daemon",
    "mail-daemon",
    "support@google",
    "security-noreply",
]


def _decoder_texte(valeur):
    if valeur is None:
        return ""

    if isinstance(valeur, bytes):
        try:
            return valeur.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return valeur.decode("latin-1")
            except UnicodeDecodeError:
                return valeur.decode("utf-8", errors="ignore")

    return str(valeur)


def _decoder_sujet(message):
    sujet_brut = message.get("Subject", "Pas de sujet")
    morceaux = decode_header(sujet_brut)

    sujet = ""
    for contenu, encodage in morceaux:
        if isinstance(contenu, bytes):
            try:
                sujet += contenu.decode(encodage or "utf-8", errors="ignore")
            except Exception:
                sujet += contenu.decode("utf-8", errors="ignore")
        else:
            sujet += contenu

    return sujet.strip() if sujet.strip() else "Pas de sujet"


def _extraire_corps_texte(message):
    corps = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition.lower():
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset()

                if payload:
                    try:
                        corps = payload.decode(charset or "utf-8", errors="ignore")
                    except Exception:
                        corps = payload.decode("utf-8", errors="ignore")

                    if corps.strip():
                        return corps.strip()
    else:
        payload = message.get_payload(decode=True)
        charset = message.get_content_charset()

        if payload:
            try:
                corps = payload.decode(charset or "utf-8", errors="ignore")
            except Exception:
                corps = payload.decode("utf-8", errors="ignore")

    return corps.strip()


def _mail_est_a_ignorer(expediteur, sujet, corps):
    texte = f"{expediteur} {sujet} {corps}".lower()

    return any(mot in texte for mot in EXPEDITEURS_A_IGNORER)


def recuperer_derniers_emails(nb_emails=3):
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    imap_url = os.getenv("EMAIL_IMAP")

    if not user or not password or not imap_url:
        return "Variables EMAIL_USER, EMAIL_PASS ou EMAIL_IMAP manquantes dans le fichier .env"

    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)

        status, _ = mail.select("INBOX")
        if status != "OK":
            mail.logout()
            return "Impossible d'ouvrir la boîte de réception."

        status, messages = mail.search(None, "ALL")
        if status != "OK":
            mail.logout()
            return "Impossible de récupérer les emails."

        mail_ids = messages[0].split()
        if not mail_ids:
            mail.logout()
            return []

        # On regarde un peu plus large pour compenser les mails filtrés
        nb_a_lire = max(nb_emails * 3, nb_emails)
        derniers_ids = mail_ids[-nb_a_lire:]
        derniers_ids.reverse()

        resultats = []

        for mail_id in derniers_ids:
            if len(resultats) >= nb_emails:
                break

            status, msg_data = mail.fetch(mail_id, "(RFC822)")
            if status != "OK":
                continue

            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                sujet = _decoder_sujet(msg)
                corps = _extraire_corps_texte(msg)
                expediteur = _decoder_texte(msg.get("From", "Inconnu"))
                date_mail = _decoder_texte(msg.get("Date", ""))

                if _mail_est_a_ignorer(expediteur, sujet, corps):
                    continue

                resultats.append({
                    "sujet": sujet,
                    "corps": corps,
                    "expediteur": expediteur,
                    "date": date_mail
                })

                if len(resultats) >= nb_emails:
                    break

        mail.logout()
        return resultats

    except imaplib.IMAP4.error as e:
        return f"Erreur IMAP : {str(e)}"
    except Exception as e:
        return f"Erreur de connexion : {str(e)}"