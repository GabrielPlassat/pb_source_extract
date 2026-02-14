import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.shared import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
import docx
import pypdf

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Architecte des Transitions", page_icon="🏗️", layout="wide")

# --- 2. INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
# On initialise les variables pour qu'elles existent partout dans l'app
if "html_content" not in st.session_state:
    st.session_state.html_content = None

if "prompt_genere" not in st.session_state:
    st.session_state.prompt_genere = False

# Liste des clés pour les champs du formulaire (Onglet 3)
# Cela permet de sauvegarder ce que vous écrivez même si vous changez d'onglet
keys_cadrage = [
    "c_perimetre", "c_type", "c_douleurs", "c_partenaires", 
    "c_benef_t", "c_benef_i", "c_obj_opp", "c_budget",
    "c_planning", "c_com", "c_market", "c_infos"
]
for key in keys_cadrage:
    if key not in st.session_state:
        st.session_state[key] = ""

# --- 3. FONCTIONS UTILITAIRES ---

def add_hyperlink(paragraph, url, text):
    """Insère un hyperlien cliquable dans un paragraphe Word."""
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
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
    """
    Nettoie le HTML de SofIA pour en extraire un texte structuré.
    Transforme les tableaux HTML en texte lisible avec des barres verticales.
    """
    if not html_content:
        return "Aucun contenu technique fourni."

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Supprimer le bruit (scripts, styles, boutons, navigation)
    for element in soup(["script", "style", "header", "footer", "nav", "button", "input", "form"]):
        element.decompose()

    # 2. Convertir les tableaux HTML en format texte structuré (| Col 1 | Col 2 |)
    for table in soup.find_all('table'):
        table_text = "\n"
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['td', 'th'])
            # Nettoyage de chaque cellule
            cols_text = [ele.get_text(separator=" ").strip().replace("\n", " ") for ele in cols]
            # Assemblage de la ligne
            line = "| " + " | ".join(cols_text) + " |"
            table_text += line + "\n"
        table_text += "\n"
        table.replace_with(table_text)

    # 3. Extraction propre du texte
    text = soup.get_text(separator='\n\n')
    
    # 4. Nettoyage des sauts de ligne multiples
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def create_clean_docx(text_content):
    """Crée un vrai fichier .docx à partir du texte nettoyé."""
    doc = Document()
    doc.add_heading('Export Réponse SofIA', 0)
    # On ajoute le texte paragraphe par paragraphe pour éviter les blocs trop massifs
    for paragraph in text_content.split('\n\n'):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 4. HEADER (LOGO + TITRE) ---
col_logo, col_titre = st.columns([1, 5])

with col_logo:
    try:
        st.image("LOGO ARC.jpg", use_container_width=True)
    except:
        st.warning("Logo non trouvé (LOGO ARC.jpg)")

