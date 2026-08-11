from __future__ import annotations

import json
import subprocess
import threading
from collections import deque
from typing import Any, Callable

MessageHandler = Callable[[dict[str, Any]], None]

TRANSPORT_CLOSED = {"__transport__": "closed"}


class StdioTransport:
    def __init__(self, command: str, args: list[str] | None = None,
                 env: dict[str, str] | None = None,
                 cwd: str | None = None) -> None:
        self.command = command
        self.args = args or []
        self.env = env
        self.cwd = cwd

        self.process: subprocess.Popen[str] | None = None
        self.message_handler: MessageHandler | None = None
        self.recent_stderr: deque[str] = deque(maxlen=50)

        self._write_lock = threading.Lock()
        self._closed = False

    def set_message_handler(self, handler: MessageHandler) -> None:
        self.message_handler = handler

    def start(self) -> None:
        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            cwd=self.cwd,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def send(self, message: dict[str, Any]) -> None:
        line = json.dumps(message, ensure_ascii=False) + "\n"
        with self._write_lock:
            self.process.stdin.write(line)
            self.process.stdin.flush()

    def close(self) -> None:
        self._closed = True
        if self.process is None:
            return
        self.process.stdin.close()
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def _read_stdout(self) -> None:
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self.recent_stderr.append(f"[non-JSON stdout] {line}")
                continue
            if self.message_handler is not None:
                self.message_handler(message)
        if not self._closed and self.message_handler is not None:
            self.message_handler(TRANSPORT_CLOSED)

    def _read_stderr(self) -> None:
        for line in self.process.stderr:
            self.recent_stderr.append(line.rstrip("\n"))
