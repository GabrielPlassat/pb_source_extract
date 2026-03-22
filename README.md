# 🏗️ Architecte des Transitions (ART) - Projet Exploratoire IMT

L'**ARchitecte des Transitions (ART)** est un outil d'accompagnement conçu pour augmenter les capacités d'action des experts et managers de l'ADEME. Il aide à concevoir des modes d'intervention robustes face à l'incertitude systémique (technique, financière, sociale).

Cette application Streamlit orchestre un flux de travail utilisant plusieurs agents IA spécialisés et s'appuie sur une base de plus de 100 évaluations de programmes historiques.

---

## 🚀 Flux de travail et Onglets

L'application est structurée de manière chronologique :

### 📝 0. Présentation du projet
Introduction aux concepts de l'incertitude systémique et présentation de la vision du projet ART.

### 📝 1. Aide au Prompt pour SofIA
- **IA Reformulation** : Utilise l'API Google Gemini (modèle `gemini-1.5-flash`) pour transformer vos notes brutes en une question de recherche institutionnelle fluide.
- **Génération Word** : Produit un document `.docx` prêt à être copié dans l'outil SofIA de l'ADEME.

### 📂 2. Extraction & Export
- **Traitement HTML** : Importez le fichier `chat_history.html` de SofIA.
- **Synthèse** : Convertit la réponse en document éditable.
- **Collecte de sources** : Télécharge automatiquement tous les PDF cités par SofIA dans une archive ZIP unique.

### 📝 3. Aide au Prompt Contraintes
- **Cadrage structuré** : Formulaire complet pour définir le périmètre, la nature du problème (Compliqué, Complexe, Pernicieux), les bénéfices attendus (tangibles/intangibles) et les contraintes budgétaires/planning.

### 🤖 4. Agent EVAL
- **Analyse de fichiers** : Fusionne l'analyse de SofIA et votre cadrage de contraintes dans un document unique optimisé pour l'IA.
- **Intervention** : Propose des modes d'intervention basés sur les retours d'expérience historiques de l'ADEME via un agent Gemini dédié.

### 🤖 5. Agent CHAOS
- **Stress-Test** : Analyse la robustesse du programme proposé par l'Agent EVAL en simulant des événements probables à fort impact pour identifier les angles morts.

### 📝 6. Questionnaire
- **Feedback** : Intégration d'un formulaire Airtable pour évaluer la pertinence des réponses fournies par les différents agents.

---

## 🛠️ Installation et Configuration

### 1. Cloner et installer
```bash
git clone <url-du-depot>
pip install -r requirements.txt
