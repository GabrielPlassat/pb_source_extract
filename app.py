import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
from docx import Document
from docx.shared import Pt

# Configuration de la page
st.set_page_config(page_title="Extracteur Sofia Pro", page_icon="📝")

def html_to_docx_pro(html_content):
    """Convertisseur avancé HTML vers DOCX conservant tableaux et structures."""
    doc = Document()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Titre principal (H1)
    h1 = soup.find('h1')
    if h1:
        doc.add_heading(h1.get_text(), 0)

    # On cible les éléments principaux de l'historique
    # On itère sur les éléments de niveau supérieur dans le body
    for element in soup.find_all(['h2', 'h3', 'div', 'table'], recursive=True):
        
        # 1. Gestion des Titres
        if element.name in ['h2', 'h3']:
            level = 1 if element.name == 'h2' else 2
            doc.add_heading(element.get_text().strip(), level=level)

        # 2. Gestion des Tableaux (Structure clé pour les acteurs/comparaisons)
        elif element.name == 'table':
            rows = element.find_all('tr')
            if rows:
                word_table = doc.add_table(rows=len(rows), cols=len(rows[0].find_all(['td', 'th'])))
                word_table.style = 'Table Grid'
                for i, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    for j, cell in enumerate(cells):
                        word_table.cell(i, j).text = cell.get_text().strip()

        # 3. Gestion des blocs de contenu (Questions / Réponses / Reformulations)
        elif element.name == 'div':
            # On ignore le contenu détaillé des sources mais on garde le titre
            if 'sources' in element.get('class', []):
                doc.add_heading("Sources associées", level=1)
                source_titles = element.find_all('h2', class_='card-title')
                for s_title in source_titles:
                    doc.add_paragraph(s_title.get_text().strip(), style='List Bullet')
                continue # On ne va pas plus loin dans le div des sources

            # Pour les autres div, on traite le texte s'il n'est pas déjà dans un tableau
            if not element.find_parent('table'):
                text = element.get_text().strip()
                if text and len(text) > 1:
                    # Si c'est un paragraphe de réponse Sofia
                    p = doc.add_paragraph(text)
                    if 'response' in element.get('class', []):
                        p.style = 'Body Text'

    # Sauvegarde
    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)
    return docx_buffer

st.title("⚡ Sofia Export Pro")
st.write("Convertissez votre historique en Word structuré et téléchargez les sources PDF.")

uploaded_file = st.file_uploader("Glissez votre fichier chat_history.html", type="html")

if uploaded_file:
    content = uploaded_file.read()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Document Word")
        with st.spinner("Génération du Word..."):
            docx_file = html_to_docx_pro(content)
            st.download_button(
                label="📥 Télécharger le .docx",
                data=docx_file,
                file_name="Historique_Sofia_Clean.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        st.caption("Conserve la structure, les tableaux et les titres.")

    with col2:
        st.subheader("📚 Sources PDF")
        if st.button("Préparer le ZIP des sources"):
            soup = BeautifulSoup(content, 'html.parser')
            sources = soup.find_all('div', class_='source-card')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                progress = st.progress(0)
                for i, source in enumerate(sources):
                    link = source.find('h2', class_='card-title').find('a')
                    if link and link.get('href'):
                        try:
                            resp = requests.get(link['href'], timeout=10)
                            name = f"{i+1}_{link.get_text()[:50].strip()}.pdf".replace('/', '_')
                            zf.writestr(name, resp.content)
                        except: pass
                    progress.progress((i+1)/len(sources))
            
            st.download_button(
                label="📥 Télécharger le .zip",
                data=zip_buffer.getvalue(),
                file_name="Sources_Sofia.zip",
                mime="application/zip"
            )
