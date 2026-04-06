#!/bin/bash
set -euo pipefail

docker compose up -d --build --force-recreate

echo
echo "Docker запущен."
echo "Проверить логи: docker compose logs -f"
