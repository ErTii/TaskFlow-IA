import streamlit as st

# Configuration de la page
st.set_page_config(page_title="TaskFlow AI", page_icon="🤖")

st.title("🤖 TaskFlow AI")
st.subheader("L'Orchestrateur de Productivité")
st.write("Transformez vos longs fils d'e-mails et vos réunions en actions concrètes.")

# Zone où l'utilisateur va coller son texte
texte_utilisateur = st.text_area("Collez votre transcription de réunion ou vos e-mails ici :", height=200)

# Le bouton qui déclenche l'IA
if st.button("Analyser et Créer les tâches"):
    if texte_utilisateur:
        st.info("L'agent analyse la situation... Veuillez patienter.")
        
        # --- C'est ici que nous mettrons l'intelligence (OpenAI + Notion) plus tard ---
        
        st.success("✅ Analyse terminée ! (Ceci est une simulation pour l'interface)")
        st.write("**Résumé :** L'équipe a discuté de la nouvelle campagne marketing.")
        st.write("**Tâche détectée :** Préparer les visuels (Assigné à : Design).")
        
    else:
        st.warning("⚠️ Veuillez entrer du texte avant de lancer l'analyse.")