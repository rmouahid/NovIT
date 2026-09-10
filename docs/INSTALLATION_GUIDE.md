# Guide d'installation — NovIT

Installation complète du serveur MCP NovIT en local, connexion à Claude Desktop, et
vérification que tout fonctionne.

---

## 1. Prérequis

| Outil | Version | Vérifier avec |
|---|---|---|
| Python | 3.11 ou supérieur | `python3 --version` |
| Git | toute version récente | `git --version` |
| Claude Desktop | version supportant MCP | [claude.ai/download](https://claude.ai/download) |

NovIT est un serveur **MCP en transport stdio** : Claude Desktop le lance lui-même comme
sous-processus (pas de port réseau à ouvrir, pas de compte cloud nécessaire pour l'usage local).

---

## 2. Installation pas à pas

### 2.1 Cloner le dépôt

```bash
git clone https://github.com/LePhyX/NovIT.git
cd NovIT
```

### 2.2 Créer et activer un environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows (PowerShell : .venv\Scripts\Activate.ps1)
```

### 2.3 Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt        # usage / production
# ou, pour contribuer au code (tests, lint) :
pip install -r requirements-dev.txt
```

### 2.4 Vérifier que le serveur démarre

```bash
python -m src.mcp < /dev/null
```

Sortie attendue (dans les logs, sur stderr) :

```
... INFO ... Démarrage du serveur NovIT MCP
... INFO ... Serveur NovIT arrêté
```

Le serveur lit le protocole MCP sur stdin/stdout : sans un vrai client MCP en face, il
s'arrête proprement dès qu'il atteint la fin de l'entrée (`< /dev/null` fournit un EOF
immédiat) — c'est le comportement normal, pas une erreur. (Ne pas utiliser `echo | python -m
src.mcp` pour ce test : le caractère de retour à la ligne envoyé par `echo` est interprété comme
un message JSON-RPC invalide et génère une erreur dans les logs.)

---

## 3. Configuration initiale

### 3.1 Fichier `.env`

```bash
cp .env.example .env
```

Toutes les variables ont une valeur par défaut fonctionnelle pour un usage local — `.env` n'est
**pas obligatoire** pour démarrer. À éditer seulement si besoin :

| Variable | Défaut | Quand la changer |
|---|---|---|
| `NOVIT_LOG_LEVEL` | `INFO` | `DEBUG` pour investiguer un problème |
| `NOVIT_DB_PATH` | `./novit.db` | Déplacer la base SQLite locale |
| `NOVIT_DEFAULT_PROFILE` | `ETUDIANT` | `INGENIEUR` si profil pro par défaut |
| `NVD_API_KEY` | vide | Augmente le rate limit CVE/NVD (optionnel) |
| `GITHUB_TOKEN` | vide | Augmente le rate limit GitHub Trending (optionnel) |
| `SENTRY_DSN` | vide | Active le tracking d'erreurs Sentry (optionnel, non requis pour l'usage local) |

Ne jamais committer `.env` (déjà exclu par `.gitignore`).

### 3.2 Connecter NovIT à Claude Desktop

Ouvrir la configuration MCP de Claude Desktop (`claude_desktop_config.json` — menu
Claude Desktop → Settings → Developer → Edit Config) et ajouter :

```json
{
  "mcpServers": {
    "novit": {
      "command": "/chemin/absolu/vers/NovIT/.venv/bin/python",
      "args": ["-m", "src.mcp"],
      "cwd": "/chemin/absolu/vers/NovIT"
    }
  }
}
```

**Points d'attention :**
- Utiliser le chemin **absolu** vers l'interpréteur du `.venv` (pas juste `python`) : Claude
  Desktop ne lance pas le processus dans un shell qui a activé le venv.
- `cwd` doit pointer sur la racine du dépôt (NovIT charge `config/*.yaml` en chemin relatif).
- Redémarrer complètement Claude Desktop après modification du fichier de config.

---

## 4. Vérifier que tout fonctionne

1. **Le serveur apparaît dans Claude Desktop** : dans une conversation, l'icône 🔌 (ou
   équivalent selon la version) doit lister `novit` avec ses outils.
2. **Appel simple** : demander à Claude *« Utilise novit_get_profile pour le profil ETUDIANT »*.
   Réponse attendue : un résumé markdown du profil (sources prioritaires, domaines favoris,
   score minimum) — ne nécessite aucun accès réseau ni base de données.
3. **Appel avec scraping réel** : demander *« Donne-moi les dernières news IA pour un
   ingénieur »*. Premier appel plus lent (le serveur scrape les sources à froid), appels
   suivants quasi instantanés (cache TTL 1h).
4. **Health check** : demander à Claude d'appeler `novit_health` → doit renvoyer `✅` avec un
   uptime et des stats de cache.

### En cas de problème

- Les logs du serveur ne s'affichent pas dans la conversation — Claude Desktop les redirige
  généralement vers un fichier logs applicatif (emplacement variable selon l'OS). Passer
  `NOVIT_LOG_LEVEL=DEBUG` dans `.env` pour plus de détail.
- Voir le [guide de débogage](TECHNICAL_DOCUMENTATION.md#4-guide-de-débogage) pour diagnostiquer
  un outil qui échoue ou une source de scraping indisponible.
- Vérifier l'installation hors Claude Desktop avec les tests : `pytest tests/ --benchmark-skip`
  (voir §2.3, nécessite `requirements-dev.txt`).

---

## 5. Alternative : Docker

```bash
docker compose up --build
```

Voir `docker-compose.yml` / `Dockerfile` (transport stdio également — `stdin_open: true` est
requis dans le service, déjà configuré). Le code source est monté en lecture seule pour le
hot-reload en développement (`./src:/app/src:ro`).
