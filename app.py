import streamlit as st
import requests
from bs4 import BeautifulSoup
import io
import zipfile
import re

st.set_page_config(page_title="Sofia Export : Tableaux & Sources", page_icon="📊")

def markdown_to_html_table(text):
    """
    Détecte les tableaux de type Markdown (avec des |) dans le texte 
    et les convertit en tableaux HTML propres pour Word.
    """
    lines = text.strip().split('\n')
    html_table = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    
    for i, line in enumerate(lines):
        if '|---' in line: # On ignore la ligne de séparation Markdown
            continue
        
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if not cells:
            continue
            
        tag = 'th' if i == 0 else 'td' # La première ligne devient l'en-tête
        html_table += '<tr>'
        for cell in cells:
            # Remplacement des retours à la ligne internes par des balises <br>
            cell_content = cell.replace('- ', '<br>- ')
            html_table += f'<{tag} style="padding: 8px; vertical-align: top;">{cell_content}</{tag}>'
        html_table += '</tr>'
    
    html_table += '</table>'
    return html_table

def convert_html_to_doc_format(html_content):
    """Encapsule le contenu pour Word en traitant les tableaux texte."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Étape cruciale : Trouver les textes qui ressemblent à des tableaux Markdown
    # et les remplacer par du vrai HTML avant l'export
    for element in soup.find_all(string=re.compile(r"\|.*\|")):
        parent = element.parent
        if parent.name not in ['script', 'style']:
            # Détection d'un bloc de tableau complet
            potential_table = element.string
            if '|' in potential_table and '---' in potential_table:
                new_table_html = markdown_to_html_table(potential_table)
                # On remplace le texte par le nouveau tableau HTML
                element.replace_with(BeautifulSoup(new_table_html, 'html.parser'))

    html_header = (
        '<html xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:w="urn:schemas-microsoft-com:office:word" '
        'xmlns="http://www.w3.org/TR/REC-html40">'
        '<head><meta charset="utf-8"><style>'
        'table { border: 1px solid #000; border-collapse: collapse; }'
        'th, td { border: 1px solid #000; padding: 5px; }'
        '</style></head><body>'
    )
    full_html = html_header + str(soup) + '</body></html>'
    return io.BytesIO(full_html.encode('utf-8'))

st.title("⚡ Sofia Export : Tableaux & Sources")
st.write("Cet outil convertit vos tableaux Markdown en tableaux Word réels.")

uploaded_file = st.file_uploader("Glissez votre fichier chat_history.html", type="html")

if uploaded_file:
    content = uploaded_file.read().decode('utf-8')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Export Document")
        doc_file = convert_html_to_doc_format(content)
        st.download_button(
            label="📥 Télécharger le .doc",
            data=doc_file,
            file_name="Historique_Sofia_Tableaux.doc",
            mime="application/msword"
        )
        st.caption("Les tableaux avec des '|' seront convertis en grilles Word.")

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
            st.download_button(label="📥 Télécharger le .zip", data=zip_buffer.getvalue(), file_name="Sources.zip", mime="application/zip")
