# Roadmap — NovIT

> Suivi détaillé : [milestones GitHub](https://github.com/rmouahid/NovIT/milestones).
> Proposer une idée : [Discussions → Ideas](https://github.com/rmouahid/NovIT/discussions/categories/ideas).

---

## État au 5 novembre 2026

| Milestone | Objectif | Statut |
|---|---|---|
| [M0 — Fondations](https://github.com/rmouahid/NovIT/milestone/1) | Repo, env, structure, docs | ✅ Terminé |
| [M1 — Architecture MCP](https://github.com/rmouahid/NovIT/milestone/2) | Serveur MCP fonctionnel | ✅ Terminé |
| [M2 — Scrapers](https://github.com/rmouahid/NovIT/milestone/3) | Toutes les sources | ✅ Terminé |
| [M3 — Logique de veille](https://github.com/rmouahid/NovIT/milestone/4) | Profils, filtrage, outils | ✅ Terminé |
| [M4 — Prompts](https://github.com/rmouahid/NovIT/milestone/5) | Qualité des réponses | ✅ Terminé |
| [M5 — UX](https://github.com/rmouahid/NovIT/milestone/6) | Commandes et navigation | ✅ Terminé |
| [M6 — Tests & monitoring](https://github.com/rmouahid/NovIT/milestone/7) | Robustesse et CI/CD | ✅ Terminé |
| [M7 — Documentation](https://github.com/rmouahid/NovIT/milestone/8) | Onboarding complet | ✅ Terminé |
| [M8 — Collaboration](https://github.com/rmouahid/NovIT/milestone/9) | Contributeurs et scalabilité | ✅ Terminé |
| [M9 — Release v1.0](https://github.com/rmouahid/NovIT/milestone/10) | Publication publique | 🔄 Release prête (#92), PyPI (#93), registre MCP (#94) |

---

## v1.0 — Publication publique

Reste à faire avant de couper la v1.0 :

1. Publier le paquet sur PyPI (#93), puis la fiche du registre MCP officiel (#94).
2. Préparer la release (#92) : CHANGELOG, `VERSION`, merge `dev` → `main`, tag `v1.0.0`.
3. Annoncer la sortie (#96), puis faire le bilan (#98).

Le support après la sortie (canaux, délais de réponse, triage) est décrit dans
[.github/SUPPORT.md](../.github/SUPPORT.md) et [SECURITY.md](../SECURITY.md).

## v1.1 — Qualité des résultats

Priorités relevées lors des essais réels, à traiter juste après la v1.0 :

| Sujet | Issue |
|---|---|
| Tagger par mots entiers, redirections suivies, flux morts remplacés | #118 |
| `novit_trends` : mots vides français et vocabulaire répétitif des CVE | #115 |
| Captures de NovIT dans un client MCP de bureau pour la documentation | #111 |


## Ensuite

Pistes ouvertes, sans engagement de date : nouvelles sources proposées par la
communauté
([modèle « Nouvelle source »](https://github.com/rmouahid/NovIT/issues/new?template=new_source.yml)),
déploiement cloud packagé ([docs/CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)).

---

_Mise à jour à chaque release._
