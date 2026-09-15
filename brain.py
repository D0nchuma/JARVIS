"""Maneja la conversación con el LLM elegido (Ollama local o Claude/Anthropic),
incluyendo el ciclo de uso de tools.

El modelo decide, según lo que el usuario dice, si responde directo o si
pide ejecutar una o más acciones (tools). Este módulo ejecuta esas
acciones localmente (ver tools.py) y le devuelve el resultado al modelo
para que arme la respuesta final en lenguaje natural. La lógica del loop
es la misma sin importar qué backend esté detrás (ver llm_ollama.py /
llm_anthropic.py), así que cambiar de uno a otro es solo una línea en
el .env (LLM_BACKEND).
"""
import config
import tools

SYSTEM_PROMPT = f"""Sos {config.ASSISTANT_NAME}, un asistente de voz tipo JARVIS
que corre en la PC Windows del usuario. Respondé siempre en español rioplatense,
de forma breve y natural (esto se lee en voz alta, así que evitá listas largas,
markdown, o párrafos extensos). Sé directo y con un poco de personalidad, como
un asistente eficiente y con confianza, sin ser exagerado.

Tenés acceso a herramientas para controlar la PC y para delegar tareas de
programación a OpenCode (un agente de código que corre en la terminal).
Usá 'run_opencode' para CUALQUIER pedido de escribir, editar, revisar o
depurar código — no intentes escribir código vos mismo, delegalo.

Para acciones que apagan, reinician o duermen la PC, confirmá una sola vez
en tu respuesta de texto antes de ejecutarlas si el pedido fue ambiguo."""

TOOLS = [
    {
        "name": "open_app",
        "description": "Abre una aplicación o archivo en Windows por su nombre o ruta.",
        "parameters": {
            "type": "object",
            "properties": {"app_name": {"type": "string"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "close_app",
        "description": "Cierra (mata) un proceso en Windows por su nombre, ej: 'notepad'.",
        "parameters": {
            "type": "object",
            "properties": {"process_name": {"type": "string"}},
            "required": ["process_name"],
        },
    },
    {
        "name": "run_opencode",
        "description": (
            "Delega una tarea de programación (escribir, editar, revisar, "
            "depurar código, correr tests, etc.) al agente OpenCode."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Instrucción para OpenCode"},
                "working_dir": {
                    "type": "string",
                    "description": "Carpeta del proyecto (opcional, usa el default si no se indica)",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "system_status",
        "description": "Devuelve uso de CPU, RAM, disco y los procesos que más CPU consumen ahora.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "control_volume",
        "description": "Sube, baja o mutea el volumen del sistema.",
        "parameters": {
            "type": "object",
            "properties": {"action": {"type": "string", "enum": ["up", "down", "mute"]}},
            "required": ["action"],
        },
    },
    {
        "name": "power_action",
        "description": "Bloquea, duerme, apaga o reinicia la PC.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["lock", "sleep", "shutdown", "restart"]}
            },
            "required": ["action"],
        },
    },
    {
        "name": "search_web",
        "description": "Abre una búsqueda en el navegador para una consulta dada.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]

TOOL_FUNCTIONS = {
    "open_app": lambda i: tools.open_app(i["app_name"]),
    "close_app": lambda i: tools.close_app(i["process_name"]),
    "run_opencode": lambda i: tools.run_opencode(i["prompt"], i.get("working_dir")),
    "system_status": lambda i: tools.system_status(),
    "control_volume": lambda i: tools.control_volume(i["action"]),
    "power_action": lambda i: tools.power_action(i["action"]),
    "search_web": lambda i: tools.search_web(i["query"]),
}


def _build_backend():
    if config.LLM_BACKEND == "anthropic":
        from llm_anthropic import AnthropicBackend
        return AnthropicBackend()
    from llm_ollama import OllamaBackend
    return OllamaBackend()


class Brain:
    def __init__(self):
        self.history: list[dict] = []
        self.backend = _build_backend()

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        while True:
            assistant_entry, tool_calls, text = self.backend.step(
                self.history, TOOLS, SYSTEM_PROMPT
            )
            self.history.append(assistant_entry)

            if not tool_calls:
                return text

            tool_results = []
            for call in tool_calls:
                func = TOOL_FUNCTIONS.get(call["name"])
                try:
                    result = func(call["arguments"]) if func else f"Tool desconocida: {call['name']}"
                except Exception as e:
                    result = f"Error ejecutando {call['name']}: {e}"
                tool_results.append({"id": call["id"], "name": call["name"], "content": str(result)})

            self.history.extend(self.backend.tool_result_messages(tool_results))
