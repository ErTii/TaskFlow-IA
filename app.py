import streamlit as st
import pandas as pd
import plotly.express as px
from agent import analyser_contenu
from notion_api import (
    creer_tache_notion,
    recuperer_taches_notion,
    mettre_a_jour_statut_tache,
)
from fetch_emails import recuperer_derniers_emails
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
if not st.user.is_logged_in:
    st.markdown("""
        <style>
        .login-box {
            max-width: 700px;
            margin: 60px auto;
            padding: 32px;
            border-radius: 18px;
            background: #f8f9fa;
            border: 1px solid #e5e7eb;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="login-box">
            <h1>🚀 TaskFlow AI</h1>
            <p style="font-size:18px;">
                Connectez-vous avec Google pour accéder à l'application.
            </p>
            <p style="color:#6b7280;">
                Seuls les comptes ajoutés comme testeurs Google peuvent se connecter.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.button("Se connecter avec Google", on_click=st.login, use_container_width=True)
    st.stop()


# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .main {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# HEADER + USER INFO
# -----------------------------
st.title("🚀 TaskFlow AI")
st.subheader("L'IA qui transforme vos flux en actions Notion")

with st.sidebar:
    st.markdown("## Compte connecté")
    st.write(f"**Nom :** {getattr(st.user, 'name', 'Utilisateur')}")
    st.write(f"**Email :** {getattr(st.user, 'email', 'Non disponible')}")
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


def afficher_bloc_taches(taches, prefixe):
    if not taches:
        st.info("Aucune tâche détectée.")
        return

    for i, t in enumerate(taches):
        key = f"{prefixe}_check_{i}"
        if key not in st.session_state:
            st.session_state[key] = True

        st.checkbox(
            f"{t.get('task', 'Tâche')} | {t.get('priority', 'Moyenne')} | {t.get('assignee', 'Non assigné')}",
            key=key
        )


def afficher_bloc_reunions(reunions, prefixe):
    if not reunions:
        return

    st.markdown("### Réunions détectées")

    for i, reunion in enumerate(reunions):
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


with tab1:
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

    if st.session_state.manual_analysis:
        resultat = st.session_state.manual_analysis
        taches = resultat.get("tasks", [])
        reunions = resultat.get("meetings", [])

        st.markdown("### Tâches détectées")
        afficher_bloc_taches(taches, "manual")

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
                        statut_manual
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

        afficher_bloc_reunions(reunions, "manual")


with tab2:
    st.write("Scannez vos derniers emails pour extraire des tâches.")
    nb_mails = st.slider("Nombre d'emails à vérifier :", 1, 5, 2)

    if st.button("🔍 Lancer le scan automatique", key="scan_outlook"):
        with st.spinner("Connexion à la boîte mail..."):
            emails = recuperer_derniers_emails(nb_mails)

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

    if st.session_state.scan_analysis:
        for mail_index, bloc in enumerate(st.session_state.scan_analysis.copy()):
            mail = bloc["mail"]
            taches = bloc["tasks"]
            reunions = bloc["meetings"]

            st.markdown("---")
            st.write(f"📧 **Mail :** {mail.get('sujet', 'Sans sujet')}")
            st.write(f"**Expéditeur :** {mail.get('expediteur', 'Inconnu')}")

            with st.expander("Voir le texte brut"):
                st.text(mail.get("corps", ""))

            if taches:
                st.markdown("**Tâches détectées :**")
                for task_index, t in enumerate(taches):
                    key = f"scan_{mail_index}_{task_index}"
                    if key not in st.session_state:
                        st.session_state[key] = True

                    st.checkbox(
                        f"{t.get('task', 'Tâche')} | {t.get('priority', 'Moyenne')} | {t.get('assignee', 'Non assigné')}",
                        key=key
                    )

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
                                statut_mail
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
            else:
                st.write("Pas d'action détectée dans ce mail.")

            if reunions:
                st.markdown("**Réunions détectées :**")
                afficher_bloc_reunions(reunions, f"scan_{mail_index}")


with tab3:
    st.markdown("## Dashboard des tâches Notion")

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

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total tâches", total)
        col2.metric("À faire", a_faire)
        col3.metric("En cours", en_cours)
        col4.metric("Fait", fait)

        st.markdown("### Répartition par statut")

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
            hole=0.2
        )

        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Filtres")

        colf1, colf2, colf3 = st.columns(3)

        with colf1:
            statuts_disponibles = sorted(df["Statut"].dropna().unique().tolist())
            filtre_statut = st.multiselect(
                "Filtrer par statut",
                statuts_disponibles,
                default=statuts_disponibles
            )

        with colf2:
            priorites_disponibles = sorted(df["Priorité"].dropna().unique().tolist())
            filtre_priorite = st.multiselect(
                "Filtrer par priorité",
                priorites_disponibles,
                default=priorites_disponibles
            )

        with colf3:
            assignes_disponibles = sorted(df["Assigné"].dropna().unique().tolist())
            filtre_assigne = st.multiselect(
                "Filtrer par assigné",
                assignes_disponibles,
                default=assignes_disponibles
            )

        df_filtre = df[
            df["Statut"].isin(filtre_statut)
            & df["Priorité"].isin(filtre_priorite)
            & df["Assigné"].isin(filtre_assigne)
        ]

        st.markdown("### Tableau des tâches")
        st.dataframe(
            df_filtre[["Tâche", "Priorité", "Assigné", "Statut"]],
            use_container_width=True,
            hide_index=True
        )


with tab4:
    st.markdown("## Modifier le statut des tâches")

    succes, message, taches_notion = recuperer_taches_notion()

    if not succes:
        st.error(message)
    elif not taches_notion:
        st.info("Aucune tâche trouvée dans Notion.")
    else:
        df = pd.DataFrame(taches_notion)

        colm1, colm2, colm3 = st.columns(3)

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

        df_modif = df[
            df["Statut"].isin(filtre_statut_modif)
            & df["Priorité"].isin(filtre_priorite_modif)
            & df["Assigné"].isin(filtre_assigne_modif)
        ].copy()

        if df_modif.empty:
            st.info("Aucune tâche ne correspond aux filtres.")
        else:
            st.markdown("### Modifier les statuts")

            header = st.columns([5, 1.5, 1.8, 1.5, 2, 1.5])
            header[0].markdown("**Tâche**")
            header[1].markdown("**Priorité**")
            header[2].markdown("**Assigné**")
            header[3].markdown("**Statut actuel**")
            header[4].markdown("**Nouveau statut**")
            header[5].markdown("**Action**")

            st.markdown("---")

            for _, row in df_modif.iterrows():
                cols = st.columns([5, 1.5, 1.8, 1.5, 2, 1.5])

                cols[0].write(row["Tâche"])
                cols[1].write(row["Priorité"])
                cols[2].write(row["Assigné"])
                cols[3].write(row["Statut"])

                options_statut = ["À faire", "En cours", "Fait"]
                index_statut = options_statut.index(row["Statut"]) if row["Statut"] in options_statut else 0

                nouveau_statut = cols[4].selectbox(
                    "Nouveau statut",
                    options_statut,
                    index=index_statut,
                    key=f"status_select_{row['id']}",
                    label_visibility="collapsed"
                )

                if cols[5].button("Mettre à jour", key=f"update_status_{row['id']}"):
                    succes_update, message_update = mettre_a_jour_statut_tache(row["id"], nouveau_statut)
                    if succes_update:
                        st.session_state.notification_message = "Statut mis à jour avec succès."
                        st.session_state.notification_type = "success"
                        st.rerun()
                    else:
                        st.session_state.notification_message = message_update
                        st.session_state.notification_type = "error"
                        st.rerun()

                st.markdown("---")

if "notification_message" in st.session_state and st.session_state.notification_message:
    afficher_notification_fixe(
        st.session_state.notification_message,
        st.session_state.get("notification_type", "success")
    )
    st.session_state.notification_message = None
    st.session_state.notification_type = "success"

st.markdown("---")
st.caption("TaskFlow AI | Hackathon Demo 2026")