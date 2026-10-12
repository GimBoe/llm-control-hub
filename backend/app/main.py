from __future__ import annotations

import os
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import API_KEY, APP_NAME, DEFAULT_MODEL, LOCAL_ONLY, OLLAMA_BASE_URL, UNCENSORED_MODE
from app.history import append_history_record, read_history
from app.runtime import OllamaRuntime

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runtime = OllamaRuntime(OLLAMA_BASE_URL)


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


def _log_interaction(kind: str, payload: dict[str, Any], result: dict[str, Any] | None = None) -> None:
    append_history_record(
        {
            "kind": kind,
            "local_only": LOCAL_ONLY,
            "uncensored_mode": UNCENSORED_MODE,
            "payload": payload,
            "result": result,
        }
    )


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
        models = runtime.list_models()
        return {"models": models or [DEFAULT_MODEL], "default_model": DEFAULT_MODEL}
    except Exception as exc:  # pragma: no cover
        return {"models": [DEFAULT_MODEL], "default_model": DEFAULT_MODEL, "warning": str(exc)}


@app.get("/history")
def history(limit: int = 20) -> dict[str, Any]:
    return {"history": read_history(limit=max(1, min(limit, 100)))}


@app.post("/chat")
def chat(request: Request, payload: ChatRequest):
    _check_api_key(request)
    model = payload.model or DEFAULT_MODEL
    _log_interaction(
        "chat",
        {
            "model": model,
            "prompt": payload.prompt,
            "system": payload.system,
            "stream": payload.stream,
            "uncensored_mode": UNCENSORED_MODE,
        },
    )

    if payload.stream:
        return StreamingResponse(
            runtime.generate_stream(model, payload.prompt, payload.system),
            media_type="text/plain",
        )

    result = runtime.generate(model, payload.prompt, payload.system)
    _log_interaction(
        "chat_response",
        {"model": model},
        result,
    )
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

    results = [runtime.generate(model, payload.prompt, payload.system) for model in selected_models]
    _log_interaction(
        "compare",
        {"models": selected_models, "prompt": payload.prompt, "system": payload.system},
        {"results": results},
    )
    return {"models": selected_models, "results": results}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {APP_NAME}. Use /health, /status, /history, /models, /chat, and /compare."}
