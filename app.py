import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import re
import docx
import pypdf
from docx import Document
from docx.oxml.shared import qn
from docx.oxml import OxmlElement
from docx.shared import Inches

# Configuration de la page (DOIT être la première commande Streamlit)
st.set_page_config(page_title="Architecte des Transitions", page_icon="🏗️", layout="wide")

def extract_text_from_file(uploaded_file):
    """Extrait le texte brut d'un fichier PDF, DOCX ou TXT."""
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif uploaded_file.name.endswith('.txt'):
            text = uploaded_file.read().decode('utf-8')
    except Exception as e:
        return f"Erreur de lecture du fichier : {e}"
    return text

def add_hyperlink(paragraph, url, text):
    """Insère un hyperlien cliquable dans un paragraphe Word."""
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Appliquer le style bleu et souligné
    c = OxmlElement('w:color')
    c.set(qn('w:val'), '0000FF')
    rPr.append(c)
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(u)

    new_run.append(rPr)
    t = OxmlElement('w:t')
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)

    paragraph._p.append(hyperlink)
    return hyperlink

def clean_html_advanced(html_content):
    """Nettoie le HTML de SofIA et transforme les tableaux en texte structuré."""
    if not html_content: return ""
    soup = BeautifulSoup(html_content, 'html.parser')

    for element in soup(["script", "style", "header", "footer", "nav", "button", "input"]):
        element.decompose()

    for table in soup.find_all('table'):
        table_text = "\n"
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['td', 'th'])
            cols_text = [ele.get_text(separator=" ").strip().replace("\n", " ") for ele in cols]
            line = "| " + " | ".join(cols_text) + " |"
            table_text += line + "\n"
        table_text += "\n"
        table.replace_with(table_text)

    text = soup.get_text(separator='\n\n')
    return re.sub(r'\n\s*\n', '\n\n', text).strip()

def convert_html_to_doc_format(html_content):
    """Encapsule le contenu pour Word avec gestion des tableaux."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Correction légère pour éviter les erreurs si markdown_to_html_table n'est pas défini
    html_header = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"></head><body>'
    full_html = html_header + str(soup) + '</body></html>'
    return io.BytesIO(full_html.encode('utf-8'))

# --- INITIALISATION SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cadrage" not in st.session_state:
    st.session_state.cadrage = {}
if 'prompt_genere' not in st.session_state:
    st.session_state.prompt_genere = False

# --- HEADER (LOGO + TITRE PROJET) ---
col_logo, col_titre = st.columns([1, 5])

with col_logo:
    try:
        st.image("LOGO ARC.jpg", use_container_width=True)
    except:
        st.warning("Logo non trouvé")

with col_titre:
    st.markdown("""
        <div style='margin-top: 20px;'>
            <h2 style='color: #2E4053;'>Projet Exploratoire Formation IMT - l'Architecte des Transitions</h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- INTERFACE STREAMLIT ---
st.title("Assistant pour formuler un problématique")

tab1, tab2, tab3, tab4 = st.tabs(["📝 1.Aide au Prompt pour SofIA", "📂 2.Extraction & Export", "📝 3.Aide au Prompt Contraintes", "🤖 4. Eval IA"])

