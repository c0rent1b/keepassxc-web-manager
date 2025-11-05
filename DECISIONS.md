# 📋 Décisions Architecturales (ADR)

> Architecture Decision Records pour KeePassXC Web Manager v2.0

Date de création : 2025-11-05

---

## 📌 Résumé des décisions validées

| # | Décision | Statut | Date |
|---|----------|--------|------|
| ADR-001 | Stack Frontend : Alpine.js + Tailwind CSS | ✅ Accepté | 2025-11-05 |
| ADR-002 | Stack Backend : FastAPI + Pydantic v2 | ✅ Accepté | 2025-11-05 |
| ADR-003 | Architecture : Clean Architecture (Hexagonal) | ✅ Accepté | 2025-11-05 |
| ADR-004 | Cache : Redis dès le début | ✅ Accepté | 2025-11-05 |
| ADR-005 | Base de données : SQLite pour métadonnées | ✅ Accepté | 2025-11-05 |
| ADR-006 | Tests : Complet/Avancé (pytest) | ✅ Accepté | 2025-11-05 |
| ADR-007 | Développement : Phase par phase | ✅ Accepté | 2025-11-05 |

---

## ADR-001 : Stack Frontend

### Contexte
Besoin d'une interface moderne, réactive et performante pour remplacer le vanilla JS de v1.0.

### Décision
**Alpine.js 3.x + Tailwind CSS 3.x**

### Justification

**Alpine.js** :
- ✅ Léger (15KB minifié)
- ✅ Pas de build complexe nécessaire
- ✅ Syntaxe déclarative (comme Vue.js)
- ✅ Parfait pour enrichir du HTML existant
- ✅ Bonne DX (Developer Experience)

**Tailwind CSS** :
- ✅ Développement rapide
- ✅ Cohérence design garantie
- ✅ Responsive facile
- ✅ Mode sombre intégré
- ✅ Utilities-first (pas de CSS custom à maintenir)

### Alternatives considérées
- ❌ **Vue.js** : Trop lourd pour notre cas d'usage
- ❌ **React** : Build complexe, overkill
- ❌ **Vanilla JS** : Moins maintenable
- ❌ **Bootstrap** : CSS moins moderne

### Conséquences
- Courbe d'apprentissage légère pour Alpine.js
- HTML plus verbeux avec Tailwind
- Excellent compromis légèreté/fonctionnalités

---

## ADR-002 : Stack Backend

### Contexte
Besoin d'un framework Python moderne, performant et avec bonne validation.

### Décision
**FastAPI 0.110+ avec Pydantic v2**

### Justification
- ✅ Performance excellente (async natif)
- ✅ OpenAPI automatique (documentation)
- ✅ Validation robuste (Pydantic)
- ✅ Type hints Python
- ✅ Écosystème mature

### Alternatives considérées
- ❌ **Flask** : Moins moderne, pas de validation intégrée
- ❌ **Django** : Trop lourd, ORM non nécessaire
- ❌ **Quart** : Écosystème plus petit

### Conséquences
- Excellente maintenabilité
- Documentation API auto-générée
- Type safety

---

## ADR-003 : Architecture

### Contexte
Besoin d'une architecture évolutive, testable et maintenable.

### Décision
**Clean Architecture (Hexagonal)**

### Structure
```
Presentation Layer (API, UI)
    ↓
Application Layer (Services, Use Cases)
    ↓
Domain Layer (Entities, Interfaces)
    ↓
Infrastructure Layer (KeePassXC, DB, Cache, Security)
```

### Justification
- ✅ Séparation claire des responsabilités
- ✅ Testabilité maximale (mocks faciles)
- ✅ Indépendance de l'infrastructure
- ✅ Évolutivité garantie

### Alternatives considérées
- ❌ **Monolithe simple** : Moins maintenable long terme
- ❌ **Microservices** : Overkill pour notre taille

### Conséquences
- Plus de code initial (interfaces, abstractions)
- Meilleure maintenabilité long terme
- Tests plus faciles

---

## ADR-004 : Cache

