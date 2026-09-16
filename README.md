# MCP Chatbot Host

A console chatbot that acts as an **MCP host**, coordinating several MCP clients
that talk to local **MCP servers**. Built for CC3067 *Redes* (Project 1,
Universidad del Valle de Guatemala).

The **Model Context Protocol (MCP)** layer is implemented **by hand over
JSON-RPC 2.0** — no MCP SDK (FastMCP, official SDK, etc.) is used. Both the
client and our own server speak the protocol through the JSON-RPC framing and
message exchange written in this repository (`src/mcp/`).

## Features

- [x] **(1)** Connects to an LLM through its API (Google Gemini).
- [x] **(2)** Keeps conversation context within a session.
- [x] **(3)** Logs every request/response exchanged with MCP servers (`/log`).
- [x] **(4)** Uses the official **Filesystem** and **Git** MCP servers.
- [x] **(5)** Ships a **custom local MCP server** (`sugarmill`) for a sugar-mill use case.
- [ ] **(6)** Remote deployment of the custom server *(second delivery)*.
- [ ] **(7)** Wireshark traffic analysis *(second delivery)*.
- [x] **(extra)** Optional **Web UI** (React + FastAPI) with a live JSON-RPC log — see [Web UI](#web-ui-optional-extra).

## Architecture

```
you ──▶ Host (chatbot) ──▶ LLM (Gemini) decides which tool to use
                  │
                  ├─ MCP client ─▶ Filesystem server (npx, official)
                  ├─ MCP client ─▶ Git server (python, official)
                  └─ MCP client ─▶ sugarmill server (ours, hand-written)
                  │
                  └─ Logger records every JSON-RPC message
```

```
src/
  main.py            # entry point
  host/
    chatbot.py       # chat loop, session context, workspace, /log command
    llm.py           # Gemini connection + tool-use loop
    logger.py        # MCP interaction log (console + logs/*.jsonl)
    servers.py       # starts MCP servers, routes tool calls, sanitizes schemas
  mcp/
    protocol.py      # JSON-RPC 2.0 message primitives
    transport.py     # stdio transport (subprocess + framing)
    client.py        # MCP client: initialize, tools/list, tools/call
    server.py        # MCP server base (used by our sugarmill server)
  servers/
    sugarmill/       # our custom MCP server (see its own README)
config/servers.json  # which MCP servers to launch
logs/                # MCP interaction logs
workspace/           # sandbox where the chatbot creates files/repos
```

## Requirements

- Python 3.14+
- Node.js + `npx` (runs the official Filesystem MCP server)
- A Google Gemini API key — free tier, no card required
  (https://aistudio.google.com/apikey)

## Installation

```bash
git clone https://github.com/nicoCT04/Proyecto-chatbot.git
cd Proyecto-chatbot

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env and set GEMINI_API_KEY
```

> `requirements.txt` also installs `mcp-server-git` (the official Git server) and
> pins `mcp<2`, which is the runtime that server depends on. Our own code never
> imports these — they run as external subprocesses that we drive over JSON-RPC.

## Usage

```bash
python -m src.main
```

Commands inside the chat:

- type a message to talk to the assistant
- `/log` — show every JSON-RPC message exchanged with the MCP servers
- `exit` / `quit` — leave

## Run everything with Docker

The whole system comes up with a single command. It starts the custom
`sugarmill` server over **HTTP** (acting as the "remote" server) and the web
chatbot host, which additionally launches the Filesystem and Git servers inside
its own container:

```bash
cp .env.example .env      # set GEMINI_API_KEY
docker compose up --build
```

Then open http://localhost:8080. Ports `8080` (web) and `8000` (sugarmill HTTP)
are published on the host, so Wireshark can capture the host ⇄ server JSON-RPC
traffic. Generated files and MCP logs are bind-mounted to `./workspace` and
`./logs`.

| Service | Image | Port | Role |
|---|---|---|---|
| `sugarmill` | `Dockerfile.sugarmill` | 8000 | custom MCP server over HTTP |
| `web` | `Dockerfile` | 8080 | chatbot host + React UI + filesystem/git servers |

The `sugarmill` image is the same artifact used for cloud deployment
(feature 6): it honours `$PORT`, so a cloud host can run it unchanged.

## Example scenarios

**General question + session context (features 1 & 2)**

```
you > Who was Alan Turing?
you > When was he born?          # understands it still refers to Turing
```

**Filesystem + Git (feature 4)**

```
you > Create a README.md in the workspace describing a demo project, then stage
      it and commit it with the message "Initial commit", and show me the git log.
```

**Sugar mill — harvest planning + quality payment (feature 5)**

```
you > List the fields that are ready to cut.
you > I have 20000 tons of milling capacity this week — what should I cut?
      Then write the plan to zafra_plan.md and commit it as "weekly harvest plan".
you > For field F-14, register a lab sample with pol 14.2 and brix 16.7, then
      compute the payment for 950 tons at 450 per ton.
```

The last examples chain **three servers** (sugarmill + filesystem + git) in a
single conversation. Run `/log` afterwards to see the JSON-RPC traffic.

## MCP servers

| Server | Type | Launch | Purpose |
|---|---|---|---|
| `filesystem` | official | `npx @modelcontextprotocol/server-filesystem` | read/write files in the workspace |
| `git` | official | `python -m mcp_server_git` | git status/add/commit/log |
| `sugarmill` | ours | `python -m src.servers.sugarmill` | harvest planning and cane payment |

The custom server is documented in
[`src/servers/sugarmill/README.md`](src/servers/sugarmill/README.md)
(tools, parameters, formulas and JSON-RPC examples).

## Web UI (optional, extra)

Besides the console, the project ships an optional **web chatbot** (React
front-end + FastAPI backend) that drives the *same* MCP host. It shows the
conversation on the left and the **live JSON-RPC traffic** with the MCP servers
on the right (feature 3, made visual), with per-message payloads you can expand.
The design follows HCI guidelines (calm agricultural palette, clear hierarchy,
keyboard-first composer, visible feedback states).

```
web/                 # React (Vite) front-end
src/web/             # FastAPI backend (REST API over the MCP host)
```

Install and run (in two terminals, from the repo root):

```bash
# backend (serves the API on :8080; also serves web/dist if it was built)
pip install -r requirements-web.txt
python -m src.web

# frontend
cd web
npm install
npm run dev          # dev server on http://localhost:5173 (proxies /api to :8080)
```

Open http://localhost:5173 during development. For a single-origin production
build, run `npm run build` inside `web/` and then just `python -m src.web` —
FastAPI serves the compiled app from `web/dist` at http://localhost:8080.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/chat` | send a message; returns the reply and the JSON-RPC log delta |
| `GET` | `/api/servers` | connected servers, tools and model |
| `GET` | `/api/log` | the full MCP interaction log |
| `POST` | `/api/reset` | clear the conversation history |

The web layer is a plain web framework — it is **not** an MCP SDK. The protocol
is still implemented by hand in `src/mcp/`.

## Interaction logging

Every message to and from the MCP servers is recorded in memory and appended to
`logs/mcp_<timestamp>.jsonl` with the full JSON-RPC payload. `/log` prints a
summary table during the session.

## Academic integrity

Generative AI was used following UVG's AI-usage guidelines. Third-party code used
as reference is cited in comments where applicable.
