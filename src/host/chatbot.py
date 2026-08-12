from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from .llm import LLMChat
from .logger import MCPLogger
from .servers import ServerManager, load_server_configs

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ensure_git_repo(workspace: Path) -> None:
    if not (workspace / ".git").exists():
        subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)


def build_system_prompt(workspace: str) -> str:
    return (
        "You are a helpful assistant running inside a console chatbot for a "
        "networking course. You can use tools from connected MCP servers "
        "(filesystem and git). You operate inside this workspace directory: "
        f"{workspace}. When a filesystem or git tool needs a path or repository, "
        "use that directory unless the user says otherwise. Keep answers concise "
        "and keep track of the conversation."
    )


class Chatbot:
    def __init__(self, api_key: str, model: str, workspace: str,
                 console: Console | None = None) -> None:
        self.console = console or Console()
        self.logger = MCPLogger(console=self.console)
        self.servers = ServerManager(self.logger)
        self.chat = LLMChat(api_key, model, build_system_prompt(workspace))

    def start_servers(self, server_configs: list[dict]) -> None:
        for config in server_configs:
            self.console.print(f"[dim]connecting to {config['name']}...[/dim]")
        self.servers.start(server_configs)
        tool_count = len(self.servers.tool_owner)
        connected = ", ".join(client.name for client in self.servers.clients)
        self.console.print(f"[green]connected:[/green] {connected} "
                           f"([bold]{tool_count}[/bold] tools available)\n")

    def run(self) -> None:
        tools = self.servers.tool_definitions()
        self.console.print("[bold green]MCP chatbot[/bold green] — "
                           "type 'exit' to quit, '/log' to see MCP traffic.\n")
        while True:
            user_message = self.console.input("[bold cyan]you >[/bold cyan] ")
            command = user_message.strip().lower()
            if command in {"exit", "quit"}:
                break
            if command == "/log":
                self.logger.show()
                continue
            reply = self.chat.ask(user_message, tools=tools,
                                  run_tool=self.servers.run_tool)
            self.console.print(f"[bold magenta]bot >[/bold magenta] {reply}\n")

    def close(self) -> None:
        self.servers.close()


def start() -> None:
    load_dotenv()
    console = Console()
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
    if not api_key:
        console.print("[red]Missing GEMINI_API_KEY. Copy .env.example to .env and set it.[/red]")
        return

    workspace = PROJECT_ROOT / "workspace"
    workspace.mkdir(exist_ok=True)
    ensure_git_repo(workspace)
    server_configs = load_server_configs(
        PROJECT_ROOT / "config" / "servers.json", str(workspace), sys.executable)

    bot = Chatbot(api_key, model, str(workspace), console)
    bot.start_servers(server_configs)
    try:
        bot.run()
    finally:
        bot.close()
