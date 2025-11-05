# Guide de Test - KeePassXC Web Manager v2.0

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :
- ✅ Python 3.12+ ou 3.13
- ✅ Poetry 2.2+
- ✅ Node.js 16+ (pour Tailwind CSS)
- ✅ KeePassXC CLI 2.7+
- ✅ Docker (pour Redis, optionnel)
- ✅ Navigateur moderne (Chrome, Firefox, Safari, Edge)

---

## 🚀 Procédure de Test Complète

### Étape 1 : Vérification des Prérequis

```bash
# Vérifier Python
python3 --version
# Doit afficher : Python 3.12.x ou 3.13.x

# Vérifier Poetry
poetry --version
# Doit afficher : Poetry (version 2.2.x)

# Vérifier Node.js
node --version
# Doit afficher : v16.x.x ou supérieur

# Vérifier KeePassXC CLI
keepassxc-cli --version
# Doit afficher : 2.7.x

# Vérifier Docker (optionnel)
docker --version
# Doit afficher : Docker version xx.x.x
```

---

### Étape 2 : Installation des Dépendances

#### Backend (Python)

```bash
cd /home/user/keepassxc-web-manager/backend

# Installer les dépendances Python
poetry install

# Vérifier l'installation
poetry run python -c "import fastapi; import uvicorn; print('✓ Dependencies OK')"
```

#### Frontend (Node.js)

```bash
cd /home/user/keepassxc-web-manager/frontend

# Installer les dépendances Node.js
npm install

# Vérifier l'installation
npm list tailwindcss
# Doit afficher : tailwindcss@3.x.x
```

---

### Étape 3 : Build Tailwind CSS

```bash
cd /home/user/keepassxc-web-manager/frontend

# Build CSS (production)
npm run build:css

# Vérifier que le fichier a été créé
ls -lh public/css/tailwind.min.css
# Doit afficher un fichier .css

# Pour le développement (watch mode, optionnel)
# npm run watch:css
```

---

### Étape 4 : Créer une Base de Test KeePassXC

**Option A : Base de Test Simple (Recommandé)**

```bash
# Créer un répertoire pour les bases de test
mkdir -p ~/test-databases
cd ~/test-databases

# Créer une base KeePassXC de test
# Note : keepassxc-cli ne supporte pas la création directe
# Vous devez créer la base avec KeePassXC GUI ou utiliser une base existante

# Si vous avez KeePassXC GUI :
# 1. Ouvrir KeePassXC
# 2. Fichier > Nouvelle base de données
# 3. Nom : test-database.kdbx
# 4. Emplacement : ~/test-databases/
# 5. Mot de passe : test_master_password
# 6. Créer quelques entrées de test :
#    - Work/GitHub (user: test@example.com, pass: test123)
#    - Personal/Email (user: email@example.com, pass: email123)
```

**Option B : Base Vide (CLI)**

Si vous ne pouvez pas créer de base avec GUI, créez un fichier minimal :

```bash
# Créer répertoire
mkdir -p ~/test-databases

# Note : Pour une vraie base, utilisez KeePassXC GUI
echo "⚠️  Vous devez créer une base .kdbx avec KeePassXC GUI"
echo "📍 Emplacement : ~/test-databases/test-database.kdbx"
echo "🔑 Mot de passe suggéré : test_master_password"
```

---

### Étape 5 : Configuration Environnement

```bash
cd /home/user/keepassxc-web-manager/backend

# Copier le fichier .env.example
cp .env.example .env

# Éditer .env (optionnel, les valeurs par défaut fonctionnent)
# Vérifier ces paramètres :
cat .env | grep -E "(SECRET_KEY|SESSION_TIMEOUT|CACHE_BACKEND)"

# Devrait afficher :
# SECRET_KEY="your-super-secret-key-change-me-in-production-min-32-chars"
# SESSION_TIMEOUT=1800
# CACHE_BACKEND="memory"  # Pas besoin de Redis pour tester
```

---

### Étape 6 : Lancer Redis (Optionnel)

**Si vous voulez tester avec Redis :**

```bash
cd /home/user/keepassxc-web-manager

# Lancer Redis avec Docker Compose
docker compose up -d redis

# Vérifier que Redis fonctionne
docker compose ps
# Doit afficher : redis ... Up

# Tester Redis
docker exec -it keepassxc-web-manager-redis-1 redis-cli ping
# Doit afficher : PONG

# Dans .env, vérifier :
# CACHE_BACKEND="redis"
```

