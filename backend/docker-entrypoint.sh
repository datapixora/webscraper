#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-webscraper}"
APP_PORT="${BACKEND_PORT:-8000}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; do
  echo "Postgres not ready yet, retrying in 1s..."
  sleep 1
done

echo "Applying database migrations..."
alembic upgrade head

echo "Starting API on 0.0.0.0:${APP_PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT}" --reload
