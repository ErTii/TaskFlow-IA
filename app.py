import streamlit as st
import json

# Import de la logique de tes autres fichiers
from agent import analyser_texte_en_taches
from notion_api import creer_tache_notion

st.set_page_config(page_title="TaskFlow AI", page_icon="🤖")

st.title("🤖 TaskFlow AI")
st.subheader("L'Orchestrateur de Productivité")
st.write("Transformez vos réunions et e-mails en actions concrètes dans Notion.")

texte_utilisateur = st.text_area("Collez votre transcription de réunion ou vos e-mails ici :", height=200)

if st.button("Analyser et Créer les tâches"):
    if texte_utilisateur:
        with st.spinner("L'agent analyse la situation et contacte Notion..."):
            try:
                # 1. Le Cerveau IA extrait les tâches depuis le texte
                reponse_brute = analyser_texte_en_taches(texte_utilisateur)
                
                # Petit nettoyage au cas où ChatGPT ajoute des balises ```json autour de sa réponse
                if reponse_brute.startswith("```json"):
                    reponse_brute = reponse_brute.strip("```json").strip("```")
                elif reponse_brute.startswith("```"):
                    reponse_brute = reponse_brute.strip("```")
                    
                # On transforme le texte JSON en vraie liste utilisable par Python
                taches = json.loads(reponse_brute)
                
                st.success("✅ Analyse terminée ! Voici ce que l'Agent a exécuté :")
                
                # 2. Les Bras (API) créent les tâches une par une dans Notion
                for tache in taches:
                    nom = tache.get("task", "Tâche sans nom")
                    priorite = tache.get("priority", "Moyenne")
                    assigne = tache.get("assignee", "Inconnu")
                    
                    st.write(f"- **{nom}** (Priorité: {priorite} | Assigné à: {assigne})")
                    
                    # L'action autonome : envoi à l'API Notion
                    succes = creer_tache_notion(nom, priorite, assigne)
                    
                    if succes:
                        st.caption(f"✨ Ticket créé avec succès dans Notion !")
                    else:
                        st.error(f"❌ Erreur lors de la création de '{nom}' dans Notion. Vérifie tes clés API.")
                        
            except Exception as e:
                st.error(f"Une erreur est survenue avec l'IA ou le code : {e}")
                
    else:
        st.warning("⚠️ Veuillez entrer du texte avant de lancer l'analyse.")