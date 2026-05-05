# Single stage: install dependencies directly into system Python
FROM python:3.12-slim-bookworm

# Security: run as non‑root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

# Prevent Python from writing .pyc files and enable bufferred logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (only if required by specific packages)
# For now, none needed beyond Python itself.

# Copy dependency definition file
COPY pyproject.toml .

# Install Python dependencies globally (no virtual environment)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source code
COPY --chown=appuser:appgroup . /app

# Switch to non‑root user
USER appuser

# Healthcheck (as before)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')" || exit 1

EXPOSE 8000

# Run uvicorn – now available in PATH
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]