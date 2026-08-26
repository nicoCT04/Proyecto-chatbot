from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

MessageHandler = Callable[[dict[str, Any]], None]


class HttpTransport:
    def __init__(self, url: str, timeout: float = 30.0) -> None:
        self.url = url
        self.timeout = timeout
        self.message_handler: MessageHandler | None = None

    def set_message_handler(self, handler: MessageHandler) -> None:
        self.message_handler = handler

    def start(self) -> None:
        pass

    def send(self, message: dict[str, Any]) -> None:
        data = json.dumps(message, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.url, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as reply:
            body = reply.read()
        if body and self.message_handler is not None:
            self.message_handler(json.loads(body))

    def close(self) -> None:
        pass
