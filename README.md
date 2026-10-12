# LLM Control Hub

A Dockerized local LLM control hub that runs a Python API, static web UI, and Ollama container. It lets you select a local model, send prompts, and inspect responses without sending data to a third-party service by default.

## What makes this project local-first

- The app is designed to run entirely on your local machine.
- The default behavior assumes the Ollama runtime and model files stay on the host.
- The app is intentionally simple and local-first: model inference happens in Ollama, not in a remote SaaS endpoint.
- `LOCAL_ONLY=true` is the default and indicates the intended runtime posture.

## Local-only and uncensored mode

This project supports the following safety and operational flags:

- `LOCAL_ONLY=true` — default posture for the app. It warns users that the instance is intended for local runtime usage.
- `UNCENSORED_MODE=false` — default posture; opt-in only. This disables any default safety layer imposed by the app itself.
- `API_KEY=` — optional local API key for protecting your local API.

## What's included

- `ollama`: local model runtime
- `api`: Python FastAPI service that calls the local model
- `web`: lightweight Nginx UI for interacting with the hub
- Docker Compose wiring for local development and testing
- Multi-model comparison and live streaming support
- Local prompt history storage in `.prompt_history.jsonl`

## Streaming support

Streaming means the response is displayed as it is generated, rather than waiting for the entire text to finish. The API uses `stream=True` when talking to Ollama and the frontend reads chunks from the stream in real time.

## API layer

The backend is a FastAPI app that exposes:
- `GET /health`
- `GET /status`
- `GET /history`
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

You can override the default runtime settings in `.env`:

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
UNCENSORED_MODE=true
API_KEY=my-local-key
```

## Local prompt history

This app stores recent interactions locally in a JSONL file named `.prompt_history.jsonl` in the repository root. It captures the model name, prompt, system prompt, and serialized result payload for local debugging and review.

## Useful commands

```bash
docker compose logs -f api

docker compose down

docker volume ls
```

## Responsible use and limits

This setup is intentionally simple and local-first. It is designed to run models you pull into Ollama, and the app does not require a hosted inference service. However, the project itself does not provide legal or policy guarantees. Using uncensored mode remains the operator's responsibility, and you should comply with local laws, content rules, and your environment's safety policies.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── history.py
│   │   ├── main.py
│   │   └── runtime.py
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
├── .prompt_history.jsonl
```
