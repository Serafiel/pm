#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

docker stop pm-app 2>/dev/null || true

echo "Building..."
docker build -t pm-app "$PROJECT_ROOT"

mkdir -p "$PROJECT_ROOT/data"

echo "Starting..."
docker run -d --rm --name pm-app -p 8000:8000 -v "$PROJECT_ROOT/data:/app/data" pm-app

echo "Running at http://localhost:8000"
