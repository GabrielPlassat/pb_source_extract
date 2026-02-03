import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile

# Configuration de la page
st.set_page_config(page_title="Extracteur de Sources Sofia", page_icon="⚡")

st.title("⚡ Extracteur de Sources PDF")
st.write("Cet outil extrait automatiquement les documents (ADEME, PPE, etc.) cités dans votre historique Sofia.")

# Composant de téléchargement de fichier (Remplace Tkinter)
uploaded_file = st.file_uploader("Étape 1 : Glissez votre fichier historique .html ici", type="html")

if uploaded_file is not None:
    # Lecture du contenu HTML
    content = uploaded_file.read()
    soup = BeautifulSoup(content, 'html.parser')
    
    # Identification des sources dans le document
    sources = soup.find_all('div', class_='source-card')
    st.info(f"🔍 {len(sources)} sources détectées dans le document.")

    if st.button(f"Étape 2 : Lancer l'extraction"):
        # Création d'un buffer en mémoire pour le fichier ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            for i, source in enumerate(sources):
                # Extraction du lien et du titre
                link_tag = source.find('h2', class_='card-title').find('a') if source.find('h2', class_='card-title') else None
                
                if link_tag and link_tag.get('href'):
                    url = link_tag['href']
                    # Nettoyage du nom de fichier
                    titre = "".join([c for c in link_tag.get_text() if c.isalnum() or c in (' ', '_')]).strip()
                    nom_fichier = f"{i+1}_{titre[:50]}.pdf"
                    
                    status_text.text(f"⏳ Téléchargement de : {nom_fichier}")
                    
                    try:
                        # Requête vers la source (ex: ADEME, SG-MD)
                        resp = requests.get(url, timeout=15)
                        if resp.status_code == 200:
                            zf.writestr(nom_fichier, resp.content)
                    except Exception:
                        st.warning(f"⚠️ Impossible de récupérer : {nom_fichier}")
                
                progress_bar.progress((i + 1) / len(sources))

            status_text.text("✅ Extraction terminée !")

        # Bouton pour récupérer le ZIP final
        st.download_button(
            label="📥 Télécharger l'archive ZIP",
            data=zip_buffer.getvalue(),
            file_name="sources_extraites.zip",
            mime="application/zip"
        )
