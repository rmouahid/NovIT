# ── Stage 1 : builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Dépendances système minimales pour la compilation des wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ── Stage 2 : runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Utilisateur non-root pour la sécurité
RUN addgroup --system novit && adduser --system --ingroup novit novit

# Copier les wheels compilés et les installer
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copier le code source
COPY src/ ./src/
COPY config/ ./config/
COPY VERSION .

# Droits sur les fichiers
RUN chown -R novit:novit /app
USER novit

ENV NOVIT_ENV=production \
    NOVIT_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

ENTRYPOINT ["python", "-m", "src.mcp.server"]
