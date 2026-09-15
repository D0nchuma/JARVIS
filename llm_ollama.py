"""Backend de LLM usando Ollama — modelo corriendo local en tu PC, sin
costo y sin API key. Requiere tener Ollama instalado y un modelo bajado
(ver README, sección de Ollama).

Solo modelos con "tool calling" sirven acá (el badge "tools" en
https://ollama.com/search?c=tools) — por ejemplo llama3.1, qwen2.5,
qwen3, mistral-nemo. Si usás un modelo sin esa capacidad, Jarvis va a
poder charlar pero nunca va a poder ejecutar acciones reales.
"""
import json

import ollama

import config


def _to_ollama_tools(tools_schema: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in tools_schema
    ]


class OllamaBackend:
    def __init__(self):
        self.client = ollama.Client(host=config.OLLAMA_HOST)

    def step(self, history: list[dict], tools_schema: list[dict], system_prompt: str):
        messages = [{"role": "system", "content": system_prompt}] + history
        response = self.client.chat(
            model=config.OLLAMA_MODEL,
            messages=messages,
            tools=_to_ollama_tools(tools_schema),
        )
        msg = response.message
        content = msg.content or ""
        raw_calls = msg.tool_calls or []

        tool_calls = []
        serializable_calls = []
        for i, call in enumerate(raw_calls):
            name = call.function.name
            args = call.function.arguments
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            args = dict(args) if args else {}
            tool_calls.append({"id": str(i), "name": name, "arguments": args})
            serializable_calls.append({"function": {"name": name, "arguments": args}})

        assistant_entry = {"role": "assistant", "content": content}
        if serializable_calls:
            assistant_entry["tool_calls"] = serializable_calls

        return assistant_entry, tool_calls, content

    def tool_result_messages(self, tool_results: list[dict]) -> list[dict]:
        return [
            {"role": "tool", "name": r["name"], "content": r["content"]}
            for r in tool_results
        ]
