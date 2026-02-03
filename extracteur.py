import os
import requests
import shutil
import tkinter as tk
from tkinter import filedialog
from bs4 import BeautifulSoup

def extraire_sources():
    # Création d'une fenêtre invisible pour sélectionner le fichier
    root = tk.Tk()
    root.withdraw()
    
    print("📂 Sélectionnez votre fichier historique .html...")
    chemin_html = filedialog.askopenfilename(filetypes=[("Fichiers HTML", "*.html")])
    
    if not chemin_html:
        print("❌ Aucun fichier sélectionné.")
        return

    dossier_temp = "sources_telechargees"
    os.makedirs(dossier_temp, exist_ok=True)

    # Lecture et analyse
    with open(chemin_html, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    sources = soup.find_all('div', class_='source-card')
    print(f"🔍 {len(sources)} sources détectées. Téléchargement en cours...")

    for i, source in enumerate(sources):
        link_tag = source.find('h2', class_='card-title').find('a')
        if link_tag and link_tag.get('href'):
            url = link_tag['href']
            # Nettoyage du nom de fichier
            titre = "".join([c for c in link_tag.get_text() if c.isalnum() or c in (' ', '_')]).strip()
            nom_fichier = f"source_{i+1}_{titre[:50]}.pdf".replace(' ', '_')
            
            try:
                resp = requests.get(url, timeout=20)
                with open(os.path.join(dossier_temp, nom_fichier), 'wb') as f_pdf:
                    f_pdf.write(resp.content)
                print(f"✅ OK : {nom_fichier}")
            except:
                print(f"❌ Échec : {url}")

    # Création du ZIP
    nom_zip = "archive_sources"
    shutil.make_archive(nom_zip, 'zip', dossier_temp)
    print(f"\n📦 Terminé ! Votre fichier '{nom_zip}.zip' est prêt.")

    # Nettoyage du dossier temporaire (garde uniquement le ZIP)
    shutil.rmtree(dossier_temp)

if __name__ == "__main__":
    extraire_sources()