**Si vous n'utilisez pas Redis :**

```bash
# Dans .env, s'assurer que :
# CACHE_BACKEND="memory"
# (le cache mémoire sera utilisé automatiquement)
```

---

### Étape 7 : Lancer le Backend

```bash
cd /home/user/keepassxc-web-manager/backend

# Option A : Lancer avec le script start.sh
chmod +x ../scripts/start.sh
../scripts/start.sh

# Option B : Lancer directement avec Poetry
poetry run python -m app.main

# Option C : Lancer avec Uvicorn (recommandé pour dev)
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Vous devriez voir :
# ================================================================================
# KeePassXC Web Manager v2.0.0-alpha
# ================================================================================
# Environment: development
# Debug mode: False
# KeePassXC CLI: keepassxc-cli
# Cache backend: memory
# API docs: True
# ================================================================================
# ✓ KeePassXC CLI available: version 2.7.10
# Application started successfully
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Étape 8 : Vérifier que le Backend Fonctionne

**Dans un AUTRE terminal :**

```bash
# Test 1 : Health check
curl http://localhost:8000/health

# Doit retourner :
# {
#   "status": "healthy",
#   "version": "2.0.0-alpha",
#   "keepassxc_available": true,
#   "cache_healthy": true,
#   "timestamp": "..."
# }

# Test 2 : Ping
curl http://localhost:8000/ping

# Doit retourner :
# {"ping":"pong"}

# Test 3 : API docs (dans navigateur)
# Ouvrir : http://localhost:8000/docs
# Doit afficher Swagger UI
```

---

### Étape 9 : Tester l'Interface Web

#### 9.1 Ouvrir l'Application

```bash
# Ouvrir dans le navigateur
xdg-open http://localhost:8000/
# ou
firefox http://localhost:8000/
# ou
google-chrome http://localhost:8000/
```

#### 9.2 Test Login

1. **Page de Login** devrait s'afficher
   - ✅ Fond gradient bleu/indigo
   - ✅ Logo 🔐
   - ✅ Champs : Database Path, Password, Keyfile

2. **Entrer les credentials** :
   ```
   Database Path : /home/user/test-databases/test-database.kdbx
   Password      : test_master_password
   Keyfile       : (laisser vide si pas de keyfile)
   ```

3. **Cliquer "Unlock Database"**
   - ✅ Bouton affiche "Connecting..."
   - ✅ Spinner de chargement
   - ✅ Toast vert "Login successful!"
   - ✅ Redirection vers Dashboard

#### 9.3 Test Dashboard

**Navigation Bar** :
- ✅ Logo + "KeePassXC Web Manager"
- ✅ Nom de la database (test-database.kdbx)
- ✅ Nombre d'entrées
- ✅ Bouton Logout (rouge)

**Sidebar** (gauche, si écran large) :
- ✅ "All Entries" (sélectionné)
- ✅ Liste des groups avec compteurs
- ✅ Icône dossier pour chaque group

**Zone Principale** :
- ✅ Barre de recherche
- ✅ Bouton "New Entry" (bleu)
- ✅ Grille de cards avec entrées

#### 9.4 Test Recherche

1. **Taper dans la barre de recherche** : "github"
   - ✅ Filtrage temps réel
   - ✅ Seules les entrées correspondantes s'affichent
   - ✅ Compteur mis à jour

2. **Effacer la recherche**
   - ✅ Toutes les entrées réapparaissent

#### 9.5 Test Filtre par Group

1. **Cliquer sur un group** dans la sidebar (ex: "Work")
   - ✅ Group surligné en bleu
   - ✅ Seules les entrées du group s'affichent
   - ✅ Compteur mis à jour

2. **Cliquer "All Entries"**
   - ✅ Toutes les entrées réapparaissent

#### 9.6 Test Détails Entrée

1. **Cliquer sur le menu (⋮)** d'une entrée
   - ✅ Menu dropdown s'affiche
   - ✅ Options : View Details, Edit, Delete

2. **Cliquer "View Details"**
   - ✅ Modal s'ouvre
   - ✅ Affiche : Title, Username, Password, URL, Notes
   - ✅ Password caché (••••••••)

3. **Cliquer bouton "Show"** (password)
   - ✅ Bouton affiche "..." pendant chargement
   - ✅ Password s'affiche en clair
   - ✅ Icône œil permet show/hide

4. **Cliquer bouton "Copy"** (username)
   - ✅ Toast vert "Copied to clipboard!"
   - ✅ Username copié dans le presse-papier

5. **Cliquer bouton "Copy"** (password)
   - ✅ Toast vert "Copied to clipboard!"
   - ✅ Password copié dans le presse-papier

6. **Cliquer "Close"**
   - ✅ Modal se ferme
   - ✅ Password effacé de la mémoire

#### 9.7 Test Suppression Entrée

**⚠️ ATTENTION : Ceci supprime réellement l'entrée !**

1. **Cliquer sur le menu (⋮)** d'une entrée de test
2. **Cliquer "Delete"**
   - ✅ Dialog confirmation "Are you sure...?"
3. **Cliquer "OK"**
   - ✅ Entrée supprimée
   - ✅ Toast vert "Entry deleted successfully"
   - ✅ Liste mise à jour
   - ✅ Compteur mis à jour

#### 9.8 Test Logout

1. **Cliquer bouton "Logout"** (rouge, en haut à droite)
   - ✅ Dialog confirmation "Are you sure...?"
2. **Cliquer "OK"**
   - ✅ Redirection vers page login
   - ✅ Token effacé

---

### Étape 10 : Test API Directement (Optionnel)

**Test avec curl :**

```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "database_path": "/home/user/test-databases/test-database.kdbx",
    "password": "test_master_password"
  }'

