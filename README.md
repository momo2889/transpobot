# TranspoBot - Application de Gestion de Transport

Application web moderne pour la gestion de transport avec intelligence artificielle intégrée.

## 🚀 Déploiement sur Railway

### 1. Prérequis
- Compte GitHub
- Compte Railway
- Base de données MySQL sur Railway

### 2. Configuration Railway

#### a) Créer un projet
1. Aller sur [Railway.app](https://railway.app)
2. Créer un nouveau projet
3. Connecter votre repository GitHub

#### b) Ajouter une base de données MySQL
1. Dans votre projet Railway, cliquer sur "Add Plugin"
2. Sélectionner "MySQL"
3. La base de données sera automatiquement configurée avec les variables d'environnement

#### c) Variables d'environnement
Railway définit automatiquement ces variables :
- `DATABASE_URL` - URL complète de connexion MySQL
- `PORT` - Port du serveur (automatique)

Ajoutez manuellement :
- `GROQ_API_KEY` - Votre clé API Groq (nécessaire pour l'IA)

### 3. Initialisation de la base de données

Après le déploiement, initialisez la base de données :

#### Option 1: Via Railway CLI
```bash
# Installer Railway CLI
npm install -g @railway/cli

# Se connecter
railway login

# Aller dans le projet
railway link

# Exécuter l'initialisation
railway run python init_db.py
```

#### Option 2: Via l'interface Railway
1. Aller dans votre projet Railway
2. Ouvrir le terminal dans l'onglet "Variables & Secrets"
3. Exécuter : `python init_db.py`

### 4. Vérification du déploiement

Une fois déployé, votre application sera accessible à l'URL fournie par Railway.

### 5. Pages disponibles

- **Dashboard** : `https://votre-app.railway.app/`
- **Connexion** : `https://votre-app.railway.app/login`
- **Stations** : `https://votre-app.railway.app/stations`
- **Maintenance** : `https://votre-app.railway.app/maintenance`
- **Ajouter Données** : `https://votre-app.railway.app/add-data`

## 🔧 Développement local

```bash
# Cloner le repository
git clone https://github.com/votre-username/transpobot.git
cd transpobot

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement (.env)
cp .env.example .env
# Éditer .env avec vos valeurs locales

# Initialiser la base de données
python init_db.py

# Lancer l'application
python main.py
```

## 📋 Structure du projet

```
transpobot/
├── main.py              # Application FastAPI principale
├── database.py          # Configuration base de données
├── chat.py              # Logique IA avec Groq
├── init_db.py           # Script d'initialisation DB
├── requirements.txt     # Dépendances Python
├── Procfile            # Configuration Railway
├── schema.sql          # Schéma base de données
├── templates/          # Templates HTML
│   ├── dashboard.html
│   ├── login.html
│   ├── stations.html
│   ├── maintenance.html
│   └── add-data.html
└── static/             # Fichiers statiques
```

## 🛠️ Technologies utilisées

- **Backend** : FastAPI, Python
- **Base de données** : MySQL
- **IA** : Groq API
- **Frontend** : HTML5, CSS3, JavaScript
- **Déploiement** : Railway
- **Icons** : Lucide

## 📞 Support

En cas de problème avec le déploiement :
1. Vérifier les logs Railway
2. S'assurer que DATABASE_URL est définie
3. Vérifier que GROQ_API_KEY est configurée
4. Tester l'initialisation de la base de données