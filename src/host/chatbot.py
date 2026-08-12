from __future__ import annotations

import os

from dotenv import load_dotenv
from rich.console import Console

from .llm import LLMChat

SYSTEM_PROMPT = (
    "You are a helpful assistant running inside a console chatbot for a "
    "networking course. Answer clearly and keep track of the conversation."
)


class Chatbot:
    def __init__(self, api_key: str, model: str, console: Console | None = None) -> None:
        self.console = console or Console()
        self.chat = LLMChat(api_key, model, SYSTEM_PROMPT)

    def run(self) -> None:
        self.console.print("[bold green]MCP chatbot[/bold green] — type 'exit' to quit.\n")
        while True:
            user_message = self.console.input("[bold cyan]you >[/bold cyan] ")
            if user_message.strip().lower() in {"exit", "quit"}:
                break
            reply = self.chat.ask(user_message)
            self.console.print(f"[bold magenta]bot >[/bold magenta] {reply}\n")


def start() -> None:
    load_dotenv()
    console = Console()
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        console.print("[red]Missing GEMINI_API_KEY. Copy .env.example to .env and set it.[/red]")
        return
    Chatbot(api_key, model, console).run()