# Sauvegarder le token retourné
TOKEN="eyJ0eXAiOiJKV1..."  # Copier le token de la réponse

# 2. Lister les entrées
curl http://localhost:8000/api/v1/entries \
  -H "Authorization: Bearer $TOKEN"

# 3. Obtenir les détails d'une entrée (PAS de password)
curl http://localhost:8000/api/v1/entries/Work/GitHub \
  -H "Authorization: Bearer $TOKEN"

# 4. Obtenir le password d'une entrée (EXPLICIT)
curl http://localhost:8000/api/v1/entries/Work/GitHub/password \
  -H "Authorization: Bearer $TOKEN"

# 5. Lister les groups
curl http://localhost:8000/api/v1/groups \
  -H "Authorization: Bearer $TOKEN"

# 6. Database info
curl http://localhost:8000/api/v1/databases/info \
  -H "Authorization: Bearer $TOKEN"

# 7. Logout
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

### Étape 11 : Test des Fonctionnalités Avancées

#### Test Dark Mode

1. **Activer le dark mode** dans les paramètres de votre OS
2. **Rafraîchir la page**
   - ✅ Interface passe en mode sombre
   - ✅ Fond gris foncé
   - ✅ Texte blanc/gris clair

#### Test Responsive

1. **Ouvrir DevTools** (F12)
2. **Activer mode responsive** (Ctrl+Shift+M)
3. **Tester différentes tailles** :
   - Mobile (320px) : 1 colonne, pas de sidebar
   - Tablet (768px) : 2 colonnes, sidebar caché
   - Desktop (1280px) : 3 colonnes, sidebar visible

#### Test Copy to Clipboard

1. **Ouvrir une entrée**
2. **Cliquer "Copy"** sur username
3. **Coller** (Ctrl+V) dans un éditeur de texte
   - ✅ Username collé correctement

---

## 🐛 Problèmes Courants

### Problème 1 : "keepassxc-cli not available"

**Solution :**
```bash
# Debian/Ubuntu
sudo apt install keepassxc-cli

# Vérifier
keepassxc-cli --version
```

### Problème 2 : "Port 8000 already in use"

**Solution :**
```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 <PID>

# Ou utiliser un autre port
poetry run uvicorn app.main:app --port 8001
```

### Problème 3 : "Module not found"

**Solution :**
```bash
# Réinstaller les dépendances
cd backend
poetry install --no-cache

# Vérifier
poetry run python -c "import app.main"
```

### Problème 4 : CSS non stylisé

**Solution :**
```bash
# Rebuild CSS
cd frontend
npm run build:css

# Vérifier que le fichier existe
ls -lh public/css/tailwind.min.css
```

