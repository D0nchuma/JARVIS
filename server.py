"""Servidor web para controlar Jarvis desde el celular (misma red o Tailscale).

Corré esto en una terminal aparte (además o en vez de main.py):
    python server.py

Después, desde el navegador del celular (Chrome), entrá a:
    http://IP_DE_TU_PC:8765
y guardá el token que pusiste en .env cuando te lo pida (se guarda en el
celular, no hace falta escribirlo de nuevo cada vez). Desde ahí podés
escribir comandos o tocar los botones rápidos.

Ver README.md, sección "Conectar el teléfono", para el paso a paso completo
(incluye cómo usarlo fuera de tu WiFi con Tailscale).
"""
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import config
from brain import Brain
from overlay import overlay

app = FastAPI(title="Jarvis Remote")
brain = Brain()
overlay.start()

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if not config.REMOTE_TOKEN:
    print(
        "⚠️  ADVERTENCIA: no configuraste REMOTE_TOKEN en tu .env. "
        "Cualquiera en tu red podría controlar tu PC. Configuralo antes de "
        "usar esto fuera de una red 100% de confianza."
    )


class CommandIn(BaseModel):
    text: str


def _check_token(x_jarvis_token: str | None):
    if config.REMOTE_TOKEN and x_jarvis_token != config.REMOTE_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")


@app.post("/command")
def command(payload: CommandIn, x_jarvis_token: str | None = Header(default=None)):
    _check_token(x_jarvis_token)
    overlay.show(f"📲  Desde el celular: {payload.text}")
    reply = brain.chat(payload.text)
    preview = reply if len(reply) <= 90 else reply[:87] + "..."
    overlay.update(f"💬  {preview}")
    return JSONResponse({"reply": reply})


@app.get("/health")
def health():
    return {"status": "ok", "assistant": config.ASSISTANT_NAME}


@app.get("/service-worker.js")
def service_worker():
    # Se sirve desde la raíz (no /static) para que su "scope" cubra
    # toda la app y pueda controlar la página principal.
    return FileResponse(STATIC_DIR / "service-worker.js", media_type="application/javascript")


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_PAGE.replace("__ASSISTANT_NAME__", config.ASSISTANT_NAME)


HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>__ASSISTANT_NAME__ Remoto</title>
<link rel="manifest" href="/static/manifest.json">
<link rel="icon" href="/static/icon-192.png">
<link rel="apple-touch-icon" href="/static/icon-192.png">
<meta name="theme-color" content="#0b0e14">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="__ASSISTANT_NAME__">
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 20px; min-height: 100vh;
    background: #0b0e14; color: #e6e9ef;
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
  }
  h1 { font-size: 1.3rem; font-weight: 600; margin: 0 0 16px; }
  #log {
    background: #12151c; border-radius: 12px; padding: 12px;
    min-height: 120px; max-height: 40vh; overflow-y: auto;
    font-size: 0.95rem; margin-bottom: 14px; white-space: pre-wrap;
  }
  .msg { margin-bottom: 10px; }
  .me { color: #7dd3fc; }
  .bot { color: #86efac; }
  form { display: flex; gap: 8px; margin-bottom: 16px; }
  input[type=text] {
    flex: 1; padding: 14px; border-radius: 10px; border: 1px solid #2a2f3a;
    background: #12151c; color: #e6e9ef; font-size: 1rem;
  }
  button {
    padding: 14px 18px; border-radius: 10px; border: none;
    background: #3b82f6; color: white; font-size: 1rem; font-weight: 600;
  }
  .quick { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .quick button {
    background: #1c2130; padding: 16px 8px; font-weight: 500;
  }
  #tokenBar { display: none; gap: 8px; margin-bottom: 14px; }
</style>
</head>
<body>
  <h1>🤖 __ASSISTANT_NAME__ remoto</h1>

  <div id="tokenBar">
    <input id="tokenInput" type="text" placeholder="Pegá tu REMOTE_TOKEN">
    <button onclick="saveToken()">Guardar</button>
  </div>

  <div id="log"></div>

  <form onsubmit="sendCommand(event)">
    <input id="textInput" type="text" placeholder="Ej: abrí Spotify" autocomplete="off">
    <button type="submit">Enviar</button>
  </form>

  <div class="quick">
    <button onclick="quick('Abrí Chrome')">🌐 Chrome</button>
    <button onclick="quick('Abrí Spotify')">🎵 Spotify</button>
    <button onclick="quick('¿Cómo está el sistema?')">📊 Estado PC</button>
    <button onclick="quick('Buscá las noticias de hoy')">🔎 Buscar noticias</button>
  </div>

  <button id="installBtn" style="display:none; width:100%; margin-top:14px; background:#1c2130;">
    ⬇️ Instalar como app
  </button>

  <script>
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/service-worker.js');
    }

    let deferredInstallPrompt = null;
    const installBtn = document.getElementById('installBtn');
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredInstallPrompt = e;
      installBtn.style.display = 'block';
    });
    installBtn.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      installBtn.style.display = 'none';
    });

    const log = document.getElementById('log');
    const tokenBar = document.getElementById('tokenBar');

    function getToken() { return localStorage.getItem('jarvis_token') || ''; }
    function saveToken() {
      localStorage.setItem('jarvis_token', document.getElementById('tokenInput').value.trim());
      tokenBar.style.display = 'none';
    }
    if (!getToken()) tokenBar.style.display = 'flex';

    function addMsg(cls, text) {
      const div = document.createElement('div');
      div.className = 'msg ' + cls;
      div.textContent = (cls === 'me' ? '🗣️ ' : '🤖 ') + text;
      log.appendChild(div);
      log.scrollTop = log.scrollHeight;
    }

    async function send(text) {
      if (!text) return;
      addMsg('me', text);
      try {
        const res = await fetch('/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Jarvis-Token': getToken() },
          body: JSON.stringify({ text })
        });
        if (res.status === 401) {
          addMsg('bot', 'Token inválido. Tocá el ícono de arriba para reconfigurarlo.');
          tokenBar.style.display = 'flex';
          return;
        }
        const data = await res.json();
        addMsg('bot', data.reply || '(sin respuesta)');
      } catch (e) {
        addMsg('bot', 'No pude conectarme al servidor. ¿Está corriendo y en la misma red?');
      }
    }

    function sendCommand(e) {
      e.preventDefault();
      const input = document.getElementById('textInput');
      const text = input.value.trim();
      input.value = '';
      send(text);
    }

    function quick(text) { send(text); }
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.REMOTE_PORT)
