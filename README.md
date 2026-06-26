# NovIT

> **Il sait, il connaît l'IT** — Serveur MCP de veille technologique pour Claude

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](VERSION)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Licence](https://img.shields.io/badge/licence-MIT-green)](LICENSE)
[![Statut](https://img.shields.io/badge/statut-en%20développement-orange)]()

---

## Présentation

NovIT est un **serveur MCP (Model Context Protocol)** qui permet à Claude d'accéder en temps réel à des sources de veille technologique : actualités, sécurité, IA, ingénierie logicielle, réglementation…

Il expose des outils MCP que Claude peut appeler pour récupérer, filtrer et synthétiser l'information selon le profil de l'utilisateur.

### Pourquoi NovIT ?

Claude possède une date de coupure de connaissance. NovIT lui donne accès à l'actualité tech **en temps réel**, de manière structurée et personnalisée, sans que l'utilisateur ait à copier-coller des articles.

---

## Fonctionnalités

### Outils MCP exposés

| Outil | Description |
|---|---|
| `novit_get_news` | Récupère les dernières news filtrées par profil et domaine |
| `novit_search` | Recherche plein texte dans les articles en cache |
| `novit_get_by_domain` | Filtre les articles par domaine technologique |
| `novit_get_profile` | Affiche le profil actif et ses préférences |
| `novit_dig` | Récupère et résume le contenu complet d'un article |
| `novit_related` | Trouve des articles similaires à un article donné |

### Profils utilisateur

- **ETUDIANT** : ton pédagogique, vulgarisation, découvertes insolites, sources accessibles
- **INGENIEUR** : ton technique, concision, CVE/sécurité, blogs d'ingénierie avancés

### Sources couvertes

| Catégorie | Sources |
|---|---|
| Actualités tech | Hacker News, TechCrunch, The Verge, MIT Tech Review |
| Intelligence artificielle | Anthropic Blog, OpenAI Blog, DeepMind, arXiv cs.AI, Papers With Code |
| Ingénierie | GitHub Trending, Netflix Tech Blog, Google Eng Blog, Meta Eng Blog |
| Sécurité | CVE/NVD, ANSSI Cert-FR |
| Réglementation | CNIL, EUR-Lex (AI Act), W3C News |
| Formation | freeCodeCamp, Roadmap.sh, Stack Overflow Survey |

---

## Installation

### Prérequis

- Python 3.11+
- [Claude Desktop](https://claude.ai/download) avec support MCP
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/LePhyX/NovIT.git
cd NovIT

# 2. Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Installer les dépendances
pip install -r requirements.txt  # production
# ou
pip install -r requirements-dev.txt  # développement

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs (optionnel pour commencer)

# 5. Lancer le serveur
python -m src.mcp
```

### Connecter à Claude Desktop

Ajouter dans la configuration MCP de Claude Desktop :

```json
{
  "mcpServers": {
    "novit": {
      "command": "python",
      "args": ["-m", "src.mcp"],
      "cwd": "/chemin/vers/NovIT"
    }
  }
}
```

---

## Quickstart

Une fois le serveur lancé et connecté à Claude :

```
Vous : Quelles sont les dernières news en IA pour un ingénieur ?
Claude : [utilise novit_get_news avec profil=INGENIEUR, domaine=IA]

Vous : Creuse cet article sur les LLMs
Claude : [utilise novit_dig avec l'URL de l'article]

Vous : Y a-t-il des CVE critiques cette semaine ?
Claude : [utilise novit_get_by_domain avec domaine=sécurité]
```

---

## Architecture

```
NovIT/
├── src/
│   ├── mcp/        # Serveur FastAPI + handlers MCP
│   ├── scrapers/   # Un scraper par source (HN, GitHub, CVE…)
│   ├── profiles/   # Logique de filtrage par profil
│   └── prompts/    # Prompts système et templates
├── tests/          # Tests unitaires et d'intégration
├── docs/           # Documentation technique
├── config/         # Configuration YAML (sources, profils, domaines)
└── scripts/        # Scripts utilitaires
```

Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) pour la vue détaillée.

---

## Développement

```bash
# Installer les hooks pre-commit
pip install pre-commit
pre-commit install

# Lancer les tests
pytest

# Vérifier le formatage
black src/ tests/
ruff check src/ tests/
```

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Guide de contribution](CONTRIBUTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](CHANGELOG.md)

---

## Licence

MIT — voir [LICENSE](LICENSE)
