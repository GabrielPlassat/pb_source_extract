import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import re
from docx import Document

st.set_page_config(page_title="Aide à la formulation du problème", page_icon="⚡", layout="wide")

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

st.title("Assistant pour formuler un problématique")

tab1, tab2, tab3 = st.tabs(["📝 Aide au Prompt pour SofIA", "📂 Extraction & Export", "📝 Aide au Prompt Contraintes"])

# --- ONGLET 1 : AIDE AU PROMPT "SofIA" ---
with tab1: 
    st.header("1.Aide pour formuler le problème initial à SofIA")
    st.info("SofIA va être utilisé pour rédiger la problématique complète en utilisant sa base de connaissance des études et guides sur tous les domaines de la TE.")
    
    # Formulaire de questions
    q1 = st.text_area("1. Action et Sujet : Comment réduire / augmenter / modifier puis indiquer votre sujet de façon synthétique", placeholder="ex: développer la pratique de la marche au quotidien ? augmenter la part des EnR ?")
    q2 = st.text_input("2. Périmètre géographique :", placeholder="ex: dans tous les territoires")
    q3 = st.text_area("3. Cibles visées en priorité :", placeholder="ex: toutes les personnes à tous les âges")
    q4 = st.text_input("4. Objectif chiffré :", placeholder="ex: augmenter de 20% la part de la marche")
    q5 = st.text_area("5. Eventuellement, une action complémentaire proposée à SofIA ?", placeholder="ex: étudier plus particulièrement ...")

    if st.button("Générer le document de Prompt pour SofIA (.docx)"):
        # Création du document Word
        prompt_doc = Document()
        prompt_doc.add_heading("Prompt pour SofIA", 0)