# --- ONGLET 1 : AIDE AU PROMPT "SofIA" ---
with tab1: 
    st.header("1.Aide pour formuler le problème initial à SofIA")
    st.info("SofIA va être utilisé pour rédiger la problématique complète. Les champs ci-dessous sont à renseigner pour générer votre Prompt.")
    
    q1 = st.text_area("1. Votre objectif principal :", placeholder="ex: développer la pratique de la marche au quotidien")
    q2 = st.text_input("2. Périmètre géographique :", placeholder="ex: dans tous les territoires")
    q3 = st.text_area("3. Cibles visées en priorité :", placeholder="ex: toutes les personnes à tous les âges")
    q4 = st.text_input("4. Objectif chiffré :", placeholder="ex: augmenter de 20% la part de la marche")
    q5 = st.text_area("5. Action complémentaire ?", placeholder="ex: étudier plus particulièrement ...")
    
    if st.button("Générer le document de Prompt pour SofIA (.docx)"):
        prompt_doc = Document()
        prompt_doc.add_heading("Prompt pour SofIA", 0)

        try:
            prompt_doc.add_paragraph("Utilisez le prompt ci-dessous dans l'interface SofIA :")
            prompt_doc.add_picture("sofia_q.png", width=Inches(5.5))
        except Exception as e:
            st.error(f"Erreur lors de l'insertion de l'image : {e}")
        
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
        
        prompt_doc.add_heading("Votre base de prompt personnalisée :", level=1)
        prompt_doc.add_paragraph(phrase_prompt)
        
        prompt_doc.add_heading("Lien vers Sofia : https://www.sofia-transition-ecologique.fr/", level=1)
        p = prompt_doc.add_paragraph("Ce document complet est à relire. Se connecter à ")
        add_hyperlink(p, "https://www.sofia-transition-ecologique.fr/", "SofIA")
        
        prompt_buffer = io.BytesIO()
        prompt_doc.save(prompt_buffer)
        prompt_buffer.seek(0)
        
        st.download_button(
            label="📥 Télécharger votre prompt pour SofIA",
            data=prompt_buffer,
            file_name="Prompt_Initial_Sofia.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            on_click=lambda: st.session_state.update({"prompt_genere": True})
        )

        if st.session_state.prompt_genere:
            st.markdown("---")
            st.success("✅ Document généré avec succès !")
            st.markdown("### 🚀 Étape suivante : Connectez-vous à [Sofia](https://www.sofia-transition-ecologique.fr/)")

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.header("2.Récupération de l'exportation")
    st.info("Importez le fichier chat_history.html généré par SofIA.")
    uploaded_file = st.file_uploader("Glissez votre fichier chat_history.html ici", type="html", key="uploader")

    if uploaded_file:
        content = uploaded_file.read().decode('utf-8')
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Export Document")
            doc_file = convert_html_to_doc_format(content)
            st.download_button("📥 Télécharger la réponse (.doc)", doc_file, "Reponse_Sofia.doc", "application/msword")
            
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
    st.header("3.Cadrage du problème et contraintes")
    c1 = st.text_area("Périmètre réduit du problème :")
    c2 = st.radio("Type de problème :", ["Compliqué", "Complexe", "Pernicieux (Wicked)"])
    c3 = st.text_area("Douleurs perçues par les acteurs :")
    c4 = st.text_area("Partenaires obligatoires / Compétiteurs :")
    c5 = st.text_area("Bénéfices tangibles :")
    c6 = st.text_area("Bénéfices intangibles :")
    c7 = st.text_area("Objectifs chiffrés et opposables :")
    c8 = st.text_area("Budget prévisionnel :")
    c9 = st.text_area("Planning et jalons :")
    c10 = st.text_area("Communication / Visibilité :")
    c11 = st.text_area("Vecteurs marketing :")
    c12 = st.text_area("Informations complémentaires :")

    if st.button("Générer le document de cadrage (.docx)"):
        prompt_doc = Document()
        prompt_doc.add_heading("Cadrage du Problème & Prompt pour Eval", 0)

        p = prompt_doc.add_paragraph("Ce document est à fournir à l'Assistant Eval. Se connecter à ")
        add_hyperlink(p, "https://m365.cloud.microsoft/chat/?titleId=T_7b923e69-c9aa-4317-d331-4647b285be26", "Eval")
       
        data = {
            "Périmètre": c1, "Nature": c2, "Douleurs": c3, "Partenaires": c4,
            "Bénéfices T": c5, "Bénéfices I": c6, "Objectifs": c7,
            "Budget": c8, "Planning": c9, "Com": c10, "Marketing": c11, "Infos": c12
        }
        
        for key, value in data.items():
            prompt_doc.add_heading(key, level=1)
            prompt_doc.add_paragraph(value if value else "Non précisé")
        
        prompt_buffer = io.BytesIO()
        prompt_doc.save(prompt_buffer)
        prompt_buffer.seek(0)
        
        st.download_button(
            label="📥 Télécharger votre document de cadrage",
            data=prompt_buffer,
            file_name="Cadrage_Projet_Sofia.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# --- ONGLET 4 : EVAL IA ---
with tab4:
    st.header("🤖 Génération de la Stratégie (Mode Externe)")
    st.info("Ce module fusionne l'analyse SofIA et vos contraintes de cadrage dans un seul document optimisé pour l'IA.")
