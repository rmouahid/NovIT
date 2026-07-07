# Architecture technique — NovIT

> Vision technique initiale · Version 0.1 · Juin 2026

---

## Vue d'ensemble

NovIT est un **serveur MCP (Model Context Protocol)** qui s'intercale entre Claude et des sources de données externes. Claude envoie des requêtes structurées au serveur via le protocole MCP ; le serveur interroge les sources, filtre les résultats selon le profil utilisateur, et renvoie une réponse structurée.

```
┌─────────────┐      MCP      ┌──────────────────┐     HTTP     ┌────────────────┐
│             │──────────────▶│                  │─────────────▶│ Sources web    │
│   Claude    │               │  Serveur NovIT   │              │ (HN, GitHub,   │
│  (client)   │◀──────────────│  (FastAPI + MCP) │◀─────────────│  CVE, RSS…)    │
│             │   Réponse     │                  │  Articles    │                │
└─────────────┘   structurée  └──────────────────┘              └────────────────┘
                                       │
                               ┌───────┴────────┐
                               │  Cache + SQLite │
                               └────────────────┘
```

---

## Modules

### `src/mcp/` — Serveur MCP

Point d'entrée du serveur. Responsable de :
- L'initialisation et le cycle de vie du serveur FastAPI
- Le handshake MCP avec Claude (négociation de capacités)
- Le routage des appels d'outils vers les handlers
- La gestion globale des erreurs et timeouts

**Fichiers attendus :**
```
src/mcp/
├── __init__.py
├── server.py        # Point d'entrée principal
├── handlers.py      # Implémentation des outils MCP
├── schemas.py       # Modèles Pydantic entrée/sortie
└── errors.py        # Codes d'erreur NovIT
```

### `src/scrapers/` — Scrapers

Un fichier par source de données. Tous héritent de `BaseScraper`.

**Interface `BaseScraper` :**
```python
class BaseScraper:
    async def fetch(self) -> list[Article]: ...
    async def health_check(self) -> bool: ...
```

**Format de sortie `Article` :**
```python
@dataclass
class Article:
    title: str
    url: str
    summary: str
    published_at: datetime
    source: str          # "hacker_news", "github_trending"…
    domains: list[str]   # ["ia", "securite", "dev"]…
    profiles: list[str]  # ["ETUDIANT", "INGENIEUR"]…
    score: float         # pertinence 0.0–1.0
```

### `src/profiles/` — Logique de profils

Filtrage et scoring des articles selon le profil actif.

**Profils disponibles :**
- `ETUDIANT` : sources accessibles, ton vulgarisé, contenu découverte
- `INGENIEUR` : sources techniques, CVE, blogs d'ingénierie, concision

**Responsabilités :**
- Pondérer les sources selon le profil
- Scorer chaque article (TF-IDF simplifié sur titre + résumé)
- Trier et paginer les résultats

### `src/prompts/` — Prompts système

Templates de prompts injectés dans chaque échange avec Claude.
Gestion des variables dynamiques (profil, domaines actifs, date/heure).

### `config/` — Configuration déclarative

| Fichier | Contenu |
|---|---|
| `settings.py` | Config Pydantic chargée depuis `.env` |
| `sources.yaml` | Liste de toutes les sources (URL, type, TTL, profils) |
| `profiles.yaml` | Définition des profils (sources prioritaires, domaines) |
| `domains.yaml` | Domaines NovIT et mots-clés associés |

### `tests/` — Tests

Structure miroir de `src/`. Chaque module a son fichier de tests.
- `tests/unit/` : tests unitaires (scrapers mockés, handlers MCP)
- `tests/integration/` : flux complets end-to-end

---

## Flux d'une requête

1. Claude appelle `novit_get_news(profil="INGENIEUR", domaines=["ia", "securite"])`
2. Le handler MCP valide les paramètres (Pydantic)
3. Le `ScraperManager` vérifie le cache : si présent et valide → retourne le cache
4. Sinon : lance les scrapers en parallèle (`asyncio.gather`)
5. Les articles sont agrégés, dédupliqués, taggés par domaine
6. Le moteur de profil filtre et score les articles
7. Le handler formate la réponse et la retourne à Claude
8. Claude synthétise et présente les résultats à l'utilisateur

---

## Décisions d'architecture

Voir [docs/ADR/](ADR/) pour les Architecture Decision Records complets (contexte, alternatives
écartées, conséquences assumées — y compris les écarts avec la vision initiale ci-dessous).

| Décision | Choix réel | ADR |
|---|---|---|
| Transport serveur MCP | SDK `mcp` officiel, stdio (pas FastAPI) | [ADR-001](ADR/0001-transport-serveur-mcp.md) |
| Base de données dev | SQLite (aiosqlite) | [ADR-002](ADR/0002-sqlite-dev-postgresql-prod.md) |
| Base de données prod | PostgreSQL envisagé, **non implémenté** | [ADR-002](ADR/0002-sqlite-dev-postgresql-prod.md) |
| Cache | `TTLCache` maison (TTL en mémoire) | [ADR-003](ADR/0003-strategie-cache-ttl.md) |
| Format de sortie des outils | Texte markdown (pas JSON structuré) | [ADR-004](ADR/0004-format-sortie-standardise.md) |
| Logging | loguru | API simple, JSON out-of-the-box en prod |

---

## Ajouter une source

1. Copier `src/scrapers/_template.py` → `src/scrapers/ma_source.py`
2. Implémenter `fetch()` et `health_check()`
3. Ajouter l'entrée dans `config/sources.yaml`
4. Écrire les tests dans `tests/unit/test_ma_source.py`
5. Ouvrir une PR avec le label `feature`

Voir [CONTRIBUTING.md](../CONTRIBUTING.md) pour le workflow complet.