### Contexte
Besoin de réduire les appels coûteux à `keepassxc-cli`.

### Décision
**Redis dès le début, avec fallback mémoire**

### Justification
- ✅ Performance excellente
- ✅ Persistance optionnelle
- ✅ TTL automatique
- ✅ Structures de données riches
- ✅ Production-ready

### Implémentation
```python
# Configuration
CACHE_BACKEND = "redis"  # ou "memory"
REDIS_URL = "redis://localhost:6379/0"

# Fallback automatique si Redis indisponible
if not redis_available():
    cache = MemoryCache()
else:
    cache = RedisCache()
```

### Stratégie de cache
- **Données en cache** :
  - Liste des entrées (TTL: 5 min)
  - Détails d'entrée (TTL: 10 min)
  - Statistiques database (TTL: 15 min)
  - Résultats de recherche (TTL: 2 min)

- **Invalidation** :
  - Automatique après création/modification/suppression
  - Par pattern de clés Redis
  - Logs détaillés d'invalidation

### Conséquences
- Dépendance externe (Redis)
- Meilleure performance
- Gestion de l'invalidation nécessaire

---

## ADR-005 : Base de données SQLite

### Contexte
Besoin de stocker des métadonnées applicatives sans complexifier le déploiement.

### Décision
**SQLite pour métadonnées NON-SENSIBLES uniquement**

### ⚠️ RÈGLE DE SÉCURITÉ ABSOLUE

```
╔═══════════════════════════════════════════════════════════╗
║  🔒 INTERDICTION STRICTE DE STOCKER DANS SQLITE :        ║
║                                                           ║
║  ❌ Mots de passe (passwords)                            ║
║  ❌ Secrets / Clés API                                   ║
║  ❌ Tokens d'authentification                            ║
║  ❌ Données de sécurité sensibles                        ║
║  ❌ Contenu des notes KeePassXC                          ║
║  ❌ Réponses aux questions secrètes                      ║
║  ❌ Fichiers de clé (.key)                               ║
║  ❌ Master passwords                                      ║
║                                                           ║
║  ✅ UNIQUEMENT : Métadonnées non-sensibles               ║
╚═══════════════════════════════════════════════════════════╝
```

### Données autorisées en SQLite