# --- AJOUT DE L'IMAGE DANS LE DOCX ---
        try:
            prompt_doc.add_paragraph("Utilisez le prompt ci-dessous dans l'interface SofIA :")
            # On insère l'image (ajustez la largeur si nécessaire)
            from docx.shared import Inches
            prompt_doc.add_picture("sofia_q.png", width=Inches(5.5))
        except Exception as e:
            st.error(f"Erreur lors de l'insertion de l'image : {e}")
        
        # Construction de la phrase de prompt à partir des variables q1 à q5
        # On utilise f"..." pour assembler le texte proprement
        phrase_prompt = (
            f"Comment {q1} dans {q2}, en ciblant plus particulièrement {q3}. "
            f"Un premier objectif serait de {q4}. En complément, il est proposé de {q5}. "
            f"Quelles sont les principales données dans ce domaine, les acteurs à mobiliser, "
            f"les paramètres clés à travailler, les solutions déjà mises en œuvre, les principaux résultats déjà obtenus, "
            f"les projets ayant réussi, leurs résultats et ceux ayant échoué et leurs causes, les règles de fonctionnement "
            f"du système considéré, les paradigmes du système considéré et comment le transcender pour réduire le problème "
            f"et identifier de nouvelles solutions, les effets et conséquences systémiques liés à ce problème et aux futures "
            f"actions dans d’autres domaines, les recommandations pour intégrer les effets rebonds, boucles de rétroactions et cobénéfices ?"
        )
        
        # Organisation dans le document Word
        prompt_doc.add_heading("Votre base de prompt personnalisée :", level=1)
        prompt_doc.add_paragraph(phrase_prompt)
        
        prompt_doc.add_heading("Relire et reformuler si besoin avant de copier/coller dans Sofia : https://www.sofia-transition-ecologique.fr/", level=1)
  
        
        # Export
        prompt_buffer = io.BytesIO()
        prompt_doc.save(prompt_buffer)
        prompt_buffer.seek(0)
        
        st.download_button(
            label="📥 Télécharger votre prompt pour SofIA",
            data=prompt_buffer,
            file_name="Prompt_Initial_Sofia.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.header("2.Récupération de l'exportation")
    st.info("Vous avez copié/collé le prompt dans [SofIA](https://www.sofia-transition-ecologique.fr/). SofIA a généré une réponse. Cliquez sur Exporter la conversation avec le bouton à droite sur la barre bleue. Cela va générer un fichier chat_history.html.")
    uploaded_file = st.file_uploader("Glissez votre fichier chat_history.html ci dessous", type="html", key="uploader")

    if uploaded_file:
        content = uploaded_file.read().decode('utf-8')
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Export Document")
            doc_file = convert_html_to_doc_format(content)
            st.download_button("📥 Télécharger la réponse de SofIA au format(.doc)", doc_file, "Reponse_Sofia.doc", "application/msword")
            
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

# --- ONGLET 3 : AIDE AU PROMPT "CONTRAINTES" ---
with tab3:
    st.header("3.Aide pour compléter le problème initial avec un champs de contraintes")
    st.info("SofIA a généré une réponse présentant le domaine considéré, le contexte, les problèmes et principaux verrous, les acteurs à rassembler ainsi que des propositions d'actions. Les questions permettent de préciser le problème à résoudre et les différentes contraintes.")

    # Formulaire de questions
    q1 = st.text_area("Peut-on réduire le périmètre du problème sur un champs plus précis :")
    
    st.markdown("Est ce que le problème à résoudre est considéré comme compliqué, complexe ou Pernicieux (wicked) ? [Comprendre les différences](https://ademecloud-my.sharepoint.com/:b:/g/personal/gabriel_plassat_ademe_fr/IQB6qkN3Av0jSJIx8VBpilRIAYNfgfTtVLn0yf9kvh_LSio?e=YVwmLr) et [En savoir plus sur les problèmes Pernicieux](https://fr.wikipedia.org/wiki/Probl%C3%A8me_vicieux)")
    q2 = st.radio("Type de problème :", ["Compliqué", "Complexe", "Pernicieux (Wicked)"])

    q3 = st.text_area("Est ce que les douleurs liées au problème sont réellement perçues par les potentiels clients ? ou d'autres acteurs à préciser ? :")
    q4 = st.text_area("Quels sont les partenaires obligatoires à impliquer : futurs clients ou utilisateurs, activateurs qui vont aider et les potentiels compétiteurs ou acteurs qui vont freiner (en plus des acteurs identifiés par SofIA) : Mentionner les différents rôles et acteurs ci dessous")
    q5 = st.text_area("Quels seraient les bénéfices tangibles pour les bénéficiaires de l'intervention ? pour l'ADEME ? pour l'intérêt collectif ? :")
    q6 = st.text_area("Quels seraient les bénéfices intangibles pour les bénéficiaires de l'intervention ? pour l'ADEME ? pour l'intérêt collectif ? :")
    q7 = st.text_area("Quels sont les objectifs [opposables](https://www.icopilots.com/discours-il-opposable/) de l'intervention de l'ADEME de façon chiffrée ? Par ex. atteindre x TWh en 2030, réduire d'un facteur 2 ou 50% les émissions de X ou les parts modales de Y ... :")
    q8 = st.text_area("Quel est le budget éventuellement décrit sur plusieurs années ? :")
    q9 = st.text_area("Quel est le planning général (jalons et livrables à 6 mois, 1 an, etc.) :")
    q10 = st.text_area("Y a t-il une communication prévue ou des contraintes de visibilité pour l'ADEME :")
    q11 = st.text_area("Quels seraient les vecteurs marketing pour toucher les cibles ? :")
    q12 = st.text_area("Envie de préciser quelque chose en plus pour bien poser le problème à résoudre ? :")

    if st.button("Générer le document de cadrage (.docx)"):
        # Création du document Word
        prompt_doc = Document()
        prompt_doc.add_heading("Cadrage du Problème & Éléments de Prompt", 0)
        
        data = {
            "Périmètre précis": q1,
            "Nature du problème": q2,
            "Douleurs perçues": q3,
            "Partenaires additionnels": q4,
            "Bénéfices tangibles": q5,
            "Bénéfices intangibles": q6,
            "Objectifs précis et opposables": q7,
            "Budget prévisionnel": q8,
            "Planning et Jalons": q9,
            "Communication et Visibilité ADEME": q10,
            "Vecteurs marketing": q11,
            "Informations complémentaires": q12
        }
        prompt_doc.add_heading("Relire, compléter si besoin et copier/coller ce texte à la fin du fichier de réponse de SofIA", 0)

        
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
