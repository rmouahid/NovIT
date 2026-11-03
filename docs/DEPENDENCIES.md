# Gestion des dépendances

## Où sont-elles déclarées

| Fichier | Contenu |
|---|---|
| `requirements.txt` | dépendances d'exécution |
| `pyproject.toml` (`[project].dependencies`) | les mêmes, pour le paquet PyPI |
| `requirements-dev.txt` | `requirements.txt` + outils de test et de qualité |

`requirements.txt` et `pyproject.toml` doivent rester identiques :
`tests/test_packaging.py` échoue sinon. Toute modification se fait dans les deux
fichiers, dans le même commit.

## Politique de version

- **Bornes basses uniquement** (`>=`) : NovIT est une bibliothèque installée à
  côté d'autres paquets, figer des versions exactes provoquerait des conflits
  chez les utilisateurs.
- **Borne haute** seulement pour une dépendance dont la prochaine version
  majeure casse l'API connue : c'est le cas du SDK MCP (`mcp>=2.3.0,<3`).
- **Monter une borne basse** quand le code utilise une fonctionnalité apparue
  dans une version plus récente, ou pour exclure une version vulnérable.

## Mises à jour automatiques

- **Dependabot** (`.github/dependabot.yml`) :
  - actions GitHub : tous les mois ;
  - dépendances Python : toutes les semaines (lundi), mineures et correctifs
    regroupés dans une seule PR, majeures dans des PR séparées. Les alertes de
    sécurité ouvrent une PR sans attendre.
- **Workflow « Dépendances »** (`.github/workflows/dependencies.yml`), chaque
  lundi et sur toute PR qui touche les fichiers de dépendances :
  - `dernieres` : installe la dernière version publiée de tout et lance la suite
    de tests. Détecte une rupture amont avant qu'un utilisateur ne la subisse.
  - `minimales` : installe exactement les minimums de `requirements.txt` (avec
    des outils de test récents) et lance la suite. Vérifie que les bornes basses
    déclarées sont réellement suffisantes.

## Traiter une PR de mise à jour

1. Attendre la CI (lint, tests, paquet) et le workflow « Dépendances ».
2. Lire le changelog de la dépendance pour les mises à jour majeures.
3. Si les tests passent : merger (rebase), comme toute PR.
4. Si une nouvelle version casse NovIT : corriger le code, ou à défaut ajouter
   une borne haute temporaire (`<x`) avec une issue qui en suit la levée.

## Quand le workflow hebdomadaire échoue

- `dernieres` rouge sans PR associée : une dépendance a publié une version
  incompatible. Ouvrir une issue `bug` avec la sortie de `uv pip freeze` du job.
- `minimales` rouge : une borne basse est trop faible. La remonter à la plus
  petite version qui passe, dans `requirements.txt` et `pyproject.toml`.
