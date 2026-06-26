# Guide de contribution — NovIT

Merci de vouloir contribuer à NovIT ! Ce guide explique comment soumettre des bugs, proposer des fonctionnalités et ouvrir des Pull Requests.

---

## Avant de commencer

1. **Lisez le [README](README.md)** pour comprendre le projet.
2. **Cherchez dans les [issues](https://github.com/LePhyX/NovIT/issues)** si votre sujet n'existe pas déjà.
3. Pour les changements importants, **ouvrez d'abord une issue** pour en discuter.

---

## Signaler un bug

Ouvrez une issue avec le label `bug` en incluant :
- La version de NovIT (`cat VERSION`)
- La version de Python (`python --version`)
- Les étapes pour reproduire le bug
- Le comportement observé vs attendu
- Les logs pertinents (niveau DEBUG si possible)

---

## Proposer une fonctionnalité

Ouvrez une issue avec le label `feature` en décrivant :
- Le problème que ça résout
- La solution proposée
- Les alternatives envisagées

---

## Ajouter une nouvelle source de scraping

Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#ajouter-une-source) pour le guide complet.
En résumé : copiez `src/scrapers/_template.py`, implémentez `BaseScraper`, ajoutez des tests.

---

## Workflow de contribution

### 1. Fork et clone

```bash
git clone https://github.com/VOTRE_USERNAME/NovIT.git
cd NovIT
git remote add upstream https://github.com/LePhyX/NovIT.git
```

### 2. Créer une branche

Nommage : `type/description-courte`

```bash
git checkout dev
git pull upstream dev
git checkout -b feature/mon-nouveau-scraper
```

Types : `feature/`, `fix/`, `doc/`, `chore/`, `test/`

### 3. Installer l'environnement de dev

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

### 4. Développer et tester

```bash
# Tests
pytest

# Formatage (appliqué automatiquement par pre-commit)
black src/ tests/
isort src/ tests/
ruff check src/ tests/
```

Les tests doivent passer à 100% avant d'ouvrir une PR.

### 5. Commits

Format : `type: description courte (#numéro-issue)`

```
feat: ajouter le scraper dev.to (#42)
fix: gérer le timeout sur Hacker News (#18)
doc: documenter l'outil novit_dig (#49)
chore: mettre à jour les dépendances (#88)
test: ajouter les tests d'intégration MCP (#65)
```

### 6. Ouvrir une Pull Request

- Base : branche `dev` (jamais `main` directement)
- Remplir le template de PR
- Lier l'issue correspondante (`Closes #N`)
- Attendre la review

---

## Standards de code

- Python 3.11+ obligatoire
- Formatage : **black** (88 caractères)
- Imports : **isort** (profil black)
- Linting : **ruff**
- Typage : annotations de type sur toutes les fonctions publiques
- Couverture de tests : 80% minimum

---

## Questions ?

Ouvrez une [Discussion GitHub](https://github.com/LePhyX/NovIT/discussions) ou une issue avec le label `question`.
