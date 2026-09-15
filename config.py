"""Carga la configuración del asistente desde el archivo .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
OPENCODE_WORKDIR = os.getenv("OPENCODE_WORKDIR", str(Path.home()))
PUSH_TO_TALK_HOTKEY = os.getenv("PUSH_TO_TALK_HOTKEY", "ctrl+space")

# --- Control remoto desde el celular ---
REMOTE_TOKEN = os.getenv("REMOTE_TOKEN", "")
REMOTE_PORT = int(os.getenv("REMOTE_PORT", "8765"))

if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "Falta ANTHROPIC_API_KEY. Copia .env.example como .env y completa tu API key."
    )
