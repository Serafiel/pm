#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

docker stop pm-app 2>/dev/null || true

echo "Building..."
docker build -t pm-app "$PROJECT_ROOT"

mkdir -p "$PROJECT_ROOT/data"

ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Warning: .env not found at $ENV_FILE — OPENROUTER_API_KEY will not be set"
fi

echo "Starting..."
ENV_ARG=""
[ -f "$ENV_FILE" ] && ENV_ARG="--env-file $ENV_FILE"
docker run -d --rm --name pm-app -p 8000:8000 -v "$PROJECT_ROOT/data:/app/data" $ENV_ARG pm-app

echo "Running at http://localhost:8000"
