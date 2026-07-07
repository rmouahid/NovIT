#!/usr/bin/env bash
# Déploiement NovIT sur Fly.io — voir docs/CLOUD_DEPLOYMENT.md.
#
# Prérequis non satisfait à ce jour (ADR-001) : le serveur ne parle que
# stdio, pas HTTP/SSE. Ce script prépare le pipeline de déploiement (checks
# + flyctl) pour le jour où le transport HTTP+SSE sera implémenté ; il
# échouera au health check tant que ce n'est pas le cas. Ne pas exécuter en
# prod avant que #86 (volet transport HTTP) soit résolu.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> Vérifications avant déploiement"

if ! command -v flyctl >/dev/null 2>&1; then
    echo "flyctl introuvable. Installation : https://fly.io/docs/flyctl/install/" >&2
    exit 1
fi

echo "==> Lint (black, isort, ruff)"
black --check src tests
isort --check-only --profile black src tests
ruff check src tests

echo "==> Tests (hors benchmarks)"
pytest tests/ --benchmark-skip

echo "==> Déploiement Fly.io"
flyctl deploy --config fly.toml --remote-only

echo "==> Déploiement terminé. Vérifier : flyctl status --app novit-mcp"
