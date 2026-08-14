from __future__ import annotations

from typing import Any, Callable

from google import genai
from google.genai import types

ToolRunner = Callable[[str, dict[str, Any]], str]


class LLMChat:
    def __init__(self, api_key: str, model: str, system_prompt: str = "") -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt
        self.history: list[types.Content] = []

    def ask(self, user_message: str,
            tools: list[dict[str, Any]] | None = None,
            run_tool: ToolRunner | None = None) -> str:
        checkpoint = len(self.history)
        self.history.append(types.Content(
            role="user", parts=[types.Part(text=user_message)]))
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt or None,
            tools=self._as_gemini_tools(tools) if tools else None,
        )
        try:
            return self._run_turn(config, run_tool)
        except Exception:
            del self.history[checkpoint:]
            raise

    def _run_turn(self, config: types.GenerateContentConfig,
                  run_tool: ToolRunner | None) -> str:
        while True:
            response = self.client.models.generate_content(
                model=self.model, contents=self.history, config=config)
            self.history.append(response.candidates[0].content)
            calls = response.function_calls
            if not calls:
                return response.text or ""
            tool_responses = []
            for call in calls:
                output = run_tool(call.name, dict(call.args))
                tool_responses.append(types.Part.from_function_response(
                    name=call.name, response={"result": output}))
            self.history.append(types.Content(role="user", parts=tool_responses))

    def _as_gemini_tools(self, tools: list[dict[str, Any]]) -> list[types.Tool]:
        declarations = [
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("inputSchema") or None,
            )
            for tool in tools
        ]
        return [types.Tool(function_declarations=declarations)]
