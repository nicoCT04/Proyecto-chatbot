from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from rich.console import Console
from rich.table import Table

from ..mcp import protocol

ServerHook = Callable[[str, dict[str, Any]], None]


def classify_message(message: dict[str, Any]) -> str:
    if protocol.is_response(message):
        return "error" if "error" in message else "response"
    if protocol.is_notification(message):
        return "notification"
    return "request"


class MCPLogger:
    def __init__(self, log_dir: str = "logs", console: Console | None = None) -> None:
        self.console = console or Console()
        self.interactions: list[dict[str, Any]] = []
        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = Path(log_dir) / f"mcp_{session_stamp}.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def for_server(self, server_name: str) -> ServerHook:
        def hook(direction: str, message: dict[str, Any]) -> None:
            self.record(server_name, direction, message)
        return hook

    def record(self, server_name: str, direction: str, message: dict[str, Any]) -> None:
        interaction = {
            "time": datetime.now().isoformat(timespec="milliseconds"),
            "server": server_name,
            "direction": direction,
            "kind": classify_message(message),
            "method": message.get("method", ""),
            "id": message.get("id", ""),
            "payload": message,
        }
        self.interactions.append(interaction)
        with self.log_file.open("a", encoding="utf-8") as log:
            log.write(json.dumps(interaction, ensure_ascii=False) + "\n")

    def show(self, limit: int | None = None) -> None:
        rows = self.interactions[-limit:] if limit else self.interactions
        table = Table(title="MCP interaction log", show_lines=False)
        table.add_column("Time", style="dim")
        table.add_column("Server", style="cyan")
        table.add_column("Flow")
        table.add_column("Kind")
        table.add_column("Method / id")
        for interaction in rows:
            client_to_server = interaction["direction"] == "send"
            flow = "host → server" if client_to_server else "host ← server"
            label = interaction["method"] or f"id={interaction['id']}"
            table.add_row(
                interaction["time"].split("T")[1],
                interaction["server"],
                flow,
                interaction["kind"],
                label,
            )
        self.console.print(table)
