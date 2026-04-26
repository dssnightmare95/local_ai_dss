#!/usr/bin/env bash
set -euo pipefail

MODEL="${OLLAMA_MODEL:-gemma4:e2b}"

docker compose -f docker-compose.download.yml up -d ollama-download
docker compose -f docker-compose.download.yml run --rm -e OLLAMA_MODEL="$MODEL" pull-model
docker compose -f docker-compose.download.yml down
docker compose up -d ollama
docker compose exec ollama ollama run "$MODEL"
