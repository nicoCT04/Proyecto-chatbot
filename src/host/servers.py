from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..mcp.client import MCPClient
from ..mcp.http_transport import HttpTransport
from ..mcp.transport import StdioTransport
from .logger import MCPLogger

GEMINI_SCHEMA_KEYS = {
    "type", "description", "properties", "required",
    "items", "enum", "nullable", "anyOf",
}


def load_server_configs(config_path: Path, workspace: str,
                        python_executable: str) -> list[dict[str, Any]]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    configs = []
    for entry in raw["servers"]:
        if "url" in entry:
            configs.append({"name": entry["name"], "url": entry["url"]})
            continue
        command = python_executable if entry["command"] == "python" else entry["command"]
        args = [arg.replace("${workspace}", workspace) for arg in entry["args"]]
        configs.append({"name": entry["name"], "command": command, "args": args})
    return configs


def sanitize_schema(schema: dict[str, Any]) -> dict[str, Any] | None:
    cleaned = {key: value for key, value in schema.items() if key in GEMINI_SCHEMA_KEYS}
    if "properties" in cleaned:
        cleaned["properties"] = {
            name: sanitize_schema(definition)
            for name, definition in cleaned["properties"].items()
        }
    if "items" in cleaned and isinstance(cleaned["items"], dict):
        cleaned["items"] = sanitize_schema(cleaned["items"])
    if cleaned.get("type") == "object" and not cleaned.get("properties"):
        return None
    return cleaned


def extract_text(result: dict[str, Any]) -> str:
    texts = [block["text"] for block in result.get("content", [])
             if block.get("type") == "text"]
    output = "\n".join(texts) or "(no output)"
    return f"ERROR: {output}" if result.get("isError") else output


class ServerManager:
    def __init__(self, logger: MCPLogger, console=None) -> None:
        self.logger = logger
        self.console = console
        self.clients: list[MCPClient] = []
        self.tool_owner: dict[str, MCPClient] = {}

    def start(self, server_configs: list[dict[str, Any]]) -> None:
        for config in server_configs:
            if "url" in config:
                transport = HttpTransport(config["url"])
            else:
                transport = StdioTransport(config["command"], config["args"])
            client = MCPClient(config["name"], transport,
                               on_message=self.logger.for_server(config["name"]))
            client.connect()
            client.list_tools()
            self.clients.append(client)
            for tool in client.tools:
                self.tool_owner[tool["name"]] = client

    def tool_definitions(self) -> list[dict[str, Any]]:
        definitions = []
        for client in self.clients:
            for tool in client.tools:
                definitions.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": sanitize_schema(tool.get("inputSchema", {})),
                })
        return definitions

    def run_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if self.console is not None:
            self.console.print(f"[dim]  → {name}({arguments})[/dim]")
        client = self.tool_owner[name]
        result = client.call_tool(name, arguments)
        return extract_text(result)

    def close(self) -> None:
        for client in self.clients:
            client.close()
