# Jarvis — Asistente de voz para Windows (Claude + OpenCode)

Asistente por voz que:
- Escucha lo que decís (push-to-talk, no está "siempre escuchando")
- Usa **Claude** como cerebro para entender y decidir qué hacer
- Delega tareas de código a **OpenCode**
- Controla tu PC: abrir/cerrar apps, volumen, lock/sleep/shutdown
- Te da el estado del sistema (CPU, RAM, disco, procesos)
- Te contesta hablando (texto a voz)

## 1. Requisitos previos

1. **Python 3.11+** instalado (marcá "Add to PATH" en el instalador).
2. **OpenCode** instalado y autenticado:
   ```
   npm install -g opencode-ai
   opencode auth login
   ```
   Verificá que funciona corriendo `opencode run "hola"` en una terminal.
3. **Ollama** (el "cerebro" gratis de Jarvis, corre local): ver sección 1.1.
4. **Micrófono** funcionando en Windows.

> ¿Preferís usar Claude en vez de un modelo local? Es de pago pero entiende
> mejor pedidos complejos. Saltá al final de esta sección (1.2).

### 1.1 Instalar Ollama (gratis, recomendado)

1. Descargalo de https://ollama.com/download/windows e instalalo (es un
   instalador normal de Windows, sin configuración rara).
2. Abrí PowerShell y bajá un modelo que soporte "tool calling" (o sea, que
   pueda ejecutar acciones, no solo charlar):
   ```powershell
   ollama pull llama3.1
   ```
   - `llama3.1` (8B): buen equilibrio, funciona razonable hasta en PCs sin
     GPU dedicada (más lento, pero anda). Necesita ~8GB de RAM libres.
   - `qwen2.5:7b` o `qwen3:8b`: alternativas livianas, buenas siguiendo
     instrucciones en español.
   - Si tenés una GPU NVIDIA con 12GB+ de VRAM, podés probar modelos más
     grandes (`llama3.1:70b`, etc.) para mejores resultados, mucho más
     lento sin esa VRAM.
3. Dejá Ollama corriendo en segundo plano (se inicia solo como servicio
   tras instalarlo; podés verificarlo entrando a http://localhost:11434
   en el navegador — debería responder "Ollama is running").
4. En tu `.env`, dejá `LLM_BACKEND=ollama` y `OLLAMA_MODEL=llama3.1` (o el
   que hayas bajado).

**Nota sobre calidad**: un modelo local de 7-8B parámetros va a entender
bien pedidos simples y directos ("abrí Chrome", "¿cómo está el sistema?"),
pero puede confundirse con pedidos ambiguos o encadenar mal varias
acciones — es la contra de que sea gratis y corra en tu PC en vez de en
los servidores de Anthropic. Si en algún momento un pedido no le sale, a
veces alcanza con pedírselo de forma más directa y específica.

### 1.2 Alternativa: usar Claude (de pago, mejor comprensión)

1. Conseguí una API key en https://console.anthropic.com/settings/keys
   (las cuentas nuevas reciben ~$5 de crédito de prueba).
2. En tu `.env`, poné `LLM_BACKEND=anthropic` y completá `ANTHROPIC_API_KEY`.

Podés cambiar entre uno y otro backend en cualquier momento editando esa
única línea del `.env` — no hace falta tocar nada más del código.

## 2. Instalación

Abrí PowerShell en esta carpeta y corré:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Si `PyAudio` falla al instalar en Windows, instalalo con:
> ```powershell
> pip install pipwin
> pipwin install pyaudio
> ```

Copiá `.env.example` como `.env` y completá los valores (el `LLM_BACKEND`
y lo que corresponda según el que elegiste en el paso 1):

```powershell
copy .env.example .env
notepad .env
```

## 3. Uso

```powershell
venv\Scripts\activate
python main.py
```

- Mantené presionado **Ctrl+Espacio** (configurable en `.env`) y hablá.
- Soltá y esperá la respuesta.
- Decí "salir" o "chau" para cerrar el asistente.
- Mientras te escucha, piensa o te contesta, aparece una burbuja flotante
  en la esquina inferior derecha de la pantalla (se cierra sola a los
  pocos segundos). Sirve para confirmar de un vistazo que te está
  escuchando, sin necesidad de mirar la consola. También aparece cuando
  el comando llega desde el celular (`server.py`), para que sepas qué
  está haciendo tu PC aunque no la estés mirando en ese momento.

