# Wiki NovIT

NovIT est un serveur MCP de veille technologique : actualités tech, CVE,
réglementation et tendances, filtrées selon un profil (ETUDIANT ou INGENIEUR)
et servies à n'importe quel client MCP.

> Ce wiki est généré depuis le dossier
> [`docs/wiki/`](https://github.com/rmouahid/NovIT/tree/dev/docs/wiki) du dépôt :
> modifiez les pages par pull request, pas dans l'interface du wiki (toute
> modification directe est écrasée à la publication suivante).

## Par où commencer

| Je veux… | Page |
|---|---|
| Installer NovIT et le brancher à mon client MCP | [Guide d'installation](https://github.com/rmouahid/NovIT/blob/dev/docs/INSTALLATION_GUIDE.md) |
| Savoir ce que fait chaque outil | [Documentation technique, §3](https://github.com/rmouahid/NovIT/blob/dev/docs/TECHNICAL_DOCUMENTATION.md#3-outils-mcp) |
| Résoudre un problème courant | [FAQ technique](FAQ-technique) |
| Comprendre pourquoi le projet est fait ainsi | [Décisions d'architecture](Decisions-d-architecture) |
| Suivre les changements importants | [Journal des changements](Journal-des-changements) |
| Ajouter une source ou un domaine | [Ajouter une source](https://github.com/rmouahid/NovIT/blob/dev/docs/ADDING_A_SOURCE.md) · [Ajouter un domaine](https://github.com/rmouahid/NovIT/blob/dev/docs/ADDING_A_DOMAIN.md) |
| Contribuer | [Guide de contribution](https://github.com/rmouahid/NovIT/blob/dev/CONTRIBUTING.md) |
| Obtenir de l'aide | [Support](https://github.com/rmouahid/NovIT/blob/dev/.github/SUPPORT.md) · [Discussions](https://github.com/rmouahid/NovIT/discussions) |

## En bref

- **Sources** : Hacker News, GitHub Trending, NVD, CERT-FR, blogs IA et
  d'ingénierie, flux réglementaires et de formation (`config/sources.yaml`),
  plus des plugins.
- **Stockage** : SQLite local (`NOVIT_DB_PATH`), recherche plein texte FTS5,
  rétention de 7 jours par défaut.
- **Transports** : stdio pour un client local (défaut), Streamable HTTP avec
  jeton bearer pour un déploiement distant.
- **Roadmap** : [docs/ROADMAP.md](https://github.com/rmouahid/NovIT/blob/dev/docs/ROADMAP.md).
