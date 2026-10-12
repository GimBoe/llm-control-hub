from __future__ import annotations

import os
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import API_KEY, APP_NAME, DEFAULT_MODEL, LOCAL_ONLY, OLLAMA_BASE_URL, UNCENSORED_MODE

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
    stream: bool = False


def _check_api_key(request: Request) -> None:
    if not API_KEY:
        return
    supplied = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if supplied != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def ollama_generate_stream(model: str, prompt: str, system: str | None):
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": True,
    }
    if system:
        payload["system"] = system

    response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, stream=True, timeout=180)
    response.raise_for_status()

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        yield line + "\n"


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


@app.get("/status")
def status() -> dict[str, Any]:
    return {
        "app": APP_NAME,
        "local_only": LOCAL_ONLY,
        "uncensored_mode": UNCENSORED_MODE,
        "ollama_base_url": OLLAMA_BASE_URL,
        "default_model": DEFAULT_MODEL,
        "api_key_configured": bool(API_KEY),
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": APP_NAME,
        "ollama_base_url": OLLAMA_BASE_URL,
        "local_only": LOCAL_ONLY,
        "uncensored_mode": UNCENSORED_MODE,
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
def chat(request: Request, payload: ChatRequest):
    _check_api_key(request)
    model = payload.model or DEFAULT_MODEL
    if payload.stream:
        return StreamingResponse(
            ollama_generate_stream(model, payload.prompt, payload.system),
            media_type="text/plain",
        )

    result = generate_model_response(model, payload.prompt, payload.system)
    return result


@app.post("/compare")
def compare(request: Request, payload: CompareRequest):
    _check_api_key(request)
    selected_models = payload.models or [DEFAULT_MODEL]

    if payload.stream:
        return {
            "status": "streaming_not_supported_for_compare",
            "payload": {
                "models": selected_models,
                "prompt": payload.prompt,
                "system": payload.system,
            },
        }

    results = [
        generate_model_response(model, payload.prompt, payload.system)
        for model in selected_models
    ]
    return {
        "models": selected_models,
        "results": results,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {APP_NAME}. Use /health, /models, /chat, and /compare."}
