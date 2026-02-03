import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import re
from docx import Document

st.set_page_config(page_title="Sofia - Assistant & Export", page_icon="⚡", layout="wide")

# --- FONCTIONS DE CONVERSION ---

def markdown_to_html_table(text):
    """Convertit les tableaux Markdown en HTML pour Word."""
    lines = text.strip().split('\n')
    html_table = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    for i, line in enumerate(lines):
        if '|---' in line: continue
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if not cells: continue
        tag = 'th' if i == 0 else 'td'
        html_table += '<tr>'
        for cell in cells:
            cell_content = cell.replace('- ', '<br>- ')
            html_table += f'<{tag} style="padding: 8px; vertical-align: top;">{cell_content}</{tag}>'
        html_table += '</tr>'
    return html_table + '</table>'

def convert_html_to_doc_format(html_content):
    """Encapsule le contenu pour Word avec gestion des tableaux."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for element in soup.find_all(string=re.compile(r"\|.*\|")):
        if '|' in element.string and '---' in element.string:
            new_table_html = markdown_to_html_table(element.string)
            element.replace_with(BeautifulSoup(new_table_html, 'html.parser'))
    
    html_header = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"></head><body>'
    full_html = html_header + str(soup) + '</body></html>'
    return io.BytesIO(full_html.encode('utf-8'))

# --- INTERFACE STREAMLIT ---

st.title("SofIA - Assistant de Transition Énergétique")

tab1, tab2 = st.tabs(["📂 Extraction & Export", "📝 Aide au Prompt"])

# --- ONGLET 1 : EXTRACTION ---
with tab1:
    st.header("Récupération des livrables")
    uploaded_file = st.file_uploader("Glissez votre fichier chat_history.html", type="html", key="uploader")

    if uploaded_file:
        content = uploaded_file.read().decode('utf-8')
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Export Document")
            doc_file = convert_html_to_doc_format(content)
            st.download_button("📥 Télécharger l'historique (.doc)", doc_file, "Historique_Sofia.doc", "application/msword")
            
        with col2:
            st.subheader("📚 Sources PDF")
            if st.button("Préparer le ZIP"):
                soup = BeautifulSoup(content, 'html.parser')
                sources = soup.find_all('div', class_='source-card')
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i, source in enumerate(sources):
                        link = source.find('h2', class_='card-title').find('a')
                        if link and link.get('href'):
                            try:
                                resp = requests.get(link['href'], timeout=10)
                                name = f"{i+1}_{link.get_text()[:50].strip()}.pdf".replace('/', '_')
                                zf.writestr(name, resp.content)
                            except: pass
                st.download_button("📥 Télécharger le .zip", zip_buffer.getvalue(), "Sources.zip", "application/zip")

# --- ONGLET 2 : AIDE AU PROMPT ---
with tab2:
    st.header("Aide à la définition du problème")
    st.info("SofIA a généré un fichier présentant le domaine considéré, le contexte, les problèmes et principaux verrous, les acteurs à rassembler ainsi que des propositions d'actions. Les questions permettent de préciser le problème à résoudre et les différentes contraintes.")

    # Formulaire de questions
    q1 = st.text_area("Peut-on réduire le périmètre du problème sur un champs plus précis :")
    
    st.markdown("Est ce que le problème à résoudre est considéré comme compliqué, complexe ou vicieux (wicked) ? [En savoir plus sur les types de problèmes](https://fr.wikipedia.org/wiki/Probl%C3%A8me_vicieux)")
    q2 = st.radio("Type de problème :", ["Compliqué", "Complexe", "Vicieux (Wicked)"])
    
    q3 = st.text_area("Quels sont les partenaires obligatoires à impliquer (en plus des acteurs identifiés par SofIA) :")
    q4 = st.text_area("Quel est le budget éventuellement décrit sur plusieurs années ? :")
    q5 = st.text_area("Quel est le planning général (jalons et livrables à 6 mois, 1 an, etc.) :")
    q6 = st.text_area("Communication prévue ou contraintes de visibilité ADEME :")
    q7 = st.text_area("Envie de nous dire quelque chose en plus ? :")

    if st.button("Générer le document de cadrage (.docx)"):
        # Création du document Word
        prompt_doc = Document()
        prompt_doc.add_heading("Cadrage du Problème & Éléments de Prompt", 0)
        
        data = {
            "Périmètre précis": q1,
            "Nature du problème": q2,
            "Partenaires additionnels": q3,
            "Budget prévisionnel": q4,
            "Planning et Jalons": q5,
            "Communication et Visibilité ADEME": q6,
            "Informations complémentaires": q7
        }
        
        for key, value in data.items():
            prompt_doc.add_heading(key, level=1)
            prompt_doc.add_paragraph(value if value else "Non précisé")
        
        # Export
        prompt_buffer = io.BytesIO()
        prompt_doc.save(prompt_buffer)
        prompt_buffer.seek(0)
        
        st.download_button(
            label="📥 Télécharger votre document de cadrage",
            data=prompt_buffer,
            file_name="Cadrage_Projet_Sofia.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
