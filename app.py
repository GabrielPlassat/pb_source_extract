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
if 'fusion_generee' not in st.session_state:
    st.session_state.fusion_generee = False

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

def convert_html_to_doc_format(html_content):
    """Encapsule le contenu pour Word avec gestion des tableaux et style HTML conservé."""
    soup = BeautifulSoup(html_content, 'html.parser')
    html_header = (
        '<html xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:w="urn:schemas-microsoft-com:office:word" '
        'xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"></head><body>'
    )
    full_html = html_header + str(soup) + '</body></html>'
    return io.BytesIO(full_html.encode('utf-8'))

def build_constraints_block(data: dict) -> str:
    """Construit un bloc HTML structuré pour les contraintes (onglet 3)."""
    # Tableau simple en HTML pour garder une forme propre dans Word
    rows = []
    labels = {
        "Périmètre": "Périmètre réduit du problème",
        "Nature": "Type de problème",
        "Douleurs": "Douleurs perçues par les acteurs",
        "Partenaires": "Partenaires obligatoires / Compétiteurs",
        "Bénéfices T": "Bénéfices tangibles",
        "Bénéfices I": "Bénéfices intangibles",
        "Objectifs": "Objectifs chiffrés et opposables",
        "Budget": "Budget prévisionnel",
        "Planning": "Planning et jalons",
        "Com": "Communication / Visibilité",
        "Marketing": "Vecteurs marketing",
        "Infos": "Informations complémentaires"
    }
    for k, v in data.items():
        label = labels.get(k, k)
        content = v if v else "Non précisé"
        rows.append(
            f"<tr><th style='text-align:left;padding:4px 8px;'>{label}</th>"
            f"<td style='padding:4px 8px;'>{content}</td></tr>"
        )
    table_html = (
        "<h2>Cadrage du problème et contraintes</h2>"
        "<table border='1' style='border-collapse:collapse;width:100%;'>"
        f"{''.join(rows)}"
        "</table>"
    )
    return table_html

def merge_html_and_constraints(sofia_html: str, constraints_data: dict) -> io.BytesIO:
    """
    Fusionne le HTML de SofIA et le bloc de contraintes (en HTML)
    dans un seul fichier .doc utilisable par Word.
    """
    constraints_html = build_constraints_block(constraints_data)
    sofia_part = BeautifulSoup(sofia_html, 'html.parser')

    # On encapsule les deux sections dans un même body pour que Word garde la mise en forme HTML
    merged_html = (
        '<html xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:w="urn:schemas-microsoft-com:office:word" '
        'xmlns="http://www.w3.org/TR/REC-html40">'
        '<head><meta charset="utf-8"></head><body>'
        '<h1>Analyse SofIA</h1>'
        f'{str(sofia_part)}'
        '<hr/>'
        f'{constraints_html}'
        '</body></html>'
    )
    return io.BytesIO(merged_html.encode('utf-8'))

# --- INITIALISATION SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cadrage" not in st.session_state:
    st.session_state.cadrage = {}
if 'prompt_genere' not in st.session_state:
    st.session_state.prompt_genere = False
if 'sofia_html' not in st.session_state:
    st.session_state.sofia_html = None

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

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 1.Aide au Prompt pour SofIA",
    "📂 2.Extraction & Export",
    "📝 3.Aide au Prompt Contraintes",
    "🤖 4. Eval IA"
])

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
        # On stocke le HTML pour réutilisation dans l'onglet 4
        st.session_state.sofia_html = content

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Export Document")
            doc_file = convert_html_to_doc_format(content)
            st.download_button(
                "📥 Télécharger la réponse (.doc)",
                doc_file,
                "Reponse_Sofia.doc",
                "application/msword"
            )
            
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
                            except:
                                pass
                st.download_button(
                    "📥 Télécharger le .zip",
                    zip_buffer.getvalue(),
                    "Sources.zip",
                    "application/zip"
                )

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

    # On mémorise les contraintes pour l'onglet 4
    st.session_state.cadrage = {
        "Périmètre": c1, "Nature": c2, "Douleurs": c3, "Partenaires": c4,
        "Bénéfices T": c5, "Bénéfices I": c6, "Objectifs": c7,
        "Budget": c8, "Planning": c9, "Com": c10, "Marketing": c11, "Infos": c12
    }

    if st.button("Générer le document de cadrage (.docx)"):
        prompt_doc = Document()
        prompt_doc.add_heading("Cadrage du Problème & Prompt pour Eval", 0)

        p = prompt_doc.add_paragraph("Ce document est à fournir à l'Assistant Eval. Se connecter à ")
        add_hyperlink(
            p,
            "https://m365.cloud.microsoft/chat/?titleId=T_7b923e69-c9aa-4317-d331-4647b285be26",
            "Eval"
        )
       
        for key, value in st.session_state.cadrage.items():
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

# --- ONGLET 4 : EVAL IA (FUSION) ---
with tab4:
    st.header("🤖 Génération de la Stratégie (Mode Externe)")
    st.info(
        "Ce module fusionne l'analyse SofIA (onglet 2) et vos contraintes de cadrage (onglet 3) "
        "dans un seul document optimisé pour l'IA."
    )

    if st.session_state.get("sofia_html") is None:
        st.warning("Veuillez d'abord importer le fichier chat_history.html dans l'onglet 2.")
    else:
        # Bouton pour générer le document fusionné
        if st.button("Générer le document fusionné (.doc)"):
            merged_file = merge_html_and_constraints(
                st.session_state.sofia_html,
                st.session_state.cadrage
            )
            st.session_state.merged_file = merged_file
            st.session_state.fusion_generee = True

        # Si le document a déjà été généré dans cette session
        if st.session_state.get("fusion_generee", False) and st.session_state.get("merged_file") is not None:
            st.download_button(
                label="📥 Télécharger le document fusionné",
                data=st.session_state.merged_file,
                file_name="Analyse_Sofia_et_Cadrage.doc",
                mime="application/msword"
            )

            st.markdown("---")
            st.success("✅ Document fusionné généré avec succès.")

            # Bouton pour ouvrir le GEM dans un nouvel onglet
            gem_url = "https://gemini.google.com/gem/1y9w9p-YCpKER7F9enlRczopToIylE-NP?usp=sharing"
            if st.button("➡️ Aller vers le GEM pour poursuivre l'analyse"):
                # Utilisation de JavaScript pour ouvrir un nouvel onglet
                js = f"window.open('{gem_url}', '_blank').focus();"
                st.components.v1.html(f"<script>{js}</script>", height=0)