#### ✅ Audit Logs (non-sensible)
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(64),           -- Hash de session
    database_path VARCHAR(500),       -- Chemin fichier .kdbx
    action VARCHAR(50),               -- login, view, edit, delete
    entry_identifier VARCHAR(255),    -- Nom ou UUID (pas le contenu !)
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN,
    error_message TEXT                -- Message d'erreur (sans données sensibles)
);
```

**⚠️ Important** :
- `entry_identifier` = nom/UUID uniquement, **JAMAIS** le contenu
- `error_message` = sanitisé, sans données sensibles

#### ✅ Statistiques (agrégées)
```sql
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE,
    database_path VARCHAR(500),
    total_entries INT,                -- Nombre total
    weak_passwords_count INT,         -- Nombre de mots de passe faibles
    duplicate_count INT,              -- Nombre de doublons
    avg_password_age_days FLOAT,      -- Âge moyen
    login_count INT,
    failed_login_count INT
);
```

**⚠️ Important** : Agrégations uniquement, **pas de détails** individuels sur les mots de passe.

#### ✅ Préférences utilisateur (non-sensible)
```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64),
    database_path VARCHAR(500),
    theme VARCHAR(20),                -- dark, light
    language VARCHAR(5),              -- fr, en
    entries_per_page INT,
    favorite_entries TEXT,            -- JSON array de noms/UUIDs uniquement
    recent_views TEXT,                -- JSON array de noms/UUIDs uniquement
    updated_at DATETIME
);
```

**⚠️ Important** : `favorite_entries` contient des **identifiants** (noms ou UUID), jamais les données réelles.

#### ✅ Export History (métadonnées)
```sql
CREATE TABLE export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(64),
    database_path VARCHAR(500),
    export_format VARCHAR(20),        -- html, json, csv
    entries_count INT,
    included_passwords BOOLEAN,       -- Flag si passwords inclus
    exported_at DATETIME,
    file_hash_sha256 VARCHAR(64)      -- Hash du fichier exporté (audit)
);
```

**⚠️ Important** : Pas le contenu du fichier, juste les métadonnées.

#### ✅ Cache Metadata (temporaire)
```sql
CREATE TABLE cache_entries (
    cache_key VARCHAR(255) PRIMARY KEY,
    database_path VARCHAR(500),
    entry_count INT,                  -- Nombre d'entrées
    groups_list TEXT,                 -- JSON array de noms de groupes
    tags_list TEXT,                   -- JSON array de tags
    computed_at DATETIME,
    expires_at DATETIME
);
```

**⚠️ Important** : Cache de **métadonnées** uniquement (nombres, listes de noms), pas de contenu sensible.

### Données qui restent UNIQUEMENT dans KeePassXC

```
╔═══════════════════════════════════════════════════════════╗
║  🔐 CES DONNÉES RESTENT DANS KEEPASSXC UNIQUEMENT :      ║
║                                                           ║
║  • Passwords (mots de passe)                             ║
║  • Usernames                                              ║
║  • URLs                                                   ║
║  • Notes                                                  ║
║  • Attributs personnalisés                                ║
║  • TOTP secrets                                           ║
║  • Pièces jointes                                         ║
║  • Historique des entrées                                 ║
║                                                           ║
║  📍 Localisation : Fichier .kdbx chiffré                 ║
║  🔑 Accès : Via keepassxc-cli uniquement                 ║
╚═══════════════════════════════════════════════════════════╝
```

### Justification

**Pourquoi SQLite** :
- ✅ Pas de serveur à gérer (fichier unique)
- ✅ Intégré à Python
- ✅ Parfait pour métadonnées
- ✅ Migration vers PostgreSQL facile (SQLAlchemy)

**Pourquoi PAS de données sensibles** :
- 🔒 KeePassXC est conçu pour ça (chiffrement éprouvé)
- 🔒 Pas de duplication de données sensibles
- 🔒 Surface d'attaque réduite
- 🔒 Conformité aux bonnes pratiques

### Implémentation technique

#### Structure de fichiers
```
/home/user/data/
    ├── keepass_metadata.db       # SQLite (métadonnées)
    ├── my_passwords.kdbx         # KeePassXC (données sensibles)
    └── my_keyfile.key            # Keyfile KeePassXC
```

#### Configuration
```python
# config/settings.py
class Settings(BaseSettings):
    # SQLite pour métadonnées NON-SENSIBLES
    DATABASE_URL: str = "sqlite:///./keepass_metadata.db"

    # Interdiction stricte
    ALLOW_SENSITIVE_DATA_IN_DB: bool = False  # TOUJOURS False
```

#### Validation automatique
```python
# infrastructure/database/validators.py

FORBIDDEN_FIELDS = [
    "password", "passwd", "pwd", "secret", "token",
    "api_key", "private_key", "master_password",
    "totp_secret", "recovery_code"
]

def validate_data_safety(data: dict) -> None:
    """Vérifie qu'aucune donnée sensible n'est stockée"""
    for key in data.keys():
        if any(forbidden in key.lower() for forbidden in FORBIDDEN_FIELDS):
            raise SecurityError(
                f"INTERDIT: Tentative de stockage de donnée sensible '{key}' en DB"
            )
```

### Migrations

```python
# Alembic migrations
alembic/
    ├── versions/
    │   ├── 001_initial_schema.py
    │   ├── 002_add_audit_logs.py
    │   └── 003_add_user_preferences.py
    └── env.py
