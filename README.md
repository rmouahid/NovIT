# NovIT

> **Il sait, il connaît l'IT** — Outil MCP de veille technologique pour Claude

NovIT est un serveur MCP (Model Context Protocol) qui connecte Claude à des sources de veille technologique en temps réel : Hacker News, GitHub Trending, CVE/ANSSI, blogs IA, réglementation, et plus encore.

## Fonctionnalités

- Veille personnalisée selon deux profils : **Étudiant** et **Ingénieur**
- Sources multiples : actualités tech, sécurité, IA, ingénierie, réglementation
- Outils MCP : `novit_get_news`, `novit_search`, `novit_get_by_domain`, `novit_dig`
- Cache intelligent avec TTL par source
- Résumé de veille quotidien

## Installation

> Documentation complète en cours de rédaction — voir [docs/](docs/)

**Prérequis :** Python 3.11+, Claude Desktop avec support MCP

```bash
git clone https://github.com/LePhyX/NovIT.git
cd NovIT
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Licence

MIT — voir [LICENSE](LICENSE)
