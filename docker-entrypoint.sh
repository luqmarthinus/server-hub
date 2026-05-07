#!/bin/bash
set -e

echo "Waiting for MySQL to be ready..."
until nc -z mysql 3306; do
    echo "MySQL not ready yet, waiting 2 seconds..."
    sleep 2
done

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1