Ejemplos de cosas que le podés pedir:
- *"Abrí el bloc de notas"*
- *"¿Cómo está el sistema?"*
- *"Decile a OpenCode que cree un script de Python que calcule fibonacci en mi carpeta de proyectos"*
- *"Subí el volumen"*
- *"Bloqueá la PC"*

## 4. Conectar el teléfono (Android)

Esto te permite mandarle comandos a Jarvis desde el celular — abrir apps,
buscar en internet, ver el estado del PC, etc. — usando una página web
simple que podés dejar como ícono en la pantalla de inicio.

### Paso 1: configurar el token de seguridad
En tu `.env`, poné un `REMOTE_TOKEN` largo y random (esto evita que
cualquiera en tu red controle tu PC). Ejemplo:
```
REMOTE_TOKEN=8f3a1c9d2e7b4f6a0d1c5e8b3a7f2d9c
```

### Paso 2: prender el servidor
```powershell
venv\Scripts\activate
python server.py
```
Vas a ver algo como `Uvicorn running on http://0.0.0.0:8765`.

> Podés correr `server.py` y `main.py` al mismo tiempo, en dos terminales
> distintas — comparten el mismo cerebro (Claude) pero son procesos
> independientes, así que la conversación de uno no la ve el otro.

### Paso 3: permitir el puerto en el Firewall de Windows
La primera vez que corras `server.py`, Windows va a preguntarte si permitís
la conexión — aceptá para **redes privadas**. Si no te preguntó, agregalo
manualmente en *Firewall de Windows Defender → Configuración avanzada →
Regla de entrada nueva → Puerto → TCP 8765 → Permitir*.

### Paso 4a: usarlo desde tu WiFi de casa (más simple)
1. En el PC, corré `ipconfig` y anotá la "Dirección IPv4" (ej: `192.168.1.50`).
2. En el celular (conectado a la **misma WiFi**), abrí Chrome y entrá a:
   `http://192.168.1.50:8765`
3. Pegá tu `REMOTE_TOKEN` cuando te lo pida.
4. En Chrome: menú (⋮) → **"Añadir a pantalla de inicio"** → te queda un
   ícono con el logo de Jarvis. Por HTTP (sin HTTPS) va a abrir dentro de
   Chrome con la barra de navegador visible — funciona perfecto, pero no
   es "pantalla completa". Para eso, seguí el paso 4c.

### Paso 4b: usarlo desde cualquier lado (fuera de tu WiFi)
Para esto **no** recomiendo abrir puertos en tu router hacia internet — es
un riesgo de seguridad grande. Usá **Tailscale** en cambio (gratis, crea
una red privada entre tus dispositivos):

1. Instalá Tailscale en el PC: https://tailscale.com/download/windows
2. Instalá la app "Tailscale" en tu Android (Play Store) y conectá ambos
   con la misma cuenta.
3. En el PC, corré `tailscale ip -4` para ver la IP de Tailscale de tu PC
   (algo como `100.x.x.x`).
4. Desde el celular, con Tailscale activo (con o sin WiFi, funciona con
   datos móviles también), entrá a `http://100.x.x.x:8765`.

### Paso 4c: instalarlo como app de verdad (ícono propio, sin barra del navegador)
Ya dejé todo listo para que esto sea una **PWA instalable** (manifest +
ícono + service worker en `static/`). El único requisito de Android/Chrome
para ofrecerte el instalado "de verdad" (ventana propia, sin barra de URL)
es que la conexión sea **HTTPS** — y Tailscale te lo da gratis:

1. Con Tailscale ya instalado (paso 4b), en el PC corré:
   ```powershell
   tailscale cert tu-maquina.tail1234.ts.net
   tailscale serve https / http://localhost:8765
   ```
   (el nombre `tu-maquina.tail1234.ts.net` te lo muestra `tailscale status`)
