# MCP Chatbot Host

A console chatbot that acts as an **MCP host**, coordinating several MCP clients
that talk to local and remote **MCP servers**. Built for CC3067 *Redes* (Project 1,
Universidad del Valle de Guatemala).

The **Model Context Protocol (MCP)** layer is implemented **by hand over JSON-RPC 2.0**
— no MCP SDK (FastMCP, official SDK, etc.) is used. Only the JSON-RPC framing and
message exchange written in this repo drive the communication with MCP servers.

## Features

- [ ] **(1)** Connects to an LLM through its API (Google Gemini).
- [ ] **(2)** Keeps conversation context within a session.
- [ ] **(3)** Logs every request/response exchanged with MCP servers.
- [ ] **(4)** Uses the official **Filesystem** and **Git** MCP servers.
- [ ] **(5)** Ships a **custom local MCP server** for an industry use case.
- [ ] **(6)** Remote deployment of the custom server *(second delivery)*.
- [ ] **(7)** Wireshark traffic analysis *(second delivery)*.

## Requirements

- Python 3.14+
- Node.js + npx (to run the official Filesystem/Git MCP servers)
- A Google Gemini API key (free tier, no card required — https://aistudio.google.com/apikey)

## Installation

```bash
git clone https://github.com/nicoCT04/Proyecto-chatbot.git
cd Proyecto-chatbot

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env and set GEMINI_API_KEY
```

## Usage

```bash
python -m src.main
```

> Detailed usage, available MCP tools and example scenarios will be documented
> as each module lands.

## Project structure

```
src/
  main.py       # TUI entry point
  host/         # chat loop, LLM connection, session context, MCP logging
  mcp/          # hand-written MCP protocol (JSON-RPC 2.0 over stdio)
  servers/      # custom MCP server(s)
config/         # MCP server configuration
logs/           # MCP interaction logs
```

## Academic integrity

Generative AI was used following UVG's AI-usage guidelines. Third-party code used
as reference is cited in comments where applicable.
