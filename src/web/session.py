"""Web chat session: a thin, thread-safe wrapper around the same MCP host the
console chatbot uses (LLM + MCP servers + interaction logger).

The console app (`src/host/chatbot.py`) and this module share the *exact* same
building blocks, so the web UI is a real front-end over the identical host, not
a second implementation of the protocol.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from ..host.chatbot import PROJECT_ROOT, build_system_prompt, ensure_git_repo
from ..host.llm import LLMChat
from ..host.logger import MCPLogger
from ..host.servers import ServerManager, load_server_configs


class WebChatSession:
    """One long-lived conversation for the web UI.

    Holds the LLM history, the connected MCP servers and the interaction log,
    guarding calls with a lock so overlapping HTTP requests never drive the
    stdio subprocesses concurrently.
    """

    def __init__(self) -> None:
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Copy .env.example to .env and set it.")
        model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

        self.workspace = PROJECT_ROOT / "workspace"
        self.workspace.mkdir(exist_ok=True)
        ensure_git_repo(self.workspace)

        config_name = os.environ.get("MCP_SERVERS_CONFIG", "config/servers.json")
        server_configs = load_server_configs(
            PROJECT_ROOT / config_name, str(self.workspace), sys.executable)

        # console=None keeps the host quiet: the web log is served over HTTP.
        self.logger = MCPLogger()
        self.servers = ServerManager(self.logger, console=None)
        self.chat = LLMChat(api_key, model, build_system_prompt(str(self.workspace)))

        self._lock = threading.Lock()
        self._started = False
        self.model = model

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            config_name = os.environ.get("MCP_SERVERS_CONFIG", "config/servers.json")
            server_configs = load_server_configs(
                PROJECT_ROOT / config_name, str(self.workspace), sys.executable)
            self.servers.start(server_configs)
            self._started = True

    def close(self) -> None:
        with self._lock:
            if self._started:
                self.servers.close()
                self._started = False

    # --- API used by the FastAPI routes ---------------------------------

    def send(self, message: str) -> dict[str, Any]:
        """Run one user turn and return the reply plus the MCP log it produced."""
        tools = self.servers.tool_definitions()
        with self._lock:
            checkpoint = len(self.logger.interactions)
            reply = self.chat.ask(message, tools=tools, run_tool=self.servers.run_tool)
            new_log = self.logger.interactions[checkpoint:]
        return {"reply": reply, "log": [_public_entry(item) for item in new_log]}

    def full_log(self) -> list[dict[str, Any]]:
        return [_public_entry(item) for item in self.logger.interactions]

    def server_summary(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "servers": [
                {
                    "name": client.name,
                    "info": client.server_info,
                    "tools": [t["name"] for t in client.tools],
                }
                for client in self.servers.clients
            ],
            "tool_count": len(self.servers.tool_owner),
        }

    def reset(self) -> None:
        with self._lock:
            self.chat.history.clear()


def _public_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Shape a logger interaction for the browser (drop nothing sensitive, but
    keep it flat and JSON-friendly)."""
    return {
        "time": entry["time"],
        "server": entry["server"],
        "direction": entry["direction"],
        "kind": entry["kind"],
        "method": entry["method"],
        "id": entry["id"],
        "payload": entry["payload"],
    }
