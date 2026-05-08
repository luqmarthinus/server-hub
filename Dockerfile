FROM python:3.12-slim-bookworm

# ------------------------------------------------------------------------------
# Env hardening
# ------------------------------------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ------------------------------------------------------------------------------
# Create non-root user first
# ------------------------------------------------------------------------------

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

# ------------------------------------------------------------------------------
# Install only required packages
# ------------------------------------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------------------------
# App directory
# ------------------------------------------------------------------------------

WORKDIR /app

# ------------------------------------------------------------------------------
# Install Python dependencies separately for layer caching
# ------------------------------------------------------------------------------

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --root-user-action=ignore -r requirements.txt

# ------------------------------------------------------------------------------
# Copy application code
# ------------------------------------------------------------------------------

COPY --chown=appuser:appgroup . /app

# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------

COPY --chown=appuser:appgroup docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod 755 /docker-entrypoint.sh

# ------------------------------------------------------------------------------
# Drop privileges
# ------------------------------------------------------------------------------

USER appuser

# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]