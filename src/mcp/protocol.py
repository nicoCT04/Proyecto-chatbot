from __future__ import annotations

from typing import Any

JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2025-06-18"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class McpError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.data = data


def make_request(request_id: int | str, method: str,
                 params: dict[str, Any] | None = None) -> dict[str, Any]:
    request = {"jsonrpc": JSONRPC_VERSION, "id": request_id, "method": method}
    if params is not None:
        request["params"] = params
    return request


def make_notification(method: str,
                      params: dict[str, Any] | None = None) -> dict[str, Any]:
    notification = {"jsonrpc": JSONRPC_VERSION, "method": method}
    if params is not None:
        notification["params"] = params
    return notification


def make_result(request_id: int | str, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def make_error(request_id: int | str | None, code: int, message: str,
               data: Any = None) -> dict[str, Any]:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def is_response(message: dict[str, Any]) -> bool:
    return "id" in message and ("result" in message or "error" in message)


def is_notification(message: dict[str, Any]) -> bool:
    return "method" in message and "id" not in message


def is_request(message: dict[str, Any]) -> bool:
    return "method" in message and "id" in message
