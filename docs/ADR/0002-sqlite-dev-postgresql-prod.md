# ADR-002 : SQLite en développement, PostgreSQL envisagé en production

**Statut :** Acceptée (volet SQLite) / Non implémentée (volet PostgreSQL)
**Date :** 2026-07-07 (rédigée rétroactivement)

## Contexte

`ArticleStore` (`src/scrapers/storage.py`) doit persister les articles scrapés avec des requêtes
simples (récence, filtres domaine/profil, recherche plein texte basique) et une rétention
courte (7 jours par défaut). Le projet vise un usage local (Claude Desktop) mais garde en tête
un déploiement distant multi-utilisateur futur (#86, #87).

## Décision

- **Dev/usage local :** SQLite via `aiosqlite`, fichier unique (`NOVIT_DB_PATH`, défaut
  `./novit.db`), zéro configuration.
- **Prod (visée, non implémentée) :** PostgreSQL, pour la concurrence en écriture et
  l'indexation avancée sous charge multi-utilisateur.

## Alternatives considérées

- **PostgreSQL partout, y compris en dev** — écartée : ajoute une dépendance d'infrastructure
  (conteneur ou service à faire tourner) pour un gain nul en usage mono-utilisateur local, alors
  que SQLite suffit largement au volume d'articles géré (quelques milliers, rétention 7 jours).
- **Un ORM (SQLAlchemy) dès le départ** pour abstraire SQLite/PostgreSQL — écartée pour l'instant :
  `ArticleStore` reste un module fin avec du SQL explicite (`aiosqlite`), suffisant tant qu'un
  seul backend est réellement utilisé. À reconsidérer si/quand PostgreSQL est implémenté.

## Conséquences

- **État réel du code à ce jour :** `config/settings.py` expose déjà `database_url` (vide par
  défaut), mais **rien ne le consomme** — `ArticleStore` est câblé en dur sur SQLite. Le volet
  PostgreSQL de cette ADR est une intention documentée, pas un fait acquis. Toute doc ou
  discussion qui présente NovIT comme « supportant PostgreSQL en prod » est actuellement
  inexacte tant que ce travail n'est pas fait.
- Le SQL de `storage.py` (requêtes `LIKE`, `INSERT OR IGNORE`) est écrit pour SQLite ; migrer
  vers PostgreSQL demandera une passe de portage (types, `ON CONFLICT`, index full-text natifs
  potentiellement plus pertinents qu'un `LIKE`), pas un simple changement de chaîne de connexion.
- Tant que ce n'est pas fait, un déploiement multi-utilisateur (#87) sur SQLite reste limité par
  les écritures concurrentes de SQLite — à garder en tête avant de lancer #87 sans #92/#86.
