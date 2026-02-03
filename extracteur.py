import os
import requests
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup

def extraire_sources():
    # Fenêtre pour choisir le fichier
    root = tk.Tk()
    root.withdraw()
    
    print("Sélection du fichier historique...")
    chemin_html = filedialog.askopenfilename(
        title="Sélectionnez votre historique HTML",
        filetypes=[("Fichiers HTML", "*.html")]
    )
    
    if not chemin_html:
        return

    dossier_temp = "sources_extraites_temp"
    os.makedirs(dossier_temp, exist_ok=True)

    with open(chemin_html, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Extraction basée sur la structure Sofia
    sources = soup.find_all('div', class_='source-card')
    
    for i, source in enumerate(sources):
        link_tag = source.find('h2', class_='card-title').find('a')
        if link_tag and link_tag.get('href'):
            url = link_tag['href']
            # Nettoyage du titre pour le nom de fichier
            titre = "".join([c for c in link_tag.get_text() if c.isalnum() or c in (' ', '_')]).strip()
            nom_fichier = f"{i+1}_{titre[:50]}.pdf".replace(' ', '_')
            
            try:
                resp = requests.get(url, timeout=20)
                with open(os.path.join(dossier_temp, nom_fichier), 'wb') as f_pdf:
                    f_pdf.write(resp.content)
            except:
                continue

    # Archivage final
    nom_zip = "Archive_Sources_Energie"
    shutil.make_archive(nom_zip, 'zip', dossier_temp)
    shutil.rmtree(dossier_temp)
    
    messagebox.showinfo("Succès", f"Terminé ! L'archive {nom_zip}.zip a été créée.")

if __name__ == "__main__":
    extraire_sources()
