#!/usr/bin/env bash
# Déploiement NovIT sur Fly.io — voir docs/CLOUD_DEPLOYMENT.md.
#
# Le serveur tourne en transport HTTP (ADR-005) : définir le secret
# NOVIT_API_TOKEN avant le premier déploiement.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> Vérifications avant déploiement"

if ! command -v flyctl >/dev/null 2>&1; then
    echo "flyctl introuvable. Installation : https://fly.io/docs/flyctl/install/" >&2
    exit 1
fi

echo "==> Lint (black, isort, ruff)"
black --check novit tests
isort --check-only --profile black novit tests
ruff check novit tests

echo "==> Tests (hors benchmarks)"
pytest tests/ --benchmark-skip

echo "==> Déploiement Fly.io"
flyctl deploy --config fly.toml --remote-only

echo "==> Déploiement terminé. Vérifier : flyctl status --app novit-mcp"
