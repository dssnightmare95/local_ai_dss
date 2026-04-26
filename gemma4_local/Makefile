MODEL ?= gemma4:e2b

.PHONY: download up bootstrap pull run chat ps logs down clean check-isolation

download:
	docker compose -f docker-compose.download.yml up -d ollama-download
	docker compose -f docker-compose.download.yml run --rm -e OLLAMA_MODEL=$(MODEL) pull-model
	docker compose -f docker-compose.download.yml down

up:
	docker compose up -d ollama

bootstrap: download up

pull:
	docker compose -f docker-compose.download.yml up -d ollama-download
	docker compose -f docker-compose.download.yml run --rm -e OLLAMA_MODEL=$(MODEL) pull-model
	docker compose -f docker-compose.download.yml down

run:
	docker compose exec ollama ollama run $(MODEL)

chat:
	curl http://localhost:11434/api/chat \
		-d '{"model":"$(MODEL)","messages":[{"role":"user","content":"Reply in English: confirm that local Gemma 4 is working."}],"stream":false}'

ps:
	docker compose ps

logs:
	docker compose logs -f ollama

check-isolation:
	docker inspect gemma4-local-ollama --format 'Port bindings: {{json .NetworkSettings.Ports}}'
	docker network inspect gemma4_local_local-only --format 'Internal network: {{.Internal}}'

down:
	docker compose down

clean:
	docker compose down -v
	docker compose -f docker-compose.download.yml down -v