### Problème 5 : "Invalid password or authentication failed"

**Solutions :**
- ✅ Vérifier le chemin de la database (.kdbx)
- ✅ Vérifier le mot de passe (sensible à la casse)
- ✅ Vérifier que la database n'est pas ouverte dans KeePassXC GUI
- ✅ Essayer de déverrouiller avec `keepassxc-cli` en ligne de commande

### Problème 6 : CORS errors dans la console

**Solution :**
```bash
# Vérifier que vous accédez via localhost:8000
# PAS via file:// ou 127.0.0.1

# Dans .env, vérifier :
CORS_ORIGINS=["http://localhost:8000", "http://localhost:3000"]
```

---

## ✅ Checklist de Test Complète

### Backend
- [ ] Health check répond (curl /health)
- [ ] API docs accessibles (/docs)
- [ ] Login fonctionne (POST /auth/login)
- [ ] List entries fonctionne (GET /entries)
- [ ] Password endpoint fonctionne (GET /entries/{name}/password)
- [ ] Logout fonctionne (POST /auth/logout)

### Frontend - Login
- [ ] Page login s'affiche correctement
- [ ] Champs database path, password visibles
- [ ] Toggle show/hide password fonctionne
- [ ] Keyfile optionnel peut être affiché
- [ ] Erreur affichée si credentials invalides
- [ ] Loading spinner pendant auth
- [ ] Redirect vers dashboard après login

### Frontend - Dashboard
- [ ] Navigation bar affiche infos correctes
- [ ] Sidebar groups visible (desktop)
- [ ] Liste entrées s'affiche
- [ ] Compteur entrées correct
- [ ] Cards affichent title, username, URL, tags
- [ ] Password length et group dans footer

### Frontend - Recherche & Filtres
- [ ] Recherche filtre en temps réel
- [ ] Filtre par group fonctionne
- [ ] Combinaison search + group fonctionne
- [ ] Message "No entries found" si vide

### Frontend - Détails Entrée
- [ ] Modal s'ouvre au clic
- [ ] Username affiché
- [ ] Password caché par défaut
- [ ] Bouton "Show" charge password
- [ ] Toggle show/hide password fonctionne
- [ ] URL cliquable (ouvre nouvel onglet)
- [ ] Notes affichées
- [ ] Bouton "Copy" fonctionne

### Frontend - Actions
- [ ] Copy username fonctionne
- [ ] Copy password fonctionne
- [ ] Toast notifications s'affichent
- [ ] Delete avec confirmation fonctionne
- [ ] Logout avec confirmation fonctionne

### Frontend - UX
- [ ] Transitions smooth
- [ ] Loading spinners pendant chargement
- [ ] Messages d'erreur clairs
- [ ] Responsive mobile/tablet/desktop
- [ ] Dark mode fonctionne (si activé)

---

## 🎉 Résultat Attendu

Après ces tests, vous devriez avoir :

✅ **Backend fonctionnel**
- API REST complète
- KeePassXC CLI intégré
- Authentication JWT
- Cache fonctionnel

✅ **Frontend fonctionnel**
- Login/Logout
- Liste entrées avec recherche/filtres
- Affichage sécurisé passwords
- Copy to clipboard
- Notifications toast

✅ **Sécurité validée**
- Passwords jamais dans listes
- Chargement on-demand
- JWT authentication
- CORS configuré

---

## 📝 Rapport de Test

**Date** : _______________

**Environnement** :
- OS : _______________
- Python : _______________
- KeePassXC CLI : _______________

**Résultats** :
- Backend : ☐ OK  ☐ Erreurs
- Frontend : ☐ OK  ☐ Erreurs
- API : ☐ OK  ☐ Erreurs

**Commentaires** :
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## 🆘 Support

En cas de problème :
1. Vérifier les logs backend (dans le terminal)
2. Vérifier la console navigateur (F12)
3. Vérifier le fichier .env
4. Consulter la documentation API (/docs)

**Logs utiles** :
```bash
# Logs backend
cd backend
poetry run uvicorn app.main:app --reload --log-level debug

# Logs Redis (si utilisé)
docker compose logs redis

# Test keepassxc-cli
keepassxc-cli ls /path/to/test-database.kdbx
```

---

Bon test ! 🚀
