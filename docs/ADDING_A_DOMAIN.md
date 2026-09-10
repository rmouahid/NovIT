# Ajouter un nouveau domaine — NovIT

Les « domaines » NovIT (`ia`, `securite`, `dev`, `ingenierie`, `reglementation`, `formation`)
catégorisent les articles pour le filtrage par profil et les commandes (`novit_get_by_domain`,
`novit_set_domains`, résumé quotidien...).

---

## 1. Modifier `config/domains.yaml`

Ajouter une entrée sous `domains:` :

```yaml
domains:
  # ... domaines existants ...

  data:                                    # clé = identifiant du domaine, snake_case
    label: "Data Engineering"              # libellé affiché à l'utilisateur
    keywords:
      - data engineering
      - etl
      - data pipeline
      - data warehouse
      - dbt
      - airflow
      - spark
```

`DomainTagger` (`src/scrapers/tagger.py`) charge ce fichier au démarrage et tague chaque
article dont le titre + résumé contient un des mots-clés (recherche insensible à la casse,
sous-chaîne simple — pas de regex). Les tags posés par un scraper (`article.domains` déjà
rempli) sont **enrichis, jamais écrasés**.

## 2. Choisir de bons mots-clés

- Inclure les variantes courantes (anglais + français si pertinent : `sécurité` / `security`).
- Éviter les mots-clés trop génériques qui provoqueraient de faux positifs sur d'autres domaines
  (ex : `"platform"` seul taguerait quasi tout le flux `ingenierie`).
- S'inspirer des domaines existants dans `config/domains.yaml` pour le niveau de granularité.

## 3. Adapter les profils si nécessaire

Un nouveau domaine n'apparaît dans les résultats d'un profil que si le profil l'accepte :
`filter_and_rank()` ne filtre pas sur le domaine par défaut, mais `score_article()`
(`src/profiles/filter.py`) pondère fortement (`domain_weight`) selon
`config/profiles.yaml` :

```yaml
profiles:
  INGENIEUR:
    domaines_favoris: [securite, ingenierie, ia, dev, data]   # poids ×1.5
    domaines_secondaires: [reglementation]                     # poids ×1.0
    # tout domaine absent des deux listes → poids ×0.6 (peut rester sous score_min et disparaître)
```

Ajouter le nouveau domaine à `domaines_favoris` ou `domaines_secondaires` d'un profil si NovIT
doit le mettre en avant pour ce profil (sinon les articles tagués passeront probablement sous
le `score_min` du profil et n'apparaîtront pas dans les réponses par défaut).

## 4. Tester le tagging automatique

```python
from src.scrapers.tagger import DomainTagger
from src.scrapers.base import Article
from datetime import datetime, UTC

tagger = DomainTagger()
article = Article(
    title="Building a modern ETL pipeline with dbt and Airflow",
    url="https://example.com/1", summary="", published_at=datetime.now(tz=UTC),
    source="test",
)
print(tagger.tag(article).domains)   # doit inclure "data"
```

En test automatisé (voir `tests/test_filter.py`/`tests/test_integration.py` pour le style) :

```python
def test_new_domain_tagging():
    tagger = DomainTagger()
    article = make_article(title="ETL pipeline avec dbt et Airflow")
    tagged = tagger.tag(article)
    assert "data" in tagged.domains
```

Vérifier aussi qu'un domaine existant n'est pas accidentellement capturé par les nouveaux
mots-clés (faux positif) en testant un titre d'un autre domaine.

## 5. Documenter le domaine ailleurs si emoji/label dédié attendu

`src/mcp/daily.py` (`domain_labels`) associe un emoji à chaque domaine pour le résumé
quotidien — sans entrée, le domaine s'affiche avec `domain.capitalize()` (acceptable, mais
moins soigné). Ajouter une entrée si le domaine est destiné à un usage fréquent :

```python
domain_labels = {
    "ia": "🤖 Intelligence Artificielle",
    # ...
    "data": "📊 Data Engineering",
}
```
