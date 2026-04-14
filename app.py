import streamlit as st
import pandas as pd
import plotly.express as px
from agent import analyser_contenu
from notion_api import (
    creer_tache_notion,
    recuperer_taches_notion,
    mettre_a_jour_statut_tache,
)
from fetch_emails import recuperer_derniers_emails_gmail
from google_calendar_api import creer_evenement_calendar

st.set_page_config(page_title="TaskFlow AI", page_icon="🚀", layout="wide")


def afficher_notification_fixe(message, type_notif="success"):
    if type_notif == "success":
        st.toast(message, icon="✅")
    else:
        st.toast(message, icon="❌")


# -----------------------------
# AUTH GOOGLE
# -----------------------------
user_info = st.user.to_dict() if hasattr(st.user, "to_dict") else {}
is_logged_in = user_info.get("is_logged_in", False)

if not is_logged_in:
    st.markdown("""
        <style>
        .login-box {
            max-width: 760px;
            margin: 70px auto;
            padding: 38px;
            border-radius: 24px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e5e7eb;
            text-align: center;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        }
        .login-title {
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 6px;
        }
        .login-sub {
            font-size: 1.05rem;
            color: #475569;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="login-box">
            <div class="login-title">🚀 TaskFlow AI</div>
            <div class="login-sub">
                Connectez-vous avec Google pour accéder à l'application.
            </div>
            <div style="color:#64748b;">
                Seuls les comptes ajoutés comme testeurs Google peuvent se connecter.
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.button("Se connecter avec Google", on_click=st.login, use_container_width=True)
    st.stop()

# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
<style>
:root {
    --bg: #f6f8fb;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #64748b;
    --border: #e2e8f0;
    --primary: #2563eb;
    --primary-2: #1d4ed8;
    --success: #16a34a;
    --warning: #f59e0b;
    --danger: #dc2626;
    --shadow: 0 8px 26px rgba(15, 23, 42, 0.06);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
}

.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}

h1, h2, h3, h4 {
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid var(--border);
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 2.9rem;
    background: linear-gradient(180deg, var(--primary) 0%, var(--primary-2) 100%);
    color: white;
    font-weight: 700;
    border: none;
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.22);
}

.stButton > button:hover {
    filter: brightness(1.03);
}

div[data-baseweb="tab-list"] {
    gap: 10px;
    background: transparent;
    margin-bottom: 12px;
}

button[data-baseweb="tab"] {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 10px 18px !important;
    box-shadow: var(--shadow);
}

button[data-baseweb="tab"][aria-selected="true"] {
    border-color: #bfdbfe !important;
    background: #eff6ff !important;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 18px 20px;
    box-shadow: var(--shadow);
    margin-bottom: 14px;
}

.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
    color: white;
    border-radius: 24px;
    padding: 26px 28px;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.16);
    margin-bottom: 14px;
}

.hero-sub {
    color: rgba(255,255,255,0.82);
    margin-top: 6px;
    font-size: 1rem;
}

.section-title {
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 10px;
}

.muted {
    color: var(--muted);
    font-size: 0.96rem;
}

.kpi-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 18px 18px;
    box-shadow: var(--shadow);
}

.kpi-label {
    font-size: 0.9rem;
    color: var(--muted);
    margin-bottom: 8px;
    font-weight: 600;
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--text);
}

.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    margin-right: 6px;
}

.badge-blue {
    background: #dbeafe;
    color: #1d4ed8;
}

.badge-orange {
    background: #ffedd5;
    color: #c2410c;
}

.badge-green {
    background: #dcfce7;
    color: #15803d;
}

.badge-red {
    background: #fee2e2;
    color: #b91c1c;
}

.badge-gray {
    background: #e2e8f0;
    color: #334155;
}

.mail-box {
    background: white;
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 16px 18px;
    box-shadow: var(--shadow);
    margin-bottom: 18px;
}

.mail-title {
    font-size: 1.08rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 2px;
}

.mail-meta {
    color: var(--muted);
    font-size: 0.92rem;
    margin-bottom: 12px;
}

.small-divider {
    height: 1px;
    background: var(--border);
    margin: 10px 0 14px 0;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--border);
    padding: 12px;
    border-radius: 18px;
    box-shadow: var(--shadow);
}

.stSelectbox > div > div,
.stTextInput > div > div,
.stTextArea textarea,
.stMultiSelect > div > div {
    border-radius: 12px !important;
}

hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 10px 0 18px 0;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER + USER INFO
# -----------------------------
user_name = user_info.get("name", "Utilisateur")
user_email = user_info.get("email", "Non disponible")

st.markdown(f"""
<div class="hero">
    <div style="font-size:2rem;font-weight:800;">🚀 TaskFlow AI</div>
    <div class="hero-sub">
        Analyse intelligente des emails et transcriptions, suivi des tâches dans Notion et création de réunions Google Calendar.
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Compte connecté")
    st.write(f"**Nom :** {user_name}")
    st.write(f"**Email :** {user_email}")
    st.button("Se déconnecter", on_click=st.logout, use_container_width=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "manual_analysis" not in st.session_state:
    st.session_state.manual_analysis = None

if "scan_analysis" not in st.session_state:
    st.session_state.scan_analysis = None

if "notification_message" not in st.session_state:
    st.session_state.notification_message = None

if "notification_type" not in st.session_state:
    st.session_state.notification_type = "success"

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Saisie Manuelle",
    "📥 Scan Outlook",
    "📊 Dashboard",
    "✏️ Modifier"
])


