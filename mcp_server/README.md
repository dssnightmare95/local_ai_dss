# Local AI MCP Server

Minimal MCP server for the local project. It runs locally over `stdio`, which
allows an MCP host such as VS Code or a future local agent to launch it as a
child process.

## Requirements

- Python 3.10 or newer
- `pip` or `uv`

## Install

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Or, without a virtual environment:

```powershell
python -m pip install -e .
```

## Run

The server waits for MCP messages on standard input and writes protocol
messages to standard output:

```powershell
python -m local_ai_mcp.server
```

It is normal for the command to appear idle. An MCP host must speak the
protocol to it.

## Current tool

- `ping(message?)`: returns the supplied message, or `pong` by default.

The server deliberately does not read or modify workspace files yet. Those
permissions will be added in separate steps.