```

### Alternatives considérées
- ❌ **Pas de DB** : Perte de fonctionnalités (audit, stats)
- ❌ **PostgreSQL direct** : Overkill pour démarrer
- ❌ **Fichiers JSON** : Moins performant, pas de requêtes

### Conséquences
- ✅ Audit et statistiques possibles
- ✅ Déploiement simple (1 fichier SQLite)
- ✅ Migration PostgreSQL facile
- ⚠️ Gestion des migrations (Alembic)
- ⚠️ Attention à ne JAMAIS y mettre de données sensibles

---

## ADR-006 : Tests

### Contexte
Besoin de garantir la qualité et la non-régression.

### Décision
**Tests complets et avancés avec pytest**

### Stratégie de tests

#### 1. Tests unitaires (80%+ coverage)
```
tests/unit/
    ├── core/services/          # Business logic
    ├── infrastructure/         # CLI wrapper, cache, etc.
    └── schemas/                # Validation Pydantic
```

#### 2. Tests d'intégration
```
tests/integration/
    ├── test_keepassxc_cli.py   # Vraies interactions CLI
    ├── test_database.py        # SQLite
    └── test_cache.py           # Redis
```

#### 3. Tests E2E (end-to-end)
```
tests/e2e/
    └── test_api_flows.py       # Scénarios complets utilisateur
```

#### 4. Tests de sécurité
```
tests/security/
    ├── test_sql_injection.py
    ├── test_xss_protection.py
    ├── test_path_traversal.py
    └── test_sensitive_data.py  # Vérifier qu'aucune donnée sensible en DB
```

#### 5. Tests de performance
```
tests/performance/
    └── test_load.py            # Locust ou pytest-benchmark
```

### Outils
- **pytest** : Framework de base
- **pytest-asyncio** : Tests async
- **pytest-cov** : Coverage
- **pytest-mock** : Mocking
- **faker** : Génération de données test
- **factory_boy** : Fixtures complexes
- **httpx** : Client de test API
- **pytest-xdist** : Tests parallèles

### Objectifs
- ✅ 80%+ de couverture de code
- ✅ Tous les endpoints API testés
- ✅ Tous les services testés
- ✅ Tests de sécurité passants
- ✅ CI/CD avec tests automatiques

### Conséquences
- Plus de temps de développement initial
- Confiance élevée dans le code
- Facilité de refactoring

---

## ADR-007 : Développement

### Contexte
Besoin de livrer progressivement avec validation à chaque étape.

### Décision
**Développement phase par phase avec commits fréquents**

### Workflow
1. Développement d'une phase complète
2. Tests de la phase
3. Commit + push
4. Validation utilisateur
5. Phase suivante

### Ordre des phases
1. Phase 0 : Setup (1j)
2. Phase 1 : Infrastructure (3-4j)
3. Phase 2 : API Core (3-4j)
4. Phase 3 : Recherche + Tags (2-3j)
5. Phase 4 : Frontend (4-5j)
6. Phase 5 : Fonctionnalités avancées (3-4j)
7. Phase 6 : UX (2-3j)
8. Phase 7 : Sécurité (2j)
9. Phase 8 : Tests + Docs (2-3j)
10. Phase 9 : Docker (2j)

### Conséquences
- Feedback régulier
- Possibilité d'ajuster
- Moins de risque de grosse erreur

---

## 🔐 Annexe : Checklist de sécurité SQLite

### ✅ Avant chaque commit

- [ ] Aucun champ nommé `password`, `secret`, `token`, etc.
- [ ] Aucune donnée de KeePassXC stockée (sauf noms/UUIDs)
- [ ] Validation automatique en place
- [ ] Tests de sécurité passants
- [ ] Code review pour données sensibles

### ✅ En production

- [ ] SQLite en mode WAL (Write-Ahead Logging)
- [ ] Permissions fichier : 600 (lecture/écriture propriétaire uniquement)
- [ ] Backup régulier du fichier .db
- [ ] Logs d'accès au fichier DB
- [ ] Monitoring des requêtes suspectes

---

## 📝 Changelog des décisions

| Date | ADR | Changement |
|------|-----|------------|
| 2025-11-05 | ADR-001 à ADR-007 | Décisions initiales |

---

**Maintenu par** : Équipe de développement KeePassXC Web Manager
**Dernière mise à jour** : 2025-11-05
