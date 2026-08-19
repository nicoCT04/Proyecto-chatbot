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

## Interaction logging

Every message to and from the MCP servers is recorded in memory and appended to
`logs/mcp_<timestamp>.jsonl` with the full JSON-RPC payload. `/log` prints a
summary table during the session.

## Academic integrity

Generative AI was used following UVG's AI-usage guidelines. Third-party code used
as reference is cited in comments where applicable.
