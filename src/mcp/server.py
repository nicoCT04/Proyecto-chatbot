from __future__ import annotations

import json
import sys
from typing import Any, Callable

from . import protocol

ToolHandler = Callable[[dict[str, Any]], str]


class MCPServer:
    def __init__(self, name: str, version: str = "0.1.0") -> None:
        self.name = name
        self.version = version
        self.tools: list[dict[str, Any]] = []
        self.handlers: dict[str, ToolHandler] = {}

    def add_tool(self, name: str, description: str,
                 input_schema: dict[str, Any], handler: ToolHandler) -> None:
        self.tools.append({
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        })
        self.handlers[name] = handler

    def run(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            message = json.loads(line)
            response = self.dispatch(message)
            if response is not None:
                self._write(response)

    def dispatch(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        message_id = message.get("id")
        if method == "initialize":
            return protocol.make_result(message_id, {
                "protocolVersion": protocol.PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        if method == "tools/list":
            return protocol.make_result(message_id, {"tools": self.tools})
        if method == "tools/call":
            return self._call_tool(message_id, message.get("params", {}))
        if method == "ping":
            return protocol.make_result(message_id, {})
        if message_id is None:
            return None
        return protocol.make_error(
            message_id, protocol.METHOD_NOT_FOUND, f"unknown method: {method}")

    def _call_tool(self, message_id: int | str,
                   params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments", {})
        handler = self.handlers.get(name)
        if handler is None:
            return protocol.make_error(
                message_id, protocol.METHOD_NOT_FOUND, f"unknown tool: {name}")
        try:
            text = handler(arguments)
            is_error = False
        except Exception as failure:
            text = f"Error: {failure}"
            is_error = True
        return protocol.make_result(message_id, {
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        })

    def _write(self, message: dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
        sys.stdout.flush()
