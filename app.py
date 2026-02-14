import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import re
from docx import Document
from docx.oxml.shared import qn
from docx.oxml import OxmlElement
import docx
import google.generativeai as genai

# --- HEADER (LOGO + TITRE PROJET) ---
col_logo, col_titre = st.columns([1, 5])

with col_logo:
    # Affiche le logo (assurez-vous que le fichier est bien à la racine)
    try:
        st.image("LOGO ARC.jpg", use_container_width=True)
    except:
        st.warning("Logo non trouvé")

with col_titre:
    # Utilisation de HTML pour un alignement vertical et une mise en forme spécifiques
    st.markdown("""
        <div style='margin-top: 20px;'>
            <h2 style='color: #2E4053;'>Projet Exploratoire Formation IMT - l'Architecte des Transitions</h2>
        </div>
    """, unsafe_allow_html=True)

# Configuration de la page
st.set_page_config(page_title="Architecte des Transitions", page_icon="🏗️", layout="wide")

# --- CONFIGURATION GEMINI ---
# On tente de récupérer la clé API depuis les secrets Streamlit
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_available = True
except Exception:
    gemini_available = False


st.markdown("---") # Ligne de séparation horizontale
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

st.set_page_config(page_title="Architecte des Transitions", page_icon="⚡", layout="wide")
# --- AJOUTER CE BLOC JUSTE APRÈS set_page_config ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "cadrage" not in st.session_state:
    st.session_state.cadrage = {}

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

tab1, tab2, tab3, tab4 = st.tabs(["📝 1.Aide au Prompt pour SofIA", "📂 2.Extraction & Export", "📝 3.Aide au Prompt Contraintes", "🤖 4. Eval IA"])

# --- ONGLET 1 : AIDE AU PROMPT "SofIA" ---
with tab1: 
    st.header("1.Aide pour formuler le problème initial à SofIA")
    st.info("SofIA va être utilisé pour rédiger la problématique complète en utilisant sa base de connaissance des études et guides sur tous les domaines de la TE. Les champs ci dessous sont à renseigner pour vous aider à rédiger un premier Prompt à fournir à SofIA.")
    
    # Formulaire de questions
    q1 = st.text_area("1. Votre objectif principal (commencer par un verbe) : Réduire / augmenter / modifier ... votre sujet", placeholder="ex: développer la pratique de la marche au quotidien ? augmenter la part des EnR ?")
    q2 = st.text_input("2. Périmètre géographique :", placeholder="ex: dans tous les territoires")
    q3 = st.text_area("3. Cibles visées en priorité :", placeholder="ex: toutes les personnes à tous les âges")
    q4 = st.text_input("4. Objectif chiffré :", placeholder="ex: augmenter de 20% la part de la marche")
    q5 = st.text_area("5. Eventuellement, une action complémentaire proposée à SofIA ?", placeholder="ex: étudier plus particulièrement ...")
    
    if 'prompt_genere' not in st.session_state:
        st.session_state.prompt_genere = False
    
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
        prompt_buffer = io.BytesIO()
        prompt_doc.save(prompt_buffer)
        prompt_buffer.seek(0)
        
        # Organisation dans le document Word
        prompt_doc.add_heading("Votre base de prompt personnalisée à relire et ajuster :", level=1)
        prompt_doc.add_paragraph(phrase_prompt)
        
        prompt_doc.add_heading("Relire et reformuler si besoin avant de copier/coller dans Sofia : https://www.sofia-transition-ecologique.fr/", level=1)
        p = prompt_doc.add_paragraph("Ce document complet est à relire, compléter, ajuster. Puis il sera copié/collé dans Sofia. Se connecter à ")
        # On ajoute le lien cliquable vers Eval
        url_sofia = "https://www.sofia-transition-ecologique.fr/"
        add_hyperlink(p, url_sofia, "SofIA")
          
        
        # Export
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
        # --- À AJOUTER EN BAS DE L'ONGLET 1 ---
