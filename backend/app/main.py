from __future__ import annotations

import os
from typing import Any

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
APP_NAME = os.getenv("APP_NAME", "LLM Control Hub")

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    model: str | None = None
    prompt: str
    system: str | None = None
    stream: bool = False


class CompareRequest(BaseModel):
    models: list[str] | None = None
    prompt: str
    system: str | None = None


def generate_model_response(model: str, prompt: str, system: str | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=180)
    response.raise_for_status()
    result = response.json()

    return {
        "model": model,
        "response": result.get("response", ""),
        "raw": result,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": APP_NAME,
        "ollama_base_url": OLLAMA_BASE_URL,
    }


@app.get("/models")
def list_models() -> dict[str, Any]:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=20)
        response.raise_for_status()
        data = response.json()
        models = [item["name"] for item in data.get("models", [])]
        return {"models": models or [DEFAULT_MODEL], "default_model": DEFAULT_MODEL}
    except Exception as exc:  # pragma: no cover
        return {"models": [DEFAULT_MODEL], "default_model": DEFAULT_MODEL, "warning": str(exc)}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    model = request.model or DEFAULT_MODEL
    result = generate_model_response(model, request.prompt, request.system)
    return result


@app.post("/compare")
def compare(request: CompareRequest) -> dict[str, Any]:
    selected_models = request.models or [DEFAULT_MODEL]
    results = [
        generate_model_response(model, request.prompt, request.system)
        for model in selected_models
    ]
    return {
        "models": selected_models,
        "results": results,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {APP_NAME}. Use /health, /models, /chat, and /compare."}
