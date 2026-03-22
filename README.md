# 🏗️ Architecte des Transitions - Projet Exploratoire IMT

Cette application Streamlit est un outil d'accompagnement conçu pour aider à la formulation de problématiques complexes liées à la **Transition Écologique (TE)**. Elle facilite l'interaction avec l'IA **SofIA** et structure le cadrage des interventions de l'**ADEME**.

---

## 🚀 Fonctionnalités

L'application est divisée en 4 modules clés :

1. **📝 1. Aide au Prompt pour SofIA**
   - Génère un document `.docx` contenant un prompt structuré et optimisé.
   - Intègre des questions spécifiques pour guider l'utilisateur dans la définition de ses objectifs et cibles.

2. **📂 2. Extraction & Export**
   - Importez l'historique de conversation SofIA (`chat_history.html`).
   - Convertit la réponse en un document Word propre (`.doc`).
   - Extrait automatiquement les sources PDF citées et les regroupe dans un fichier `.zip`.

3. **📝 3. Aide au Prompt Contraintes**
   - Formulaire guidé pour définir la nature du problème (Compliqué, Complexe ou Pernicieux).
   - Précise les contraintes de projet : budget, planning, partenaires et objectifs opposables.
   - Génère un document de cadrage complet.

4. **🤖 4. Eval IA (Génération de Stratégie)**
   - Module de fusion pour préparer la stratégie finale avec l'assistant Eval.

---

## 🛠️ Installation et Lancement

### 1. Prérequis
Assurez-vous d'avoir Python installé (version 3.8 ou supérieure).

### 2. Cloner le projet
```bash
git clone <url-du-depot>
cd <nom-du-dossier>
