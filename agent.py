import os
import json
import re
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _valeur_texte(valeur: Any, defaut: str = "") -> str:
    if valeur is None:
        return defaut
    if isinstance(valeur, str):
        return valeur.strip()
    return str(valeur).strip()


def _normaliser_priorite(priorite: str) -> str:
    p = _valeur_texte(priorite, "Moyenne").lower()

    mapping = {
        "haute": "Haute",
        "high": "Haute",
        "urgent": "Haute",
        "urgente": "Haute",
        "élevée": "Haute",
        "elevee": "Haute",
        "prioritaire": "Haute",
        "critique": "Haute",
        "moyenne": "Moyenne",
        "medium": "Moyenne",
        "normale": "Moyenne",
        "basse": "Basse",
        "low": "Basse",
        "faible": "Basse",
    }
    return mapping.get(p, "Moyenne")


def _task_est_trop_vague(task: str) -> bool:
    t = task.lower().strip()
    formulations_vagues = [
        "penser à",
        "voir pour",
        "discuter de",
        "parler de",
    ]
    return any(t.startswith(expr) for expr in formulations_vagues)


def _tokeniser_utile(texte: str) -> List[str]:
    stopwords = {
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "à", "a", "au",
        "aux", "en", "sur", "pour", "par", "dans", "que", "qui", "il", "elle",
        "ils", "elles", "je", "tu", "nous", "vous", "doit", "doivent", "faut",
        "falloir", "peux", "peut", "merci", "bonjour", "salut", "avant", "avec",
        "se", "s", "l", "d", "ce", "cet", "cette", "ces", "quand", "temps",
        "plus", "tard", "the"
    }
    mots = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", texte.lower())
    return [m for m in mots if len(m) > 2 and m not in stopwords]


def _score_similarite(task: str, ligne: str, assignee: str) -> int:
    tokens_task = set(_tokeniser_utile(task))
    tokens_ligne = set(_tokeniser_utile(ligne))

    score = len(tokens_task & tokens_ligne)

    if assignee and assignee.lower() != "non assigné" and assignee.lower() in ligne.lower():
        score += 3

    return score


def _extraire_lignes_pertinentes(texte_source: str) -> List[str]:
    lignes = [ligne.strip(" -•\t") for ligne in texte_source.splitlines() if ligne.strip()]
    if lignes:
        return lignes
    return [bloc.strip(" -•\t") for bloc in re.split(r"[.!?;\n]+", texte_source) if bloc.strip()]


def _ligne_indique_urgence(ligne: str) -> bool:
    l = ligne.lower()

    mots_urgence = [
        "urgent",
        "urgente",
        "prioritaire",
        "priorité",
        "critique",
        "bloquant",
        "bloquante",
        "asap",
        "immédiat",
        "immediat",
        "rapidement",
        "absolument",
    ]

    echeances_proches = [
        "demain",
        "demain matin",
        "demain soir",
        "avant lundi",
        "avant mardi",
        "avant mercredi",
        "avant jeudi",
        "avant vendredi",
        "avant samedi",
        "avant dimanche",
        "pour lundi",
        "pour mardi",
        "pour mercredi",
        "pour jeudi",
        "pour vendredi",
        "pour samedi",
        "pour dimanche",
        "d'ici lundi",
        "d'ici mardi",
        "d'ici mercredi",
        "d'ici jeudi",
        "d'ici vendredi",
        "d'ici samedi",
        "d'ici dimanche",
    ]

    return any(mot in l for mot in mots_urgence) or any(expr in l for expr in echeances_proches)


def _ligne_indique_basse_priorite(ligne: str) -> bool:
    l = ligne.lower()

    mots_basse = [
        "quand tu peux",
        "quand vous pouvez",
        "quand il a le temps",
        "quand elle a le temps",
        "quand ils ont le temps",
        "quand elles ont le temps",
        "pas urgent",
        "non urgent",
        "faible priorité",
        "basse priorité",
        "si possible",
        "à l'occasion",
        "plus tard",
        "pas prioritaire",
        "optionnel",
        "secondaire",
        "a le temps",
    ]

    return any(mot in l for mot in mots_basse)


