"""Minimal local MCP server.

The server uses stdio so an MCP host can launch it as a local subprocess.
Keep stdout reserved for the MCP protocol; diagnostic messages belong in logs.
"""

from mcp.server import MCPServer

from .security import WorkspacePolicy
from .workspace import (
    list_workspace_files,
    read_workspace_file,
    workspace_info as build_workspace_info,
)


mcp = MCPServer(
    "local-ai-mcp",
    version="0.1.0",
    instructions=(
        "Local workspace MCP server. Read-only workspace inspection is "
        "available; filesystem writes will require explicit future tools."
    ),
)

# Central policy used by all future filesystem tools.
# The current server does not expose a filesystem tool yet.
workspace_policy = WorkspacePolicy.from_environment()


@mcp.tool()
def ping(message: str = "pong") -> str:
    """Confirm that the local MCP server is running."""

    return message


@mcp.tool()
def workspace_info() -> dict:
    """Return the active workspace root and filesystem security limits."""

    return build_workspace_info(workspace_policy)


@mcp.tool()
def list_files(
    path: str = ".",
    recursive: bool = False,
    max_entries: int = 200,
) -> list[dict]:
    """List allowed files and directories using workspace-relative paths."""

    return list_workspace_files(
        workspace_policy,
        path=path,
        recursive=recursive,
        max_entries=max_entries,
    )


@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> dict:
    """Read one allowed text file using a workspace-relative path."""

    return read_workspace_file(
        workspace_policy,
        path,
        encoding=encoding,
    )


def main() -> None:
    """Run the MCP server over stdin/stdout."""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