def _recuperer_access_token():
    tokens = user_info.get("tokens", {})
    if isinstance(tokens, dict):
        return tokens.get("access")
    return None


def _badge_priorite(priority: str) -> str:
    priority = (priority or "").lower()
    if priority == "haute":
        return '<span class="badge badge-red">Haute</span>'
    if priority == "moyenne":
        return '<span class="badge badge-orange">Moyenne</span>'
    if priority == "basse":
        return '<span class="badge badge-green">Basse</span>'
    return f'<span class="badge badge-gray">{priority or "Non définie"}</span>'


def _badge_statut(statut: str) -> str:
    statut = statut or ""
    if statut == "À faire":
        return '<span class="badge badge-blue">À faire</span>'
    if statut == "En cours":
        return '<span class="badge badge-orange">En cours</span>'
    if statut == "Fait":
        return '<span class="badge badge-green">Fait</span>'
    return f'<span class="badge badge-gray">{statut}</span>'


def afficher_bloc_taches(taches, prefixe):
    if not taches:
        st.info("Aucune tâche détectée.")
        return

    for i, t in enumerate(taches):
        key = f"{prefixe}_check_{i}"
        if key not in st.session_state:
            st.session_state[key] = True

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.checkbox(
            f"{t.get('task', 'Tâche')} | {t.get('priority', 'Moyenne')} | {t.get('assignee', 'Non assigné')}",
            key=key
        )
        st.markdown(
            f"""
            <div class="muted">
                {_badge_priorite(t.get('priority', 'Moyenne'))}
                <span class="badge badge-gray">{t.get('assignee', 'Non assigné')}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


def afficher_bloc_reunions(reunions, prefixe):
    if not reunions:
        return

    st.markdown('<div class="section-title">Réunions détectées</div>', unsafe_allow_html=True)
    access_token = _recuperer_access_token()

    for i, reunion in enumerate(reunions):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**Réunion {i + 1}**")
        st.write(f"**Titre :** {reunion.get('title', '')}")
        st.write(f"**Date :** {reunion.get('date', '')}")
        st.write(f"**Heure :** {reunion.get('time', '')}")
        st.write(f"**Durée :** {reunion.get('duration_minutes', 60)} min")

        participants = st.text_input(
            "Emails des participants (séparés par des virgules)",
            key=f"{prefixe}_participants_{i}",
            placeholder="exemple1@gmail.com, exemple2@gmail.com"
        )

        if st.button("Créer dans Google Calendar", key=f"{prefixe}_create_meeting_{i}"):
            emails = [email.strip() for email in participants.split(",") if email.strip()]

            succes, message = creer_evenement_calendar(
                access_token=access_token,
                titre=reunion.get("title", "Réunion"),
                date_str=reunion.get("date", ""),
                heure_str=reunion.get("time", ""),
                participants=emails,
                duree_minutes=reunion.get("duration_minutes", 60),
                description="Événement proposé par TaskFlow AI"
            )

            if succes:
                st.session_state.notification_message = "Réunion créée avec succès dans Google Calendar."
                st.session_state.notification_type = "success"
                st.rerun()
            else:
                st.session_state.notification_message = message
                st.session_state.notification_type = "error"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


with tab1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Analyse manuelle</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Collez une transcription ou un email, puis laissez l’IA extraire les actions.</div>', unsafe_allow_html=True)

    source = st.selectbox("Type de contenu :", ["Réunion (Transcription)", "Email reçu"])
    texte_source = st.text_area(
        "Collez le contenu ici :",
        height=220,
        placeholder="Ex: Mathieu doit corriger le bug pour demain..."
    )

    if st.button("Analyser", key="analyse_manuelle"):
        if not texte_source or not texte_source.strip():
            st.warning("Le champ est vide.")
        else:
            with st.spinner("Analyse IA en cours..."):
                st.session_state.manual_analysis = analyser_contenu(texte_source, source)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.manual_analysis:
        resultat = st.session_state.manual_analysis
        taches = resultat.get("tasks", [])
        reunions = resultat.get("meetings", [])

        st.markdown('<div class="section-title">Tâches détectées</div>', unsafe_allow_html=True)
        afficher_bloc_taches(taches, "manual")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        statut_manual = st.selectbox(
            "Statut à appliquer dans Notion",
            ["À faire", "En cours", "Fait"],
            key="statut_manual"
        )

        if st.button("Envoyer les tâches sélectionnées vers Notion", key="send_manual"):
            nb_envoyees = 0

            for i, t in enumerate(taches):
                if st.session_state.get(f"manual_check_{i}", False):
                    succes, message = creer_tache_notion(
                        t.get("task"),
                        t.get("priority"),
                        t.get("assignee"),
                        None,
                        statut_manual,
                        user_email
                    )
                    if succes:
                        nb_envoyees += 1
                    else:
                        st.session_state.notification_message = message
                        st.session_state.notification_type = "error"

            if nb_envoyees > 0:
                st.session_state.notification_message = f"{nb_envoyees} tâche(s) envoyée(s) vers Notion."
                st.session_state.notification_type = "success"
                st.session_state.manual_analysis = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        afficher_bloc_reunions(reunions, "manual")


with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Scan Gmail</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Analyse des derniers emails du compte Google connecté.</div>', unsafe_allow_html=True)

    nb_mails = st.slider("Nombre d'emails à vérifier :", 1, 5, 2)

    if st.button("🔍 Lancer le scan automatique", key="scan_outlook"):
        with st.spinner("Connexion à Gmail..."):
            access_token = _recuperer_access_token()

            if not access_token:
                st.session_state.notification_message = (
                    "Aucun token Gmail disponible. Déconnecte-toi puis reconnecte-toi pour autoriser Gmail."
                )
                st.session_state.notification_type = "error"
                st.session_state.scan_analysis = None
                st.rerun()

            emails = recuperer_derniers_emails_gmail(access_token, nb_mails)

            if isinstance(emails, str):
                st.error(emails)
                st.session_state.scan_analysis = None
            elif not emails:
                st.info("Aucun email trouvé.")
                st.session_state.scan_analysis = []
            else:
                analyses = []
                for mail in emails:
                    analyse = analyser_contenu(mail["corps"], "Email reçu")
                    analyses.append({
                        "mail": mail,
                        "tasks": analyse.get("tasks", []),
                        "meetings": analyse.get("meetings", [])
                    })
                st.session_state.scan_analysis = analyses
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.scan_analysis:
        for mail_index, bloc in enumerate(st.session_state.scan_analysis.copy()):
            mail = bloc["mail"]
            taches = bloc["tasks"]
            reunions = bloc["meetings"]

            st.markdown(f"""
            <div class="mail-box">
                <div class="mail-title">📧 {mail.get('sujet', 'Sans sujet')}</div>
                <div class="mail-meta">Expéditeur : {mail.get('expediteur', 'Inconnu')}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Voir le texte brut"):
                st.text(mail.get("corps", ""))

            if taches:
                st.markdown('<div class="section-title">Tâches détectées</div>', unsafe_allow_html=True)
                for task_index, t in enumerate(taches):
                    key = f"scan_{mail_index}_{task_index}"
                    if key not in st.session_state:
                        st.session_state[key] = True

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.checkbox(
                        f"{t.get('task', 'Tâche')} | {t.get('priority', 'Moyenne')} | {t.get('assignee', 'Non assigné')}",
                        key=key
                    )
                    st.markdown(
                        f"""
                        <div class="muted">
                            {_badge_priorite(t.get('priority', 'Moyenne'))}
                            <span class="badge badge-gray">{t.get('assignee', 'Non assigné')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown('<div class="card">', unsafe_allow_html=True)
                statut_mail = st.selectbox(
                    "Statut à appliquer pour ce mail",
                    ["À faire", "En cours", "Fait"],
                    key=f"statut_scan_mail_{mail_index}"
                )

                if st.button(
                    "Envoyer les tâches sélectionnées de ce mail vers Notion",
                    key=f"send_scan_mail_{mail_index}"
                ):
                    nb_envoyees_mail = 0

                    for task_index, t in enumerate(taches):
                        key = f"scan_{mail_index}_{task_index}"
                        if st.session_state.get(key, False):
                            succes, message = creer_tache_notion(
                                t.get("task"),
                                t.get("priority"),
                                t.get("assignee"),
                                None,
                                statut_mail,
                                user_email
                            )
                            if succes:
                                nb_envoyees_mail += 1
                            else:
                                st.session_state.notification_message = message
                                st.session_state.notification_type = "error"

                    if nb_envoyees_mail > 0:
                        st.session_state.notification_message = f"{nb_envoyees_mail} tâche(s) envoyée(s) pour ce mail."
                        st.session_state.notification_type = "success"
                        st.session_state.scan_analysis.pop(mail_index)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Pas d'action détectée dans ce mail.")

            if reunions:
                afficher_bloc_reunions(reunions, f"scan_{mail_index}")


with tab3:
    st.markdown('<div class="section-title">Dashboard des tâches</div>', unsafe_allow_html=True)

    if st.button("🔄 Actualiser le dashboard", key="refresh_dashboard"):
        st.rerun()

    succes, message, taches_notion = recuperer_taches_notion()

    if not succes:
        st.error(message)
    elif not taches_notion:
        st.info("Aucune tâche trouvée dans Notion.")
    else:
        df = pd.DataFrame(taches_notion)

        total = len(df)
        a_faire = len(df[df["Statut"] == "À faire"])
        en_cours = len(df[df["Statut"] == "En cours"])
        fait = len(df[df["Statut"] == "Fait"])

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Total tâches</div><div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">À faire</div><div class="kpi-value">{a_faire}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">En cours</div><div class="kpi-value">{en_cours}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Fait</div><div class="kpi-value">{fait}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        left, right = st.columns([1.1, 1.3])

        with left:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Répartition par statut</div>', unsafe_allow_html=True)

            df_statuts = pd.DataFrame({
                "Statut": ["À faire", "En cours", "Fait"],
                "Nombre": [a_faire, en_cours, fait]
            })

            fig = px.pie(
                df_statuts,
                names="Statut",
                values="Nombre",
                color="Statut",
                color_discrete_map={
                    "À faire": "#3B82F6",
                    "En cours": "#F59E0B",
                    "Fait": "#10B981"
                },
                hole=0.25
            )

            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Filtres</div>', unsafe_allow_html=True)

            colf1, colf2 = st.columns(2)
            with colf1:
                statuts_disponibles = sorted(df["Statut"].dropna().unique().tolist())
                filtre_statut = st.multiselect(
                    "Filtrer par statut",
                    statuts_disponibles,
                    default=statuts_disponibles
                )

                assignes_disponibles = sorted(df["Assigné"].dropna().unique().tolist())
                filtre_assigne = st.multiselect(
                    "Filtrer par assigné",
                    assignes_disponibles,
                    default=assignes_disponibles
                )

            with colf2:
                priorites_disponibles = sorted(df["Priorité"].dropna().unique().tolist())
                filtre_priorite = st.multiselect(
                    "Filtrer par priorité",
                    priorites_disponibles,
                    default=priorites_disponibles
                )

                createurs_disponibles = sorted([x for x in df["Créé par"].dropna().unique().tolist() if x])
                filtre_createur = st.multiselect(
                    "Filtrer par créateur",
                    createurs_disponibles,
                    default=createurs_disponibles if createurs_disponibles else []
                )
            st.markdown("</div>", unsafe_allow_html=True)

        df_filtre = df[
            df["Statut"].isin(filtre_statut)
            & df["Priorité"].isin(filtre_priorite)
            & df["Assigné"].isin(filtre_assigne)
        ]

        if createurs_disponibles:
            df_filtre = df_filtre[df_filtre["Créé par"].isin(filtre_createur)]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tableau des tâches</div>', unsafe_allow_html=True)
        st.dataframe(
            df_filtre[["Tâche", "Priorité", "Assigné", "Statut", "Créé par"]],
            use_container_width=True,
            hide_index=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


with tab4:
    st.markdown('<div class="section-title">Modifier le statut des tâches</div>', unsafe_allow_html=True)

    succes, message, taches_notion = recuperer_taches_notion()

    if not succes:
        st.error(message)
    elif not taches_notion:
        st.info("Aucune tâche trouvée dans Notion.")
    else:
        df = pd.DataFrame(taches_notion)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        colm1, colm2, colm3, colm4 = st.columns(4)

        with colm1:
            statuts_disponibles = sorted(df["Statut"].dropna().unique().tolist())
            filtre_statut_modif = st.multiselect(
                "Filtrer par statut",
                statuts_disponibles,
                default=statuts_disponibles,
                key="filtre_statut_modif"
            )

        with colm2:
            priorites_disponibles = sorted(df["Priorité"].dropna().unique().tolist())
            filtre_priorite_modif = st.multiselect(
                "Filtrer par priorité",
                priorites_disponibles,
                default=priorites_disponibles,
                key="filtre_priorite_modif"
            )

        with colm3:
            assignes_disponibles = sorted(df["Assigné"].dropna().unique().tolist())
            filtre_assigne_modif = st.multiselect(
                "Filtrer par assigné",
                assignes_disponibles,
                default=assignes_disponibles,
                key="filtre_assigne_modif"
            )

        with colm4:
            createurs_disponibles = sorted([x for x in df["Créé par"].dropna().unique().tolist() if x])
            filtre_createur_modif = st.multiselect(
                "Filtrer par créateur",
                createurs_disponibles,
                default=createurs_disponibles if createurs_disponibles else [],
                key="filtre_createur_modif"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        df_modif = df[
            df["Statut"].isin(filtre_statut_modif)
            & df["Priorité"].isin(filtre_priorite_modif)
            & df["Assigné"].isin(filtre_assigne_modif)
        ].copy()

        if createurs_disponibles:
            df_modif = df_modif[df_modif["Créé par"].isin(filtre_createur_modif)]

        if df_modif.empty:
            st.info("Aucune tâche ne correspond aux filtres.")
        else:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Modifier les statuts</div>', unsafe_allow_html=True)

            header = st.columns([4.3, 1.3, 1.8, 1.4, 2.2, 2, 1.4])
            header[0].markdown("**Tâche**")
            header[1].markdown("**Priorité**")
            header[2].markdown("**Assigné**")
            header[3].markdown("**Statut**")
            header[4].markdown("**Créé par**")
            header[5].markdown("**Nouveau statut**")
            header[6].markdown("**Action**")

            st.markdown('<div class="small-divider"></div>', unsafe_allow_html=True)

            for _, row in df_modif.iterrows():
                cols = st.columns([4.3, 1.3, 1.8, 1.4, 2.2, 2, 1.4])

                cols[0].write(row["Tâche"])
                cols[1].markdown(_badge_priorite(row["Priorité"]), unsafe_allow_html=True)
                cols[2].write(row["Assigné"])
                cols[3].markdown(_badge_statut(row["Statut"]), unsafe_allow_html=True)
                cols[4].write(row["Créé par"])

                options_statut = ["À faire", "En cours", "Fait"]
                index_statut = options_statut.index(row["Statut"]) if row["Statut"] in options_statut else 0

                nouveau_statut = cols[5].selectbox(
                    "Nouveau statut",
                    options_statut,
                    index=index_statut,
                    key=f"status_select_{row['id']}",
                    label_visibility="collapsed"
                )

                if cols[6].button("Mettre à jour", key=f"update_status_{row['id']}"):
                    succes_update, message_update = mettre_a_jour_statut_tache(row["id"], nouveau_statut)
                    if succes_update:
                        st.session_state.notification_message = "Statut mis à jour avec succès."
                        st.session_state.notification_type = "success"
                        st.rerun()
                    else:
                        st.session_state.notification_message = message_update
                        st.session_state.notification_type = "error"
                        st.rerun()

                st.markdown('<div class="small-divider"></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

if "notification_message" in st.session_state and st.session_state.notification_message:
    afficher_notification_fixe(
        st.session_state.notification_message,
        st.session_state.get("notification_type", "success")
    )
    st.session_state.notification_message = None
    st.session_state.notification_type = "success"

st.markdown("---")
st.caption("TaskFlow AI | Hackathon Demo 2026")