def _trouver_meilleure_ligne(task: str, assignee: str, texte_source: str) -> str:
    lignes = _extraire_lignes_pertinentes(texte_source)

    meilleure_ligne = ""
    meilleur_score = -1

    for ligne in lignes:
        score = _score_similarite(task, ligne, assignee)
        if score > meilleur_score:
            meilleur_score = score
            meilleure_ligne = ligne

    return meilleure_ligne


def _extraire_destinataire_mail(texte_source: str) -> str | None:
    lignes = [ligne.strip() for ligne in texte_source.splitlines() if ligne.strip()]
    if not lignes:
        return None

    premiere = lignes[0]

    patterns = [
        r"^(?:salut|bonjour|bonsoir)\s+([A-ZÀ-Ý][a-zà-ÿA-ZÀ-Ý'-]+)",
        r"^(?:hello|hi)\s+([A-Z][a-zA-Z'-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, premiere, flags=re.IGNORECASE)
        if match:
            nom = match.group(1).strip(" ,.:;!")
            return nom

    return None


def _recalculer_priorite(task: str, assignee: str, priority_modele: str, texte_source: str) -> str:
    meilleure_ligne = _trouver_meilleure_ligne(task, assignee, texte_source)

    if meilleure_ligne:
        if _ligne_indique_basse_priorite(meilleure_ligne):
            return "Basse"
        if _ligne_indique_urgence(meilleure_ligne):
            return "Haute"

    if priority_modele == "Basse":
        return "Basse"
    if priority_modele == "Haute":
        return "Haute"

    return "Moyenne"


def _nettoyer_tache(tache: Dict[str, Any], texte_source: str, type_source: str) -> Dict[str, Any] | None:
    if not isinstance(tache, dict):
        return None

    task = _valeur_texte(tache.get("task"))
    if not task or _task_est_trop_vague(task):
        return None

    assignee = _valeur_texte(tache.get("assignee"), "Non assigné")
    if assignee.lower() in ["non assigne", "non assigné", "aucun", "inconnu", "unknown", "n/a"]:
        assignee = "Non assigné"

    if type_source == "Email reçu" and assignee == "Non assigné":
        destinataire = _extraire_destinataire_mail(texte_source)
        if destinataire:
            assignee = destinataire

    priority_modele = _normaliser_priorite(tache.get("priority"))
    priority = _recalculer_priorite(task, assignee, priority_modele, texte_source)

    return {
        "task": task,
        "priority": priority,
        "assignee": assignee,
        "date": None
    }


def _nettoyer_reunion(reunion: Dict[str, Any]) -> Dict[str, Any] | None:
    if not isinstance(reunion, dict):
        return None

    titre = _valeur_texte(reunion.get("title"))
    date = _valeur_texte(reunion.get("date"))
    heure = _valeur_texte(reunion.get("time"))
    duree = reunion.get("duration_minutes", 60)

    if not titre or not date or not heure:
        return None

    try:
        duree = int(duree)
    except Exception:
        duree = 60

    if duree <= 0:
        duree = 60

    return {
        "title": titre,
        "date": date,
        "time": heure,
        "duration_minutes": duree
    }


def analyser_contenu(texte: str, type_source: str) -> Dict[str, Any]:
    texte = _valeur_texte(texte)
    if not texte:
        return {"summary": "", "tasks": [], "meetings": []}

    contexte = "un email professionnel" if type_source == "Email reçu" else "une transcription de réunion"

    prompt = f"""
Tu es un assistant expert en gestion de projet.

Analyse {contexte} ci-dessous.

Tu dois produire :
1. un résumé court en 2 ou 3 phrases maximum
2. les tâches réellement actionnables
3. les demandes de réunion explicites si elles existent

Règles obligatoires :
- Retourne uniquement des tâches réellement actionnables.
- N'invente aucune tâche.
- Conserve une formulation fidèle au texte.
- Le champ "task" doit contenir uniquement l'action à réaliser.
- Mets toujours null dans le champ "date" des tâches.
- Le champ "assignee" doit contenir la personne qui doit réellement faire l'action.
- Si plusieurs personnes sont mentionnées, choisis celle liée directement au verbe d'action de la tâche.
- Ne réutilise pas automatiquement la personne de la phrase précédente.
- Dans un email, si une tâche n'a pas d'assigné explicite mais que le mail commence par un destinataire clair comme "Salut Adam", alors assigne cette tâche à Adam.
- Si l'assigné n'est pas certain : "Non assigné".
- La priorité doit être strictement : "Haute", "Moyenne" ou "Basse".
- Mets "Haute" si le texte exprime clairement une urgence, une forte priorité, un blocage, ou une échéance très proche.
- Mets "Basse" si le texte indique que ce n'est pas urgent, secondaire, optionnel, ou à faire plus tard.
- Mets "Moyenne" par défaut.
- Si une phrase contient plusieurs actions pour plusieurs personnes, sépare-les correctement.
- Pour les réunions :
  - détecte uniquement les vraies demandes de réunion, point, call, visio, rendez-vous ou échange planifié
  - retourne une réunion seulement si une date ET une heure sont présentes ou clairement déductibles
  - le champ "title" doit être court et clair
  - le champ "date" doit être au format YYYY-MM-DD
  - le champ "time" doit être au format HH:MM
  - le champ "duration_minutes" vaut 60 par défaut si rien n'est précisé
- Si aucune réunion claire n'est présente, retourne une liste vide.
- Le résumé doit être clair, court et professionnel.

Réponds EXCLUSIVEMENT avec un JSON de cette forme :
{{
  "summary": "Résumé court",
  "taches": [
    {{
      "task": "Nom fidèle de la tâche",
      "priority": "Moyenne",
      "assignee": "Prénom",
      "date": null
    }}
  ],
  "meetings": [
    {{
      "title": "Point projet X",
      "date": "2026-04-18",
      "time": "10:00",
      "duration_minutes": 60
    }}
  ]
}}

Aujourd'hui nous sommes le 2026-04-13.

Texte :
\"\"\"
{texte}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        contenu = response.choices[0].message.content.strip()
        data = json.loads(contenu)

        summary = _valeur_texte(data.get("summary"))
        taches_brutes = data.get("taches", [])
        reunions_brutes = data.get("meetings", [])

        if not isinstance(taches_brutes, list):
            taches_brutes = []
        if not isinstance(reunions_brutes, list):
            reunions_brutes = []

        taches_finales = []
        vues_taches = set()

        for tache in taches_brutes:
            tache_propre = _nettoyer_tache(tache, texte, type_source)
            if not tache_propre:
                continue

            cle = (
                tache_propre["task"].lower(),
                tache_propre["assignee"].lower(),
            )
            if cle in vues_taches:
                continue

            vues_taches.add(cle)
            taches_finales.append(tache_propre)

        reunions_finales = []
        vues_reunions = set()

        for reunion in reunions_brutes:
            reunion_propre = _nettoyer_reunion(reunion)
            if not reunion_propre:
                continue

            cle = (
                reunion_propre["title"].lower(),
                reunion_propre["date"],
                reunion_propre["time"],
            )
            if cle in vues_reunions:
                continue

            vues_reunions.add(cle)
            reunions_finales.append(reunion_propre)

        return {
            "summary": summary,
            "tasks": taches_finales,
            "meetings": reunions_finales
        }

    except Exception:
        return {"summary": "", "tasks": [], "meetings": []}


def analyser_texte_en_taches(texte: str, type_source: str) -> List[Dict[str, Any]]:
    return analyser_contenu(texte, type_source).get("tasks", [])