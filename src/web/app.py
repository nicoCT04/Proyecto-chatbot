from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .session import WebChatSession

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "web" / "dist"

session: WebChatSession | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global session
    session = WebChatSession()
    session.start()
    try:
        yield
    finally:
        session.close()


app = FastAPI(title="MCP Chatbot Web", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ModelRequest(BaseModel):
    model: str


def _require_session() -> WebChatSession:
    if session is None:
        raise HTTPException(status_code=503, detail="session not ready")
    return session


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict:
    active = _require_session()
    text = request.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty message")
    try:
        return active.send(text)
    except Exception as failure:
        raise HTTPException(status_code=502, detail=str(failure))


@app.get("/api/log")
def get_log() -> dict:
    return {"log": _require_session().full_log()}


@app.get("/api/servers")
def get_servers() -> dict:
    return _require_session().server_summary()


@app.get("/api/usage")
def get_usage() -> dict:
    return _require_session().usage()


@app.post("/api/model")
def set_model(request: ModelRequest) -> dict:
    active = _require_session()
    try:
        active.set_model(request.model)
    except ValueError as failure:
        raise HTTPException(status_code=400, detail=str(failure))
    return {"model": request.model}


@app.post("/api/reset")
def reset() -> dict:
    _require_session().reset()
    return {"ok": True}


@app.get("/api/health")
def health() -> dict:
    return {"ok": session is not None}


if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
