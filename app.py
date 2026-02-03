import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
from docx import Document

# Configuration de la page
st.set_page_config(page_title="Extracteur de Sources Sofia", page_icon="⚡")

def convert_html_to_docx(html_content):
    """Transforme le contenu HTML en un document Word structuré."""
    doc = Document()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraction du titre principal
    h1 = soup.find('h1')
    if h1:
        doc.add_heading(h1.get_text(), 0)
    
    # Parcourir les sections de l'historique
    for div in soup.find_all(['div', 'p', 'h2', 'h3', 'h4']):
        text = div.get_text().strip()
        if not text:
            continue
            
        if div.name == 'h2':
            doc.add_heading(text, level=1)
        elif div.name == 'h3':
            doc.add_heading(text, level=2)
        elif div.name == 'h4':
            doc.add_heading(text, level=3)
        else:
            # On ajoute le texte normal (réponses, questions, extraits)
            doc.add_paragraph(text)
            
    # Sauvegarde dans un buffer
    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)
    return docx_buffer

st.title("⚡ Extracteur de Sources & Convertisseur")
st.write("Cet outil extrait les PDF sources et convertit votre historique en format Word (.doc).")

uploaded_file = st.file_uploader("Étape 1 : Glissez votre fichier historique .html ici", type="html")

if uploaded_file is not None:
    content = uploaded_file.read()
    soup = BeautifulSoup(content, 'html.parser')
    sources = soup.find_all('div', class_='source-card')
    
    st.info(f"🔍 {len(sources)} sources détectées.")

    # Colonnes pour les boutons de téléchargement
    col1, col2 = st.columns(2)

    # LIVRABLE 1 : LE DOCUMENT WORD
    with col1:
        st.subheader("📄 Format Word")
        docx_file = convert_html_to_docx(content)
        st.download_button(
            label="Télécharger l'historique (.docx)",
            data=docx_file,
            file_name="historique_sofia.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    # LIVRABLE 2 : LES SOURCES PDF
    with col2:
        st.subheader("📚 Sources PDF")
        if st.button("Préparer les sources"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                progress_bar = st.progress(0)
                for i, source in enumerate(sources):
                    link_tag = source.find('h2', class_='card-title').find('a') if source.find('h2', class_='card-title') else None
                    if link_tag and link_tag.get('href'):
                        url = link_tag['href']
                        titre = "".join([c for c in link_tag.get_text() if c.isalnum() or c in (' ', '_')]).strip()
                        nom_fichier = f"{i+1}_{titre[:50]}.pdf"
                        try:
                            resp = requests.get(url, timeout=10)
                            if resp.status_code == 200:
                                zf.writestr(nom_fichier, resp.content)
                        except:
                            pass
                    progress_bar.progress((i + 1) / len(sources))
            
            st.download_button(
                label="Télécharger le ZIP des sources",
                data=zip_buffer.getvalue(),
                file_name="sources_extraites.zip",
                mime="application/zip"
            )
