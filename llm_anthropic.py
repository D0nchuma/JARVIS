"""Backend de LLM usando la API de Anthropic (Claude). Requiere
ANTHROPIC_API_KEY y consume créditos de pago (ver consola de Anthropic).

Se usa solo si en .env ponés LLM_BACKEND=anthropic. Por defecto el
proyecto usa Ollama (llm_ollama.py), que es local y gratis.
"""
import anthropic

import config


def _to_anthropic_tools(tools_schema: list[dict]) -> list[dict]:
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools_schema
    ]


class AnthropicBackend:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def step(self, history: list[dict], tools_schema: list[dict], system_prompt: str):
        response = self.client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            tools=_to_anthropic_tools(tools_schema),
            messages=history,
        )
        assistant_entry = {"role": "assistant", "content": response.content}

        tool_calls = []
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "name": block.name, "arguments": block.input})

        return assistant_entry, tool_calls, text

    def tool_result_messages(self, tool_results: list[dict]) -> list[dict]:
        return [{
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": r["id"], "content": r["content"]}
                for r in tool_results
            ],
        }]