2. Desde el celular (con Tailscale conectado), entrá a
   `https://tu-maquina.tail1234.ts.net`.
3. Chrome va a mostrar un botón **"Instalar app"** solo, o desde el menú
   (⋮) → **"Instalar aplicación"**. Al tocarlo, Jarvis queda como una app
   real: ícono propio, pantalla completa, aparece en el selector de apps
   recientes.

> **¿Querés un .apk de verdad, para instalar como cualquier otra app o
> subir a la Play Store?** Con la PWA ya funcionando por HTTPS, podés
> pegar la URL en [PWABuilder](https://www.pwabuilder.com/) y te genera
> un paquete Android (.apk/.aab) instalable, sin escribir código nativo.
> Para eso necesitás exponer la URL a internet (con `tailscale funnel` en
> vez de `serve`) — avisame si querés que te arme ese paso también.

### Notas
- La página web es solo texto por ahora (sin dictado por voz desde el
  celular) — el reconocimiento de voz del navegador exige conexión HTTPS
  segura, igual que la instalación de la PWA. Si ya armaste el paso 4c,
  puedo sumarte el botón de micrófono — avisame.
- Los botones rápidos ("Chrome", "Spotify", etc.) son editables: abrí
  `server.py`, buscá la sección `<div class="quick">` en `HTML_PAGE` y
  cambiá los textos por tus apps favoritas.
- El ícono de la app está en `static/icon-192.png` y `static/icon-512.png`
  — si querés cambiar el diseño, reemplazá esos dos archivos (mismo
  tamaño) o pedime que te genere uno distinto.

## 5. Estructura del proyecto

```
config.py    → carga variables de entorno
llm_ollama.py    → backend de LLM local (Ollama, gratis)
llm_anthropic.py → backend de LLM Claude (Anthropic, de pago)
voice.py     → escucha (STT) y habla (TTS)
overlay.py   → burbuja flotante en pantalla con el estado de Jarvis
tools.py     → acciones reales sobre Windows (abrir apps, opencode, sistema, etc.)
brain.py     → conversación con Claude + loop de tool use
main.py      → loop principal / hotkey (uso por voz en la PC)
server.py    → servidor web + API para controlar Jarvis desde el celular
static/      → manifest, ícono y service worker de la app (PWA) del celular
```

## 6. Extender el asistente

- **Agregar una acción nueva**: escribí la función en `tools.py`, agregala al
  diccionario `TOOL_FUNCTIONS` y su definición en la lista `TOOLS`, ambos en
  `brain.py`. Claude la va a poder usar automáticamente, sin tocar nada más.
- **Wake-word real ("Jarvis, ...") en vez de hotkey**: se puede sumar
  [Picovoice Porcupine](https://picovoice.ai/) (tiene un tier gratuito),
  reemplazando el `kb.wait(...)` de `main.py` por su loop de detección.
- **STT 100% offline**: reemplazar `voice.listen()` por
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper) corriendo local.
- **Ejecutar solo, arranque con Windows**: crear un acceso directo a
  `venv\Scripts\pythonw.exe main.py` en la carpeta de inicio de Windows
  (`shell:startup`).

## 7. Seguridad

- Las acciones de `power_action` (shutdown/restart) ejecutan con 5 segundos
  de margen — tenés tiempo de cancelar con `shutdown /a` en una terminal.
- El asistente solo puede ejecutar las acciones definidas en `tools.py`; no
  tiene acceso libre a la terminal. `run_opencode` sí puede modificar
  archivos dentro de `OPENCODE_WORKDIR`, así que apuntalo a una carpeta de
  proyectos, no a `C:\`.
- Tu `.env` (con el token remoto y, si usás Claude, la API key) nunca se
  debe subir a un repositorio público.
- Ollama corre 100% local: nada de lo que le decís sale de tu PC hacia
  ningún servidor. Con Claude, en cambio, cada mensaje viaja a la API de
  Anthropic.
- `server.py` expone control de tu PC a la red — usalo siempre con
  `REMOTE_TOKEN` configurado, y preferí Tailscale antes que abrir puertos
  del router hacia internet.
