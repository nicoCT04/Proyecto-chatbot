from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB_PORT", "8080"))
    uvicorn.run("src.web.app:app", host=host, port=port, reload=False)
