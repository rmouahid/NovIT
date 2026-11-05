# Journal des changements importants

Le détail de chaque version est dans le
[CHANGELOG](https://github.com/rmouahid/NovIT/blob/dev/CHANGELOG.md). Ce journal
ne retient que ce qui change la façon d'installer, d'utiliser ou de contribuer.

## v1.0.0 — 5 novembre 2026

Première version publique.


- **Paquet `novit`** : le package `src` devient `novit` (rupture : lancer
  `python -m novit.mcp`), installable avec `pip install .` et bientôt depuis
  PyPI (#93, #119, #120).
- **SDK `mcp` 2.x** : le serveur suit la nouvelle API ; dépendance
  `mcp>=2.3.0,<3` (#112).
- **Transport HTTP** pour le déploiement distant, protégé par jeton
  ([ADR-005](https://github.com/rmouahid/NovIT/blob/dev/docs/ADR/0005-transport-http-authentification.md), #100).
- **Recherche par mots entiers** grâce à un index SQLite FTS5 (#104).
- **Mode hors-ligne** quand toutes les sources tombent (#91), **collecte
  complète en ~2 s** au lieu de 6 à 9 s (#90).
- **Retours utilisateurs** avec l'outil `novit_feedback` et un rapport
  hebdomadaire (#89).
- **Gestion des dépendances** : Dependabot et tests des versions minimales et
  dernières (#88).
- **Support** : canaux, délais de réponse, triage et politique de sécurité
  (#97).

## v0.1.0 — 26 juin 2026

Initialisation du projet : dépôt, structure, milestones M0 à M9.
