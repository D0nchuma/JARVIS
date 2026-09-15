"""Maneja la conversación con Claude, incluyendo el ciclo de uso de tools.

Claude decide, según lo que el usuario dice, si responde directo o si
pide ejecutar una o más acciones (tools). Este módulo ejecuta esas
acciones localmente (ver tools.py) y le devuelve el resultado a Claude
para que arme la respuesta final en lenguaje natural.
"""
import anthropic
import config
import tools

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

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
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "close_app",
        "description": "Cierra (mata) un proceso en Windows por su nombre, ej: 'notepad'.",
        "input_schema": {
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
        "input_schema": {
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
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "control_volume",
        "description": "Sube, baja o mutea el volumen del sistema.",
        "input_schema": {
            "type": "object",
            "properties": {"action": {"type": "string", "enum": ["up", "down", "mute"]}},
            "required": ["action"],
        },
    },
    {
        "name": "power_action",
        "description": "Bloquea, duerme, apaga o reinicia la PC.",
        "input_schema": {
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
        "input_schema": {
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


class Brain:
    def __init__(self):
        self.history: list[dict] = []

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})

        while True:
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history,
            )

            self.history.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join(
                    block.text for block in response.content if block.type == "text"
                )

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                func = TOOL_FUNCTIONS.get(block.name)
                try:
                    result = func(block.input) if func else f"Tool desconocida: {block.name}"
                except Exception as e:
                    result = f"Error ejecutando {block.name}: {e}"
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
                )

            self.history.append({"role": "user", "content": tool_results})
