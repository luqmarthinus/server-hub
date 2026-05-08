FROM python:3.12-slim-bookworm


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ------------------------------------------------------------------------------
# System dependencies (minimal + cleaned)
# ------------------------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*


RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser


WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt


COPY --chown=appuser:appgroup . /app

COPY --chown=appuser:appgroup docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod 755 /docker-entrypoint.sh

USER appuser

# ------------------------------------------------------------------------------
# Healthcheck 
# ------------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/live || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]