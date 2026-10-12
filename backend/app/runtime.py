from __future__ import annotations

import hashlib
from typing import Any, Iterator

import requests


class RuntimeAdapter:
    def list_models(self) -> list[str]:
        raise NotImplementedError

    def get_provenance(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def generate(self, model: str, prompt: str, system: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def generate_stream(self, model: str, prompt: str, system: str | None = None) -> Iterator[str]:
        raise NotImplementedError


class OllamaRuntime(RuntimeAdapter):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def list_models(self) -> list[str]:
        response = requests.get(f"{self.base_url}/api/tags", timeout=20)
        response.raise_for_status()
        data = response.json()
        return [item["name"] for item in data.get("models", [])]

    def get_provenance(self) -> list[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/api/tags", timeout=20)
        response.raise_for_status()
        data = response.json()

        provenance: list[dict[str, Any]] = []
        for item in data.get("models", []):
            record = {
                "name": item.get("name", "unknown"),
                "source": "local Ollama runtime",
                "size": item.get("size"),
                "modified_at": item.get("modified_at"),
                "digest": item.get("digest"),
                "checksum": hashlib.sha256(
                    str(
                        {
                            "name": item.get("name"),
                            "size": item.get("size"),
                            "modified_at": item.get("modified_at"),
                            "digest": item.get("digest"),
                        }
                    ).encode("utf-8")
                ).hexdigest(),
            }
            provenance.append(record)
        return provenance

    def generate(self, model: str, prompt: str, system: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system

        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        return {
            "model": model,
            "response": result.get("response", ""),
            "raw": result,
        }

    def generate_stream(self, model: str, prompt: str, system: str | None = None) -> Iterator[str]:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        if system:
            payload["system"] = system

        response = requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=180)
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            yield line + "\n"