if st.session_state.prompt_genere:
        st.markdown("---")
        st.success("✅ Document généré avec succès !")
        st.markdown("### 🚀 Étape suivante")
        st.markdown("Connectez-vous maintenant à [Sofia](https://www.sofia-transition-ecologique.fr/) pour copier/coller votre prompt généré.")

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
    st.info("SofIA a généré une réponse présentant le domaine considéré, le contexte, les problèmes et principaux verrous, les acteurs à rassembler ainsi que des propositions d'actions. Les questions ci-dessous vont permettre de préciser le problème à résoudre et les différentes contraintes.")

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
        prompt_doc.add_heading("Cadrage du Problème & Prompt pour Eval", 0)

        # Création du paragraphe de conclusion avec le lien
        p = prompt_doc.add_paragraph("Ce document complet est à relire, compléter, ajuster. Puis il sera fourni à un Assistant Eval (au format .pdf) pour proposer un mode d'intervention. Se connecter à ")
        # On ajoute le lien cliquable vers Eval
        url_eval = "https://m365.cloud.microsoft/chat/?titleId=T_7b923e69-c9aa-4317-d331-4647b285be26"
        add_hyperlink(p, url_eval, "Eval")
       
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
        
      # --- TAB 4 : ASSISTANT GEMINI (NOUVEAU) ---
# --- TAB 4 : ASSISTANT GEMINI & STRATÉGIE ---
with tab4:
    st.header("🤖 L'Architecte des Transitions (IA)")
    
    if not gemini_available:
        st.warning("⚠️ Pour activer l'IA, veuillez configurer votre clé API Gemini dans les secrets.")
    else:
        st.info("Cet assistant peut analyser l'ensemble de votre dossier (Réponse SofIA + Cadrage) pour proposer une stratégie.")

        # --- BOUTON D'ACTION STRATÉGIQUE ---
        if st.button("🧠 Générer la Stratégie d'Intervention (Fusion des documents)"):
            
            # 1. Vérification des données sources
            if not st.session_state.html_content:
                st.error("❌ Erreur : Aucun fichier SofIA chargé dans l'Onglet 2.")
            else:
                with st.spinner("Fusion des documents et analyse par l'Architecte..."):
                    try:
                        # A. Extraction du texte de la réponse SofIA (HTML -> Texte brut)
                        soup = BeautifulSoup(st.session_state.html_content, 'html.parser')
                        texte_sofia = soup.get_text(separator="\n")

                        # B. Formatage des données de Cadrage (Onglet 3)
                        texte_cadrage = "--- DONNÉES DE CADRAGE ET CONTRAINTES ---\n"
                        if st.session_state.cadrage:
                            for k, v in st.session_state.cadrage.items():
                                texte_cadrage += f"- {k} : {v}\n"
                        else:
                            texte_cadrage += "Aucune contrainte spécifique saisie dans l'onglet 3.\n"

                        # C. Construction du Prompt "Fusion"
                        prompt_strategie = (
                            "Tu es un expert en stratégie de transition écologique (Architecte des Transitions). "
                            "Voici les données complètes du problème (Dossier technique + Contraintes terrain).\n\n"
                            f"{texte_cadrage}\n\n"
                            "--- ANALYSE TECHNIQUE PRÉALABLE (SOFIA) ---\n"
                            f"{texte_sofia}\n\n"
                            "--- CONSIGNE ---\n"
                            "Propose le meilleur mode d'intervention ou une combinaison de modes d'intervention "
                            "pour résoudre le problème présenté dans ces contenus fusionnés. "
                            "Sois structuré, opérationnel et justifie tes choix par rapport aux contraintes du cadrage."
                        )

                        # D. Envoi à Gemini
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt_strategie)

                        # E. Affichage du résultat
                        st.session_state.messages.append({"role": "user", "content": "Génère la stratégie d'intervention basée sur le dossier complet."})
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        st.rerun() # Pour rafraîchir l'affichage du chat immédiatement

                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse : {e}")

        st.divider()

        # --- INTERFACE DE CHAT CLASSIQUE ---
        # Affichage de l'historique
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Zone de saisie pour continuer la discussion sur la stratégie
        if prompt := st.chat_input("Posez une question sur la stratégie proposée..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Contexte glissant (on garde les derniers échanges en mémoire)
            chat_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(chat_context)
                
                with st.chat_message("assistant"):
                    st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Erreur : {e}")
