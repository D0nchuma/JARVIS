"""Carga la configuración del asistente desde el archivo .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Qué "cerebro" usar: "ollama" (local, gratis) o "anthropic" (Claude, de pago) ---
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").strip().lower()

# --- Ollama (modelo local, sin costo, sin API key) ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# --- Anthropic / Claude (opcional, solo si LLM_BACKEND=anthropic) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
OPENCODE_WORKDIR = os.getenv("OPENCODE_WORKDIR", str(Path.home()))
PUSH_TO_TALK_HOTKEY = os.getenv("PUSH_TO_TALK_HOTKEY", "ctrl+space")

# --- Control remoto desde el celular ---
REMOTE_TOKEN = os.getenv("REMOTE_TOKEN", "")
REMOTE_PORT = int(os.getenv("REMOTE_PORT", "8765"))

if LLM_BACKEND not in {"ollama", "anthropic"}:
    raise RuntimeError("LLM_BACKEND en tu .env debe ser 'ollama' o 'anthropic'.")

if LLM_BACKEND == "anthropic" and not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "LLM_BACKEND=anthropic pero falta ANTHROPIC_API_KEY en tu .env. "
        "O bien completá esa key, o cambiá LLM_BACKEND=ollama para usar el modelo local gratis."
    )
