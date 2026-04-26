# Gemma 4 Local with Docker

Minimal project for running `gemma4:e2b` locally with Docker and Ollama, using an isolated inference mode.

## Requirements

- Docker
- Docker Compose v2
- At least 16 GB of RAM for `gemma4:e2b`
- Free disk space for the model. In Ollama, `gemma4:e2b` is approximately 7.2 GB.

A GPU is optional. If you do not have a GPU available, Ollama will run the model on CPU, although it will be slower.

## Network Security

The main service is configured to:

- Publish Ollama only on `127.0.0.1:${OLLAMA_HOST_PORT:-11434}`.
- Prevent access from other machines on the local network.
- Run inference on an internal Docker network without direct internet access.

Model download runs in a separate phase through `docker-compose.download.yml`, because Ollama only needs internet access to download the model.

## Quick Start

From the repository root:

```bash
cd gemma4_local
cp .env.example .env
make bootstrap
docker compose exec ollama ollama run gemma4:e2b
```

You can also use `make`:

```bash
cd gemma4_local
make bootstrap
make run
```

The first download can take several minutes.

## Recommended Workflow

Download the model with internet access:

```bash
cd gemma4_local
make download
```

Start Ollama in isolated mode:

```bash
make up
```

Open the local chat:

```bash
make run
```

`make bootstrap` runs `make download` and then `make up`.

## Test the API

Ollama is available only from your machine at `http://127.0.0.1:11434`.

```bash
curl http://127.0.0.1:11434/api/chat \
  -d '{
    "model": "gemma4:e2b",
    "messages": [
      {
        "role": "user",
        "content": "Reply in English: confirm that local Gemma 4 is working."
      }
    ],
    "stream": false
  }'
```

With `make`:

```bash
make chat
```

## Use an NVIDIA GPU

First install and configure NVIDIA Container Toolkit on the host. Then start the service with the GPU override:

```bash
cd gemma4_local
make download
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ollama
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec ollama ollama run gemma4:e2b
```

If Docker cannot see the GPU, the service can fail or fall back to CPU depending on the host configuration.

## Change the Model

Edit `gemma4_local/.env`:

```env
OLLAMA_MODEL=gemma4:e4b
```

Or run:

```bash
cd gemma4_local
make download MODEL=gemma4:e4b
make run MODEL=gemma4:e4b
```

## Verify Isolation

Check that the port is bound to localhost and that the Docker network is internal:

```bash
cd gemma4_local
make check-isolation
```

The expected output should show a port binding similar to `127.0.0.1:11434` and:

```text
Internal network: true
```

You can also validate it from the host:

```bash
docker inspect gemma4-local-ollama --format '{{json .NetworkSettings.Ports}}'
docker network inspect gemma4_local_local-only --format '{{.Internal}}'
```

## Useful Commands

Run these commands from `gemma4_local`:

```bash
docker compose ps
docker compose logs -f ollama
docker compose down
docker compose down -v
```

`docker compose down -v` deletes the volume with the downloaded models.

To delete all project resources, including downloaded models:

```bash
make clean
```
