# Gouvernance — NovIT

## Rôles

### Mainteneur

- Fusionne les pull requests vers `dev` et `main`.
- Décide de la roadmap et arbitre les désaccords de conception (via issue de discussion avant
  tout changement important, cf. [CONTRIBUTING.md](CONTRIBUTING.md)).
- Coupe les releases (voir *Processus de release* ci-dessous).
- Fait respecter le [Code de conduite](CODE_OF_CONDUCT.md).

À ce jour, [LePhyX](https://github.com/LePhyX) est l'unique mainteneur du projet. Cette section
sera mise à jour si l'équipe de maintenance s'élargit.

### Reviewer

- Relit les pull requests d'autres contributeurs : correction, respect des standards de code
  (voir *Standards de code* dans [CONTRIBUTING.md](CONTRIBUTING.md)), couverture de tests.
- Peut approuver une PR mais la fusion reste une action de mainteneur.
- Statut accordé par un mainteneur à un contributeur régulier qui démontre une bonne
  compréhension du projet (pas de processus formel de nomination à ce stade du projet).

### Contributor

- Toute personne qui ouvre une issue, propose une PR, ou participe aux discussions.
- Aucune permission d'écriture requise sur le dépôt : le workflow passe par fork + PR (voir
  [CONTRIBUTING.md](CONTRIBUTING.md#1-fork-et-clone)).

## Prise de décision

- **Changements mineurs** (bugfix, doc, nouvelle source RSS, nouveau domaine) : une PR
  conforme aux standards de code peut être fusionnée directement par un mainteneur, sans
  discussion préalable obligatoire.
- **Changements structurants** (nouvelle dépendance majeure, changement de format de sortie,
  changement d'architecture) : à discuter dans une issue **avant** d'ouvrir la PR — voir
  [ADR](docs/ADR/) pour la façon de documenter la décision une fois prise.
- **Désaccord non résolu** : le mainteneur tranche en dernier ressort.

## Processus de release

NovIT suit [Semantic Versioning](https://semver.org/lang/fr/) (`MAJOR.MINOR.PATCH`) et tient un
[CHANGELOG.md](CHANGELOG.md) au format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

1. Les changements s'accumulent sur `dev` (branche de développement par défaut,
   `no-commit-to-branch: main` est appliqué par les hooks pre-commit).
2. Avant une release : vérifier que `CHANGELOG.md` reflète les changements notables depuis la
   dernière version (section `[Unreleased]` → nouvelle section versionnée), mettre à jour
   `VERSION`.
3. Merge `dev` → `main`.
4. Tag Git `vX.Y.Z` sur `main`, release GitHub correspondante (notes reprenant le CHANGELOG).
5. Publication des artefacts si applicable (PyPI, registre MCP — voir la checklist de release
   dans les issues de préparation de version).

**Versionnage** : `MAJOR` pour un changement de comportement d'outil MCP incompatible avec
l'existant (ex : renommer/retirer un paramètre d'entrée), `MINOR` pour une nouvelle
fonctionnalité rétrocompatible (nouvel outil, nouvelle source), `PATCH` pour un correctif sans
changement de comportement observable.

## Code de conduite

Voir [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
