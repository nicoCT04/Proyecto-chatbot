# syntax=docker/dockerfile:1
#
# Image for the web chatbot host. It bundles:
#   - the FastAPI backend + the built React front-end
#   - Node (npx) so the official Filesystem MCP server can run as a subprocess
#   - git + the official Git MCP server
# The sugarmill server runs in its own container (see Dockerfile.sugarmill) and
# is reached over HTTP, exactly like a remote MCP server.

# ---- Stage 1: build the React front-end ----
FROM node:22-bookworm-slim AS webbuild
WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# ---- Stage 2: Python host that also drives the official MCP servers ----
FROM python:3.13-slim-bookworm

# git is needed by the official Git MCP server and the workspace demo repo.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Bring Node + npm/npx over from the official node image so the Filesystem MCP
# server can be launched with npx, and pre-install it for deterministic runs.
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && npm install -g @modelcontextprotocol/server-filesystem

WORKDIR /app

COPY requirements.txt requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-web.txt

COPY src/ ./src/
COPY config/ ./config/
COPY --from=webbuild /web/dist ./web/dist

# Bind address, port and the docker server map (sugarmill over HTTP).
ENV WEB_HOST=0.0.0.0 \
    WEB_PORT=8080 \
    MCP_SERVERS_CONFIG=config/servers.docker.json

EXPOSE 8080
CMD ["python", "-m", "src.web"]
