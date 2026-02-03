import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile

# Configuration de la page
st.set_page_config(page_title="Sofia Export Pro", page_icon="📝")

def convert_html_to_doc_format(html_content):
    """
    Encapsule le HTML dans un format interprétable directement par Word 
    pour conserver tableaux, styles et mise en forme.
    """
    # On ajoute des balises spécifiques pour que Word reconnaisse l'encodage
    html_header = (
        '<html xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:w="urn:schemas-microsoft-com:office:word" '
        'xmlns="http://www.w3.org/TR/REC-html40">'
        '<head><meta charset="utf-8"></head><body>'
    )
    html_footer = '</body></html>'
    
    # On nettoie éventuellement le HTML pour supprimer les éléments interactifs (boutons)
    soup = BeautifulSoup(html_content, 'html.parser')
    for btn in soup.find_all('button'):
        btn.decompose()
        
    full_html = html_header + str(soup) + html_footer
    return io.BytesIO(full_html.encode('utf-8'))

st.title("⚡ Sofia Export : Word & Sources")
st.write("Générez un document propre et téléchargez vos sources PDF.")

uploaded_file = st.file_uploader("Glissez votre fichier chat_history.html", type="html")

if uploaded_file:
    content = uploaded_file.read()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Export Document")
        # Conversion directe en format interprétable par Word
        doc_file = convert_html_to_doc_format(content)
        
        st.download_button(
            label="📥 Télécharger l'historique (.doc)",
            data=doc_file,
            file_name="Historique_Sofia_Complet.doc",
            mime="application/msword"
        )
        st.caption("Conserve fidèlement la structure et les tableaux.")

    with col2:
        st.subheader("📚 Sources PDF")
        if st.button("Préparer le ZIP"):
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
