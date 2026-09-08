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

## Current tools

- `ping(message?)`: returns the supplied message, or `pong` by default.
- `workspace_info()`: returns the active workspace root and security limits.
- `list_files(path?, recursive?, max_entries?)`: lists allowed workspace files
  and directories using relative paths.
- `read_file(path, encoding?)`: reads one allowed text file and returns its
  content and metadata.

The current filesystem tools are read-only. They do not modify workspace files,
skip protected paths, and `read_file` enforces the configured file-size limit.


## Workspace security policy

The server now has a reusable filesystem boundary for future tools:

- `LOCAL_AI_WORKSPACE_ROOT`: allowed workspace root. Defaults to the process
  working directory; hosts should set this explicitly.
- `LOCAL_AI_MAX_FILE_BYTES`: maximum file size for future reads. Defaults to
  `1048576` bytes.

The policy rejects absolute paths, path traversal outside the root, symlinks
that resolve outside the root, common dependency/build directories, dotenv
files, and private-key file extensions. Future filesystem tools must call
`WorkspacePolicy.resolve_path()` before accessing a path.
