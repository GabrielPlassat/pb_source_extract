import os
import requests
import shutil
import glob
from bs4 import BeautifulSoup
from google.colab import files

def traiter_historique_et_exporter():
    """
    Fonction interactive pour Colab :
    1. Demande l'upload d'un ou plusieurs fichiers .html
    2. Extrait et télécharge les sources PDF
    3. Compresse les résultats en ZIP
    4. Nettoie les dossiers temporaires
    """
    
    # --- 1. IMPORT DU FICHIER ---
    print("📂 ÉTAPE 1 : Veuillez sélectionner votre fichier .html (historique)")
    uploaded = files.upload()
    
    if not uploaded:
        print("❌ Aucun fichier sélectionné. Arrêt du processus.")
        return

    dossier_temp = "temp_sources"
    os.makedirs(dossier_temp, exist_ok=True)
    
    # --- 2. EXTRACTION ET TÉLÉCHARGEMENT ---
    print("\n🔍 ÉTAPE 2 : Analyse des fichiers et téléchargement des sources...")
    
    fichiers_html = [f for f in uploaded.keys() if f.endswith('.html')]
    
    for html_file in fichiers_html:
        print(f"--- Analyse de : {html_file} ---")
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Recherche des sources (basé sur la structure du document fourni)
        sources = soup.find_all('div', class_='source-card')
        
        for i, source in enumerate(sources):
            link_tag = source.find('h2', class_='card-title').find('a') if source.find('h2', class_='card-title') else None
            
            if link_tag and link_tag.get('href'):
                url = link_tag['href']
                # Nettoyage du titre pour le nom de fichier
                titre = "".join([c for c in link_tag.get_text() if c.isalnum() or c in (' ', '_')]).strip()
                titre = titre.replace(' ', '_')[:60]
                nom_fichier = f"source_{i+1}_{titre}.pdf"
                
                try:
                    resp = requests.get(url, timeout=15)
                    resp.raise_for_status()
                    with open(os.path.join(dossier_temp, nom_fichier), 'wb') as f_pdf:
                        f_pdf.write(resp.content)
                    print(f"✅ Récupéré : {nom_fichier}")
                except Exception as e:
                    print(f"⚠️ Erreur sur {url} : {e}")

    # --- 3. CRÉATION DU ZIP ET TÉLÉCHARGEMENT ---
    if os.listdir(dossier_temp):
        print("\n📦 ÉTAPE 3 : Création de l'archive ZIP...")
        nom_zip = "sources_extraites"
        shutil.make_archive(nom_zip, 'zip', dossier_temp)
        
        print(f"📥 Envoi du fichier {nom_zip}.zip vers votre ordinateur...")
        files.download(f"{nom_zip}.zip")
    else:
        print("\nℹ️ Aucune source n'a été trouvée ou téléchargée.")

    # --- 4. NETTOYAGE AUTOMATIQUE ---
    print("\n🧹 ÉTAPE 4 : Nettoyage de l'espace de travail...")
    
    # Suppression du dossier temporaire
    shutil.rmtree(dossier_temp)
    
    # Suppression des fichiers HTML uploadés pour ne pas encombrer Colab
    for f in fichiers_html:
        if os.path.exists(f):
            os.remove(f)
            
    print("✨ Terminé ! L'environnement est propre.")

# Lancement de l'outil
if __name__ == "__main__":
    traiter_historique_et_exporter()
