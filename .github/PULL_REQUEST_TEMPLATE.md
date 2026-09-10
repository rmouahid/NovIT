## Résumé

<!-- Que fait cette PR, et pourquoi (pas juste "quoi" — le code le montre déjà). -->

Closes #

## Type de changement

- [ ] `feat` — nouvelle fonctionnalité
- [ ] `fix` — correction de bug
- [ ] `doc` — documentation uniquement
- [ ] `chore` — infra/config/dépendances
- [ ] `test` — ajout/modification de tests uniquement

## Checklist

- [ ] Base : branche `dev` (jamais `main` directement — voir [CONTRIBUTING.md](../CONTRIBUTING.md))
- [ ] Tests ajoutés/mis à jour, `pytest tests/ --benchmark-skip` passe en local
- [ ] `black`, `isort --profile black`, `ruff check` passent sans erreur
- [ ] Documentation mise à jour si le comportement d'un outil MCP change (voir
      [docs/RESPONSE_FORMATS.md](../docs/RESPONSE_FORMATS.md) et
      [tests/test_prompt_regression.py](../tests/test_prompt_regression.py) si le format de
      sortie d'un handler change)
- [ ] Pour un changement structurant : issue de discussion liée (voir
      [GOVERNANCE.md](../GOVERNANCE.md#prise-de-décision)) et/ou ADR ajoutée
      ([docs/ADR/](../docs/ADR/))

## Notes pour le reviewer

<!-- Points d'attention particuliers, choix discutables, ce qui reste à faire dans une PR suivante. -->
