"""Implementación de las acciones ('tools') que Claude puede pedir ejecutar.

Cada función corresponde a un tool_use que Claude puede invocar. Todas
devuelven un string simple que se le manda de vuelta a Claude como
tool_result, para que pueda comentarle el resultado al usuario.
"""
import os
import subprocess
import psutil

import config

# ---------------------------------------------------------------------------
# 1. Abrir / cerrar aplicaciones
# ---------------------------------------------------------------------------

def open_app(app_name: str) -> str:
    """Abre una app o archivo usando el comando 'start' de Windows."""
    try:
        os.startfile(app_name)  # type: ignore[attr-defined]
        return f"Abrí {app_name}."
    except FileNotFoundError:
        try:
            subprocess.Popen(f'start "" "{app_name}"', shell=True)
            return f"Abrí {app_name}."
        except Exception as e:
            return f"No pude abrir {app_name}: {e}"


def close_app(process_name: str) -> str:
    """Cierra todos los procesos que coincidan con el nombre (ej: 'notepad.exe')."""
    if not process_name.lower().endswith(".exe"):
        process_name += ".exe"
    result = subprocess.run(
        ["taskkill", "/IM", process_name, "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return f"Cerré {process_name}."
    return f"No encontré ningún proceso llamado {process_name} corriendo."


# ---------------------------------------------------------------------------
# 2. OpenCode: delegar tareas de código
# ---------------------------------------------------------------------------

def run_opencode(prompt: str, working_dir: str | None = None) -> str:
    """Ejecuta OpenCode en modo no interactivo ('opencode run') con un prompt.

    Requiere tener OpenCode instalado y autenticado (`opencode auth login`).
    """
    cwd = working_dir or config.OPENCODE_WORKDIR
    try:
        result = subprocess.run(
            ["opencode", "run", prompt],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        if result.returncode != 0:
            return f"OpenCode terminó con error: {error[-1500:] or 'sin detalle'}"
        return output[-3000:] if output else "OpenCode terminó sin mostrar salida."
    except FileNotFoundError:
        return (
            "No encontré el comando 'opencode'. ¿Está instalado y en el PATH? "
            "Instalación: https://opencode.ai/docs/"
        )
    except subprocess.TimeoutExpired:
        return "OpenCode tardó demasiado y corté la ejecución (timeout de 10 min)."


# ---------------------------------------------------------------------------
# 3. Estado del sistema
# ---------------------------------------------------------------------------

def system_status() -> str:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    top = sorted(
        psutil.process_iter(["name", "cpu_percent"]),
        key=lambda p: p.info["cpu_percent"] or 0,
        reverse=True,
    )[:5]
    top_str = ", ".join(f"{p.info['name']} ({p.info['cpu_percent']}%)" for p in top)
    return (
        f"CPU: {cpu}% | RAM: {mem.percent}% usada de {mem.total // (1024**3)}GB | "
        f"Disco C: {disk.percent}% usado | "
        f"Procesos con más CPU ahora: {top_str}"
    )


# ---------------------------------------------------------------------------
# 4. Volumen
# ---------------------------------------------------------------------------

def control_volume(action: str) -> str:
    """action: 'up', 'down', o 'mute'"""
    import keyboard as kb
    mapping = {"up": "volume up", "down": "volume down", "mute": "volume mute"}
    key = mapping.get(action)
    if not key:
        return "Acción de volumen no reconocida (usá up, down o mute)."
    for _ in range(5 if action != "mute" else 1):
        kb.send(key)
    return f"Listo, volumen: {action}."


# ---------------------------------------------------------------------------
# 5. Energía (con confirmación explícita ya validada por el usuario en el chat)
# ---------------------------------------------------------------------------

def power_action(action: str) -> str:
    """action: 'lock', 'sleep', 'shutdown', 'restart'"""
    commands = {
        "lock": "rundll32.exe user32.dll,LockWorkStation",
        "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
        "shutdown": "shutdown /s /t 5",
        "restart": "shutdown /r /t 5",
    }
    cmd = commands.get(action)
    if not cmd:
        return "Acción de energía no reconocida (usá lock, sleep, shutdown o restart)."
    os.system(cmd)
    return f"Ejecutando: {action}."


# ---------------------------------------------------------------------------
# 6. Búsqueda web (abre el navegador; no usa API de búsqueda)
# ---------------------------------------------------------------------------

def search_web(query: str) -> str:
    import webbrowser
    import urllib.parse
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"Abrí una búsqueda en el navegador para: {query}"
