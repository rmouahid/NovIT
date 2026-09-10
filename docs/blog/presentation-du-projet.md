<!--
Brouillon de post de blog (dev.to / Medium) — voir #81.
À publier manuellement : ce dépôt ne publie rien automatiquement sur un compte externe.
-->

# NovIT : donner à Claude un accès temps réel à la veille tech

## Le problème

Claude a une date de coupure de connaissance. Pour tout ce qui bouge vite — un nouveau CVE
critique, la dernière annonce d'un labo IA, un repo qui explose sur GitHub Trending — il faut
soit copier-coller l'info à la main dans la conversation, soit accepter que Claude ne le sache
pas encore. Pour quelqu'un qui utilise Claude comme point d'entrée quotidien vers l'actu tech
(étudiant en veille, ingénieur qui doit rester à jour sur la sécu), ça casse le flux.

## La solution : un serveur MCP de veille

NovIT est un serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io/docs/) —
le protocole ouvert d'Anthropic pour connecter des outils externes à Claude. Concrètement :
Claude Desktop lance NovIT comme sous-processus local, lui pose des questions structurées
(« donne-moi les news IA des 6 dernières heures »), NovIT scrape/filtre/score et répond en
markdown prêt à être présenté.

Pas de compte à créer, pas de cloud requis pour l'usage de base : tout tourne en local.

### Ce que NovIT couvre

22 sources à ce jour : Hacker News, GitHub Trending, CVE/NVD, ANSSI, arXiv, blogs des grands
labos IA (OpenAI, DeepMind, Anthropic), blogs d'ingénierie (Netflix, Google, Meta), veille
réglementaire (CNIL, EUR-Lex/AI Act), sources de formation. Chaque article est tagué par domaine
(IA, sécurité, dev, ingénierie, réglementation, formation) et scoré selon un profil utilisateur.

### Deux profils, pas un mode générique

- **ETUDIANT** : ton pédagogique, sources accessibles, découvertes insolites.
- **INGENIEUR** : ton technique concis, CVE et blogs d'ingénierie en priorité, plus d'articles
  par requête.

Le scoring pondère chaque article selon les sources/domaines prioritaires du profil actif —
un même article n'a pas le même poids pour les deux profils.

## Architecture en 5 minutes

```
Claude Desktop ──(MCP, stdio)──▶ Serveur NovIT ──(HTTP)──▶ 22 sources externes
                                       │
                          TTLCache (mémoire) + SQLite (aiosqlite)
```

- **`ScraperManager`** lance les 22 scrapers en parallèle (`asyncio.gather`), avec timeout
  individuel — un scraper cassé ne bloque jamais les autres.
- **Déduplication** par URL exacte, hash de titre, et similarité de Jaccard fuzzy (pour capter
  les reprises du même événement par plusieurs sources avec des titres légèrement différents).
- **13 outils MCP** exposés : récupération de news, recherche, résumé quotidien, détection de
  tendances, extraction d'article complet, articles similaires, health check...
- **Cache TTL** en mémoire (1h pour les news) pour éviter de re-scraper à chaque appel.

Détails complets : [docs/TECHNICAL_DOCUMENTATION.md](../TECHNICAL_DOCUMENTATION.md) et les
[ADR](../ADR/) pour le pourquoi de chaque choix (y compris les compromis assumés).

## Comment l'utiliser

```bash
git clone https://github.com/LePhyX/NovIT.git
cd NovIT
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Puis ajouter NovIT à la config MCP de Claude Desktop — le
[guide d'installation complet](../INSTALLATION_GUIDE.md) détaille chaque étape, y compris les
pièges concrets (chemin absolu vers l'interpréteur du venv, `cwd` sur la racine du dépôt).

Ensuite, en conversation avec Claude : *« Quelles sont les dernières news IA pour un
ingénieur ? »*, *« Y a-t-il des CVE critiques cette semaine ? »*, *« Creuse cet article »*. Plus
d'exemples dans [docs/EXAMPLES.md](../EXAMPLES.md).

## Comment contribuer

Le projet est jeune et le backlog est public (voir les
[issues GitHub](https://github.com/LePhyX/NovIT/issues)). Deux points d'entrée simples pour une
première contribution :

- **Ajouter une source** : la majorité sont des flux RSS déclarés en quelques lignes, pas de
  code à écrire — voir [docs/ADDING_A_SOURCE.md](../ADDING_A_SOURCE.md).
- **Ajouter un domaine** : enrichir `config/domains.yaml` avec de nouveaux mots-clés — voir
  [docs/ADDING_A_DOMAIN.md](../ADDING_A_DOMAIN.md).

Le [guide de contribution](../../CONTRIBUTING.md) couvre le workflow complet (branches,
commits, PR). La CI (lint + 161 tests) tourne sur chaque PR.

---

*NovIT est un projet en développement actif — retours et contributions bienvenus.*
