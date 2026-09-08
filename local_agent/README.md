# Local AI Agent

This package contains the MCP client and will later contain the agent loop
that connects MCP tools to Ollama/Gemma.

## Install

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

## Use

```powershell
python -m local_ai_agent.client list-tools
python -m local_ai_agent.client call-tool workspace_info
python -m local_ai_agent.client call-tool list_files --arguments '{"recursive":true}'
python -m local_ai_agent.client call-tool read_file --arguments '{"path":"README.md"}'
```

The client launches `mcp_server` locally over `stdio` and passes the workspace
root explicitly to it.
