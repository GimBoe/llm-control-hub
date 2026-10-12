import os

APP_NAME = os.getenv("APP_NAME", "LLM Control Hub")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
LOCAL_ONLY = os.getenv("LOCAL_ONLY", "true").strip().lower() in {"1", "true", "yes", "on"}
UNCENSORED_MODE = os.getenv("UNCENSORED_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
API_KEY = os.getenv("API_KEY")
