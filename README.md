# LLM Control Hub

A Dockerized local LLM control hub that runs a Python API, static web UI, and Ollama container. It lets you select a local model, send prompts, and inspect responses without sending data to a third-party service.

## What's included

- `ollama`: local model runtime
- `api`: Python FastAPI service that calls the local model
- `web`: lightweight Nginx UI for interacting with the hub
- Docker Compose wiring for local development and testing
- Multi-model comparison and live streaming support

## Streaming support

Streaming means the response is displayed as it is generated, rather than waiting for the entire text to finish. The API uses `stream=True` when talking to Ollama and the frontend reads chunks from the HTTP response in real time.

## Dockerized option breakdown

### 1. API layer
The backend is a FastAPI app that exposes:
- `GET /health`
- `GET /models`
- `POST /chat`
- `POST /compare`

It proxies requests to the local Ollama runtime at `http://ollama:11434`.

### 2. Model runtime
The `ollama` container is the real inference engine. It keeps models on a Docker volume so they are not lost when the service restarts.

### 3. Web layer
The `web` service serves a simple HTML + JS interface on port `3000`, proxied to the API on port `8000`.

### 4. Runtime flow
- User types a prompt in the browser
- Browser sends request to `/api/chat`
- FastAPI sends the request to Ollama with `stream=True`
- Ollama streams chunks back as they are generated
- The browser renders each chunk in real time

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

## Useful commands

```bash
docker compose logs -f api

docker compose down

docker volume ls
```

## Notes

This setup is intentionally simple and local-first. It is designed to run models you pull into Ollama, so the "uncensored" or policy-free behavior depends entirely on the model you select and the environment you run it in.

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
