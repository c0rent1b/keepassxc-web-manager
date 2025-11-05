# 🔧 Guide de Dépannage - KeePassXC Web Manager

> Solutions aux problèmes courants d'installation et de configuration

---

## 🐳 Problème : Docker Daemon non démarré

### Symptôme

```
unable to get image 'redis:7-alpine': Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

### Solution

Le daemon Docker n'est pas en cours d'exécution. Voici comment le démarrer :

#### 1. Vérifier le statut de Docker

```bash
sudo systemctl status docker
```

#### 2. Démarrer Docker

```bash
# Démarrer le service Docker
sudo systemctl start docker

# Activer le démarrage automatique
sudo systemctl enable docker

# Vérifier que Docker fonctionne
sudo docker ps
```

#### 3. Ajouter votre utilisateur au groupe docker (optionnel)

Pour éviter d'utiliser `sudo` à chaque fois :

```bash
# Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER

# Appliquer les changements (ou se déconnecter/reconnecter)
newgrp docker

# Tester sans sudo
docker ps
```

#### 4. Démarrer Redis

```bash
# Maintenant vous pouvez démarrer Redis
docker compose up -d redis

# Vérifier que Redis fonctionne
docker compose ps
```

---

## 📦 Problème : Poetry - Package Mode

### Symptôme

```
Error: The current project could not be installed: No file/folder found for package keepassxc-web-manager
```

### Solution

✅ **CORRIGÉ** : Le fichier `pyproject.toml` a été mis à jour avec `package-mode = false`.

Si vous avez encore l'erreur, assurez-vous d'avoir la dernière version :

```bash
# Mettre à jour depuis git
git pull origin claude/keepassxc-web-admin-redesign-011CUq3swaQXCMpemw2vctjJ

# Réinstaller les dépendances
poetry install
```

---

## 🐍 Python Version

### Vous avez Python 3.13 ?

✅ **C'est parfait !** Python 3.13 est compatible (même meilleur que 3.12).

Le projet est configuré pour `python = "^3.12"` ce qui signifie :
- ✅ Compatible avec Python 3.12
- ✅ Compatible avec Python 3.13
- ✅ Compatible avec Python 3.14+ (futures versions)

---

## 🔄 Checklist Complète d'Installation

Suivez ces étapes dans l'ordre :

### 1. ✅ Vérifier les prérequis

```bash
# Python version
python3 --version  # Doit être >= 3.12

# Poetry
poetry --version

# KeePassXC CLI
keepassxc-cli --version  # Doit être >= 2.7.10

# Docker
docker --version
```

### 2. ✅ Démarrer Docker

```bash
# Vérifier le statut
sudo systemctl status docker

# Si non démarré
sudo systemctl start docker

# Activer au démarrage
sudo systemctl enable docker

# Ajouter utilisateur au groupe (optionnel)
sudo usermod -aG docker $USER
newgrp docker
```

### 3. ✅ Installer les dépendances Python

```bash
cd ~/Build/keepassxc-web-manager

# Installer avec Poetry
poetry install

# Si erreur de package, vérifier pyproject.toml contient:
# package-mode = false
```

### 4. ✅ Démarrer Redis

```bash
# Démarrer Redis avec Docker Compose
docker compose up -d redis

# Vérifier que Redis fonctionne
docker compose ps

# Logs Redis (si besoin)
docker compose logs -f redis
```

### 5. ✅ Installer Node.js et dépendances

```bash
# Si Node.js n'est pas installé
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Installer les dépendances Node.js
npm install

# Build Tailwind CSS
npm run build:css
```

### 6. ✅ Créer le fichier .env

```bash
# Copier l'exemple
cp .env.example .env

# Générer une secret key sécurisée
openssl rand -hex 32

# Éditer .env et remplacer SECRET_KEY
nano .env
```

### 7. ✅ Tester l'installation

```bash
# Test Poetry
poetry run python --version

# Test que les imports fonctionnent
poetry run python -c "import fastapi; print('FastAPI OK')"
poetry run python -c "import redis; print('Redis OK')"

# Vérifier que les scripts sont exécutables
ls -la scripts/

# Si pas exécutables:
chmod +x scripts/*.sh
```

---

## 🧪 Commandes de Test

### Tester Redis

```bash
# Vérifier que Redis écoute
docker compose ps redis

# Tester la connexion Redis
docker compose exec redis redis-cli ping
# Devrait retourner: PONG

# Shell Redis interactif
docker compose exec redis redis-cli
# > SET test "hello"
# > GET test
# > EXIT
```

### Tester Poetry

```bash
# Liste des packages installés
poetry show

# Vérifier une dépendance spécifique
poetry show fastapi

# Shell interactif avec environnement Poetry
poetry shell

# Dans le shell:
python -c "import fastapi; print(fastapi.__version__)"
```

---

## 🚨 Problèmes Courants

### Conflit docker-compose / docker compose

**Symptôme** : `-bash: docker-compose: command not found`

**Solution** : Utilisez `docker compose` (sans tiret) au lieu de `docker-compose` :

```bash
# Ancien (docker-compose)
docker-compose up -d redis

# Nouveau (docker compose)
docker compose up -d redis
```

### Permission Denied sur Docker

**Symptôme** : `permission denied while trying to connect to the Docker daemon socket`

**Solution** :

```bash
# Option 1: Ajouter votre utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Option 2: Utiliser sudo
sudo docker compose up -d redis
```

### Redis ne démarre pas

**Symptôme** : `Error response from daemon: driver failed programming external connectivity`

**Solution** :

```bash
# Port 6379 déjà utilisé ?
sudo netstat -tlnp | grep 6379

# Arrêter Redis local si installé
sudo systemctl stop redis-server

# Ou changer le port dans docker-compose.yml
# Éditer la ligne:
# ports:
#   - "6380:6379"  # Utiliser 6380 au lieu de 6379
```

### Poetry lock file outdated

**Symptôme** : `The lock file is not compatible with the current version of Poetry`

**Solution** :

```bash
# Mettre à jour le lock file
poetry lock --no-update

# Réinstaller
poetry install
```

---

## 📞 Besoin d'Aide ?

Si vous rencontrez d'autres problèmes :

1. **Vérifier les logs** :
   ```bash
   # Docker
   docker compose logs redis

   # Poetry
   poetry install --verbose
   ```

2. **Informations système** :
   ```bash
   # Créer un rapport de debug
   echo "=== System Info ===" > debug.txt
   uname -a >> debug.txt
   python3 --version >> debug.txt
   poetry --version >> debug.txt
   docker --version >> debug.txt
   keepassxc-cli --version >> debug.txt

   cat debug.txt
   ```

3. **Logs complets** :
   ```bash
   # Tout relancer avec logs
   docker compose down
   docker compose up redis  # Sans -d pour voir les logs
   ```

---

## ✅ Validation Complète

Une fois tout installé, testez avec cette séquence :

```bash
# 1. Docker/Redis
docker compose ps
docker compose exec redis redis-cli ping

# 2. Poetry
poetry run python --version
poetry show | grep fastapi

# 3. Permissions scripts
ls -la scripts/
chmod +x scripts/*.sh

# 4. Tailwind CSS
ls -la frontend/public/css/

# 5. .env
ls -la .env

echo "✅ Installation validée !"
```

---

**Dernière mise à jour** : 2025-11-05
