#!/usr/bin/env bash
set -e

docker stop pm-app 2>/dev/null || true
echo "Stopped"
