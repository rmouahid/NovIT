# Publier NovIT sur PyPI

Le paquet `novit` est construit avec [hatchling](https://hatch.pypa.io/) à
partir de `pyproject.toml`. La version vient du fichier `VERSION`. La
publication est automatique : pousser un tag `vX.Y.Z` lance le workflow
`.github/workflows/publish.yml`, qui publie sur **TestPyPI** puis sur
**PyPI**.

L'authentification passe par le
[trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) :
PyPI fait confiance au workflow GitHub, sans jeton ni mot de passe à stocker
dans les secrets du dépôt.

## Contenu du paquet

| Élément | Où |
|---|---|
| Code | package `novit` (`novit.mcp`, `novit.scrapers`, `novit.profiles`, `novit.settings`) |
| Commande | `novit` : démarre le serveur MCP en stdio (`novit.mcp.server:run`) |
| Configuration par défaut | `config/*.yaml`, copiés dans la wheel sous `novit/data/` |
| Dépendances | identiques à `requirements.txt` (vérifié par `tests/test_packaging.py`) |

Au démarrage, `novit.settings.config_file()` lit `config/<fichier>.yaml` dans
le répertoire courant s'il existe (dépôt cloné, image Docker,
personnalisation locale), sinon la copie embarquée dans le paquet. Pour
personnaliser les sources d'une installation `pip`, créer un dossier
`config/` contenant le fichier à remplacer dans le répertoire de lancement.

## Configuration initiale (une seule fois)

1. **Comptes** : créer un compte sur [pypi.org](https://pypi.org/account/register/)
   et un autre sur [test.pypi.org](https://test.pypi.org/account/register/)
   (comptes distincts), avec la double authentification activée.
2. **Éditeurs de confiance en attente** : sur chacun des deux sites, aller dans
   *Your projects → Publishing → Add a new pending publisher* et
   renseigner :

   | Champ | TestPyPI | PyPI |
   |---|---|---|
   | PyPI Project Name | `novit` | `novit` |
   | Owner | `rmouahid` | `rmouahid` |
   | Repository name | `NovIT` | `NovIT` |
   | Workflow name | `publish.yml` | `publish.yml` |
   | Environment name | `testpypi` | `pypi` |

   Le projet `novit` est créé à la première publication.
3. **Environnements GitHub** : dans *Settings → Environments* du dépôt, créer
   `testpypi` et `pypi`. Pour `pypi`, ajouter une règle *Required reviewers*
   (soi-même) : la publication définitive attend alors une validation
   manuelle, après vérification de la page TestPyPI.

## Publier une version

1. Sur la branche `release/X.Y.Z` : mettre à jour `VERSION` et le
   `CHANGELOG.md`, puis fusionner dans `main`.
2. Taguer `main` et pousser le tag :

   ```bash
   git switch main && git pull
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

3. Le workflow vérifie que le tag correspond à `VERSION`, construit la wheel
   et la sdist (`twine check --strict`), publie sur TestPyPI, puis sur PyPI
   après validation de l'environnement `pypi`.
4. Contrôler l'installation depuis TestPyPI (les dépendances viennent de
   PyPI) :

   ```bash
   python -m venv /tmp/novit-test && . /tmp/novit-test/bin/activate
   pip install --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ novit
   novit < /dev/null   # démarre puis s'arrête proprement
   ```

5. Remplacer le badge « PyPI bientôt » du README par
   `https://img.shields.io/pypi/v/novit`.

Une version publiée sur PyPI ne peut pas être republiée sous le même numéro :
en cas d'erreur, corriger, incrémenter `VERSION` et taguer à nouveau.

## Vérifier localement avant un tag

```bash
pip install build twine
python -m build
twine check --strict dist/*
python -m venv /tmp/novit-wheel && /tmp/novit-wheel/bin/pip install dist/*.whl
cd /tmp && /tmp/novit-wheel/bin/novit < /dev/null
```

Le job CI `package` exécute ces étapes à chaque push et chaque pull request.

## Blocage observé sur v1.1.0

Le [workflow v1.1.0](https://github.com/rmouahid/NovIT/actions/runs/42323818530)
a construit et vérifié la wheel et la sdist avec succès. L'envoi TestPyPI a
ensuite échoué avec `invalid-publisher` : le jeton OIDC est valide, mais
TestPyPI ne trouve aucun éditeur de confiance correspondant. Le job PyPI a
donc été ignoré. Ce succès de build ne prouve pas une publication.

Sur le compte propriétaire de TestPyPI, enregistrer l'éditeur décrit plus
haut avec **owner `rmouahid`, dépôt `NovIT`, workflow `publish.yml`,
environnement `testpypi`**. Configurer séparément l'éditeur PyPI avec
l'environnement `pypi`. Il s'agit d'une configuration de compte externe ;
modifier le YAML seul ne crée pas ces éditeurs.

Après correction, relancer les jobs échoués du workflow de la version
concernée, puis vérifier la présence des distributions sur chaque index.
Ne pas recréer ni déplacer le tag existant. La
[documentation PyPI de diagnostic](https://docs.pypi.org/trusted-publishers/troubleshooting/)
détaille les écarts de claims possibles.
