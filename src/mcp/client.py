from __future__ import annotations

import itertools
import threading
from concurrent.futures import Future
from typing import Any, Callable

from . import protocol
from .protocol import McpError
from .transport import StdioTransport, TRANSPORT_CLOSED

TrafficHook = Callable[[str, dict[str, Any]], None]


class MCPClient:
    def __init__(self, name: str, transport: StdioTransport,
                 request_timeout: float = 30.0,
                 on_message: TrafficHook | None = None) -> None:
        self.name = name
        self.transport = transport
        self.request_timeout = request_timeout
        self.on_message = on_message

        self.server_info: dict[str, Any] = {}
        self.server_capabilities: dict[str, Any] = {}
        self.tools: list[dict[str, Any]] = []

        self._next_id = itertools.count(1)
        self._pending_requests: dict[int | str, Future[Any]] = {}
        self._lock = threading.Lock()

        transport.set_message_handler(self._on_incoming_message)

    def connect(self) -> None:
        self.transport.start()
        handshake = self._send_request("initialize", {
            "protocolVersion": protocol.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "mcp-chatbot-host", "version": "0.1.0"},
        })
        self.server_info = handshake.get("serverInfo", {})
        self.server_capabilities = handshake.get("capabilities", {})
        self._send_notification("notifications/initialized")

    def close(self) -> None:
        self.transport.close()
        with self._lock:
            for request in self._pending_requests.values():
                if not request.done():
                    request.set_exception(RuntimeError("connection closed"))
            self._pending_requests.clear()

    def list_tools(self) -> list[dict[str, Any]]:
        discovered_tools: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            page = self._send_request("tools/list", params)
            discovered_tools.extend(page.get("tools", []))
            cursor = page.get("nextCursor")
            if not cursor:
                break
        self.tools = discovered_tools
        return discovered_tools

    def call_tool(self, name: str,
                  arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {},
        })

    def _send_request(self, method: str,
                      params: dict[str, Any] | None = None) -> Any:
        request_id = next(self._next_id)
        response = Future()
        with self._lock:
            self._pending_requests[request_id] = response
        message = protocol.make_request(request_id, method, params)
        self._forward_to_hook("send", message)
        self.transport.send(message)
        try:
            return response.result(timeout=self.request_timeout)
        except TimeoutError:
            with self._lock:
                self._pending_requests.pop(request_id, None)
            raise TimeoutError(f"'{method}' timed out after {self.request_timeout}s")

    def _send_notification(self, method: str,
                           params: dict[str, Any] | None = None) -> None:
        message = protocol.make_notification(method, params)
        self._forward_to_hook("send", message)
        self.transport.send(message)

    def _on_incoming_message(self, message: dict[str, Any]) -> None:
        if message is TRANSPORT_CLOSED:
            self.close()
            return

        self._forward_to_hook("recv", message)

        if protocol.is_response(message):
            self._resolve_pending_request(message)
        elif protocol.is_request(message):
            self._answer_server_request(message)

    def _resolve_pending_request(self, message: dict[str, Any]) -> None:
        with self._lock:
            waiting_request = self._pending_requests.pop(message.get("id"), None)
        if waiting_request is None:
            return
        if "error" in message:
            error = message["error"]
            waiting_request.set_exception(McpError(
                error.get("code", protocol.INTERNAL_ERROR),
                error.get("message", "unknown error"),
                error.get("data"),
            ))
        else:
            waiting_request.set_result(message.get("result"))

    def _answer_server_request(self, message: dict[str, Any]) -> None:
        request_id = message["id"]
        if message.get("method") == "ping":
            self.transport.send(protocol.make_result(request_id, {}))
        else:
            self.transport.send(protocol.make_error(
                request_id, protocol.METHOD_NOT_FOUND,
                f"method not found: {message.get('method')}"))

    def _forward_to_hook(self, direction: str, message: dict[str, Any]) -> None:
        if self.on_message is not None:
            self.on_message(direction, message)
