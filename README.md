# LLM Control Hub

A Dockerized local LLM control hub that runs a Python API, static web UI, and Ollama container. It lets you select a local model, send prompts, and inspect responses without sending data to a third-party service by default.

## What makes this project local-first

- The app is designed to run entirely on your local machine.
- The default behavior assumes the Ollama runtime and model files stay on the host.
- The app is intentionally simple and local-first: model inference happens in Ollama, not in a remote SaaS endpoint.

## Local-only and uncensored mode

This project now supports two important operational flags:

- `LOCAL_ONLY=true` — indicates the app is intended to run without outbound connectivity assumptions. It is enabled by default.
- `UNCENSORED_MODE=false` — disables pre-applied content filtering at the app level. This is opt-in and should be used only when you understand the risks and local legal requirements.

## What's included

- `ollama`: local model runtime
- `api`: Python FastAPI service that calls the local model
- `web`: lightweight Nginx UI for interacting with the hub
- Docker Compose wiring for local development and testing
- Multi-model comparison and live streaming support

## Streaming support

Streaming means the response is displayed as it is generated, rather than waiting for the entire text to finish. The API uses `stream=True` when talking to Ollama and the frontend reads chunks from the stream in real time.

## API layer

The backend is a FastAPI app that exposes:
- `GET /health`
- `GET /status`
- `GET /models`
- `POST /chat`
- `POST /compare`

It proxies requests to the local Ollama runtime at `http://ollama:11434` by default.

## Quick start

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Open the dashboard:

```text
http://localhost:3000
```

4. Pull a model when Ollama is ready:

```bash
docker exec -it llm-ollama ollama pull llama3.2
```

## Environment overrides

You can override the default OpenAI/Ollama settings in `.env`:

```dotenv
APP_NAME=LLM Control Hub
HOST=0.0.0.0
PORT=8000
LOCAL_ONLY=true
UNCENSORED_MODE=false
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2
API_KEY=
```

Examples:

```dotenv
OLLAMA_BASE_URL=http://host.docker.internal:11434
DEFAULT_MODEL=llama3.1:8b
LOCAL_ONLY=true
```

## Useful commands

```bash
docker compose logs -f api

docker compose down

docker volume ls
```

## Responsible use and limits

This setup is intentionally simple and local-first. It is designed to run models you pull into Ollama, and the app does not require a hosted inference service. However, the project itself does not provide law or policy guarantees. Using uncensored model behavior remains the operator's responsibility, and you should comply with local laws, content rules, and your environment's safety policies.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── nginx/
│   └── default.conf
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
```