with col_titre:
    st.markdown("""
        <div style='margin-top: 20px;'>
            <h2 style='color: #2E4053;'>Projet Exploratoire Formation IMT - l'Architecte des Transitions</h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- 5. NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 1. Aide au Prompt", "📂 2. Extraction & Export", "📝 3. Cadrage Projet", "🤖 4. Stratégie IA (Fusion)"])

# --- ONGLET 1 : AIDE AU PROMPT ---
with tab1: 
    st.header("1. Aide pour formuler le problème initial à SofIA")
    st.info("Remplissez ce formulaire pour générer un prompt structuré à copier dans SofIA.")
    
    q1 = st.text_area("1. Votre objectif principal (Action + Sujet) :", placeholder="ex: développer la pratique de la marche au quotidien")
    q2 = st.text_input("2. Périmètre géographique :", placeholder="ex: dans tous les territoires ruraux")
    q3 = st.text_area("3. Cibles visées en priorité :", placeholder="ex: les séniors et les scolaires")
    q4 = st.text_input("4. Objectif chiffré :", placeholder="ex: augmenter de 20% la part modale")
    q5 = st.text_area("5. Action complémentaire / Précision :", placeholder="ex: étudier l'impact sur la santé")
    
    if st.button("Générer le document de Prompt (.docx)"):
        prompt_doc = Document()
        prompt_doc.add_heading("Prompt pour SofIA", 0)
        
        try:
            prompt_doc.add_paragraph("Utilisez le prompt ci-dessous dans l'interface SofIA :")
            prompt_doc.add_picture("sofia_q.png", width=Inches(5.5))
        except:
            pass # Si l'image n'est pas là, on continue sans planter
        
        phrase_prompt = (
            f"Comment {q1} dans {q2}, en ciblant plus particulièrement {q3}. "
            f"Un premier objectif serait de {q4}. En complément, il est proposé de {q5}. "
            f"Quelles sont les principales données dans ce domaine, les acteurs à mobiliser, "
            f"les paramètres clés à travailler, les solutions déjà mises en œuvre, les principaux résultats, "
            f"les projets ayant réussi ou échoué. Identifie les verrous systémiques et les effets rebonds possibles."
        )
        
        prompt_doc.add_heading("Votre prompt :", level=1)
        prompt_doc.add_paragraph(phrase_prompt)
        
        p = prompt_doc.add_paragraph("Puis connectez-vous à ")
        add_hyperlink(p, "https://www.sofia-transition-ecologique.fr/", "SofIA")
        
        buf = io.BytesIO()
        prompt_doc.save(buf)
        buf.seek(0)
        
        st.session_state.prompt_buffer = buf
        st.session_state.prompt_genere = True

    if st.session_state.prompt_genere and 'prompt_buffer' in st.session_state:
        st.download_button(
            label="📥 Télécharger votre prompt",
            data=st.session_state.prompt_buffer,
            file_name="Prompt_Initial_Sofia.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        st.markdown("---")
        st.success("✅ Prompt généré !")
        st.markdown("👉 **Étape suivante :** Connectez-vous à [Sofia](https://www.sofia-transition-ecologique.fr/) pour copier ce prompt.")

# --- ONGLET 2 : EXTRACTION ---
with tab2:
    st.header("2. Récupération de l'exportation SofIA")
    st.info("Importez ici le fichier 'chat_history.html' exporté depuis SofIA.")
    
    uploaded_file = st.file_uploader("Glissez votre fichier HTML ci-dessous", type="html")

    if uploaded_file:
        content = uploaded_file.read().decode('utf-8')
        # Sauvegarde en mémoire pour l'onglet 4
        st.session_state.html_content = content
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Convertir en Word")
            # Utilisation de la nouvelle méthode propre
            clean_text = clean_html_advanced(content)
            docx_buffer = create_clean_docx(clean_text)
            
            st.download_button(
                "📥 Télécharger la réponse (.docx)", 
                docx_buffer, 
                "Reponse_Sofia_Clean.docx", 
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        with col2:
            st.subheader("📚 Extraire les Sources PDF")
            if st.button("Préparer le ZIP des sources"):
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
                st.download_button("📥 Télécharger les Sources (.zip)", zip_buffer.getvalue(), "Sources.zip", "application/zip")

# --- ONGLET 3 : CADRAGE ---
with tab3:
    st.header("3. Préciser les Contraintes du Projet")
    st.info("Remplissez ces champs pour cadrer la stratégie. Ces informations seront automatiquement transmises à l'onglet 4.")

    # NOTE IMPORTANTE : L'ajout de key="c_..." permet de sauvegarder les données automatiquement
    q1 = st.text_area("Périmètre précis :", key="c_perimetre")
    
    st.markdown("Nature du problème ([En savoir plus](https://fr.wikipedia.org/wiki/Probl%C3%A8me_vicieux))")
    q2 = st.radio("Type de problème :", ["Compliqué", "Complexe", "Pernicieux (Wicked)"], key="c_type")

    col_a, col_b = st.columns(2)
    with col_a:
        st.text_area("Douleurs perçues :", key="c_douleurs")
        st.text_area("Bénéfices tangibles :", key="c_benef_t")
        st.text_area("Objectifs opposables (chiffrés) :", key="c_obj_opp")
        st.text_area("Planning / Jalons :", key="c_planning")
        st.text_area("Vecteurs marketing :", key="c_market")
    
    with col_b:
        st.text_area("Partenaires obligatoires :", key="c_partenaires")
        st.text_area("Bénéfices intangibles :", key="c_benef_i")
        st.text_area("Budget prévisionnel :", key="c_budget")
        st.text_area("Communication / Visibilité :", key="c_com")
        st.text_area("Informations complémentaires :", key="c_infos")

    # Bouton optionnel si on veut juste le cadrage seul
    if st.button("Générer uniquement le document de Cadrage (.docx)"):
        cad_doc = Document()
        cad_doc.add_heading("Cadrage du Problème", 0)
        
        # On récupère les données via le session_state
        data_cadrage = {k: st.session_state[k] for k in keys_cadrage if st.session_state[k]}
        
        for k, v in data_cadrage.items():
            label = k.replace("c_", "").capitalize()
            cad_doc.add_heading(label, level=1)
            cad_doc.add_paragraph(v)
            
        buf = io.BytesIO()
        cad_doc.save(buf)
        buf.seek(0)
        st.download_button("📥 Télécharger Cadrage Seul", buf, "Cadrage_Projet.docx")

# --- ONGLET 4 : FUSION & STRATÉGIE ---
with tab4:
    st.header("🤖 4. Génération de la Stratégie (Fusion)")
    st.info("Ce module crée un 'Dossier Maître' optimisé pour l'IA, contenant le cadrage (Onglet 3) et l'analyse technique (Onglet 2).")

    # Vérification des données disponibles
    has_sofia = st.session_state.html_content is not None
    # On vérifie s'il y a au moins une contrainte saisie
    has_cadrage = any(st.session_state[k] for k in keys_cadrage if st.session_state[k])

    col_check1, col_check2 = st.columns(2)
    col_check1.metric("Données SofIA (Onglet 2)", "Présent" if has_sofia else "Manquant", delta_color="normal" if has_sofia else "off")
    col_check2.metric("Données Cadrage (Onglet 3)", "Présent" if has_cadrage else "Vide", delta_color="normal" if has_cadrage else "off")

    if st.button("🔄 Fusionner les documents pour le GEM", type="primary"):
        
        fusion_doc = Document()
        
        # 1. PROMPT MASTER (Le Cerveau)
        fusion_doc.add_heading("INSTRUCTIONS POUR L'ASSISTANT IA", 0)
        
        p = fusion_doc.add_paragraph()
        run = p.add_run("RÔLE : ")
        run.bold = True
        run.font.color.rgb = RGBColor(255, 0, 0) # Rouge
        p.add_run("Tu es un expert senior en stratégie de transition écologique.\n")
        
        run = p.add_run("TÂCHE : ")
        run.bold = True
        run.font.color.rgb = RGBColor(255, 0, 0)
        p.add_run("Analyse les contraintes du projet (Partie 1) et l'analyse technique fournie (Partie 2). Propose ensuite une stratégie d'intervention opérationnelle.\n")
        
        run = p.add_run("LIVRABLE : ")
        run.bold = True
        p.add_run("1. Diagnostic synthétique (Verrous/Opportunités)\n2. Mode d'intervention recommandé (justifié)\n3. Feuille de route.")
        
        fusion_doc.add_page_break()

        # 2. CADRAGE (Le Terrain)
        fusion_doc.add_heading("PARTIE 1 : CONTEXTE ET CONTRAINTES", 1)
        fusion_doc.add_paragraph("Voici les paramètres structurants saisis par le porteur de projet :")
        
        # Récupération dynamique des champs remplis
        donnees_cadrage = {k: st.session_state[k] for k in keys_cadrage if st.session_state[k]}
        
        if donnees_cadrage:
            for k, v in donnees_cadrage.items():
                # On rend le nom de la clé plus joli (c_budget -> Budget)
                label_joli = k.replace("c_", "").replace("_", " ").capitalize()
                p = fusion_doc.add_paragraph(style='List Bullet')
                p.add_run(f"{label_joli} : ").bold = True
                p.add_run(str(v))
        else:
            fusion_doc.add_paragraph("⚠️ Aucune contrainte spécifique renseignée dans l'onglet 3.")

        fusion_doc.add_paragraph("\n")

        # 3. ANALYSE SOFIA (La Matière)
        fusion_doc.add_heading("PARTIE 2 : ANALYSE TECHNIQUE (SOURCE SOFIA)", 1)
        
        if st.session_state.html_content:
            # Nettoyage avancé
            clean_text = clean_html_advanced(st.session_state.html_content)
            fusion_doc.add_paragraph(clean_text)
        else:
            fusion_doc.add_paragraph("⚠️ Aucune donnée SofIA fournie (fichier HTML manquant).")

        # Sauvegarde
        buffer = io.BytesIO()
        fusion_doc.save(buffer)
        buffer.seek(0)
        st.session_state.fusion_buffer = buffer
        
        st.success("✅ Dossier stratégique généré avec succès !")

    # Affichage du bouton de téléchargement si le buffer existe
    if 'fusion_buffer' in st.session_state:
        st.markdown("---")
        col_dl, col_gem = st.columns(2)
        
        with col_dl:
            st.download_button(
                label="📥 1. Télécharger le Dossier Complet (.docx)",
                data=st.session_state.fusion_buffer,
                file_name="Dossier_Strategie_IA.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        
        with col_gem:
            # Lien vers Gemini (ou autre IA)
            url_gem = "https://gemini.google.com/app"
            st.link_button("🧠 2. Ouvrir l'Assistant IA (Gemini)", url_gem)
            st.caption("Une fois sur Gemini, glissez-y le fichier téléchargé.")
