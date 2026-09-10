# ADR-004 : Format de sortie standardisé — texte markdown, pas JSON structuré

**Statut :** Acceptée
**Date :** 2026-07-07 (rédigée rétroactivement)

## Contexte

Chaque outil MCP doit retourner un contenu que Claude peut directement présenter à
l'utilisateur, potentiellement en le résumant ou en le citant partiellement. Le protocole MCP
autorise plusieurs types de contenu (`text`, `image`, `resource`...) — voir
[MCP_NOTES.md](../MCP_NOTES.md).

## Décision

Tous les handlers NovIT (`src/mcp/handlers.py`, `daily.py`, `trends.py`, `dig.py`, `related.py`)
retournent une **chaîne de texte markdown**, encapsulée en `TextContent` côté serveur
(`src/mcp/server.py`). Structure commune : titre `#`/`##`, listes numérotées ou à puces, emoji
comme repères visuels rapides (🔗 lien, 📅 date, 🏷 domaines, 📰 source) — voir
[RESPONSE_FORMATS.md](../RESPONSE_FORMATS.md) pour le détail par outil, gelé par
`tests/test_prompt_regression.py`.

## Alternatives considérées

- **JSON structuré, mise en forme laissée à Claude** — écartée : oblige Claude à reformater
  systématiquement une structure de données brute à chaque appel, plus coûteux en tokens et en
  latence perçue que de recevoir un texte déjà lisible qu'il peut citer ou résumer directement.
  MCP permet en théorie de typer plus finement la sortie ; NovIT choisit la simplicité.
- **HTML** — écartée : Claude et les clients MCP affichent nativement du markdown, HTML
  n'apporte rien et complique le rendu terminal/texte brut.
- **Un format par outil, sans convention commune** — écartée : rendrait chaque outil
  imprévisible pour Claude (pas de motif reconnaissable d'un appel à l'autre) et empêcherait des
  tests de régression génériques sur la structure de sortie.

## Conséquences

- Impossible pour un client MCP non-Claude d'exploiter la donnée de façon programmatique sans
  reparser le markdown (pas de schéma de sortie machine-lisible) — acceptable tant que NovIT
  cible spécifiquement Claude comme unique consommateur.
- Toute évolution du format (ajout d'un champ, changement d'emoji) est une modification
  potentiellement risquée pour la compréhension de Claude — d'où `tests/test_prompt_regression.py`
  qui gèle la structure et doit être mis à jour consciemment, pas accidentellement, à chaque
  changement de handler.
- La longueur du texte doit rester maîtrisée (troncature à 100-300 caractères des résumés,
  4000 caractères pour `novit_dig`) pour respecter la contrainte de fenêtre de contexte MCP
  documentée dans [MCP_NOTES.md](../MCP_NOTES.md#contraintes-et-limitations-identifiées).
