"""Minimal local MCP server.

The server uses stdio so an MCP host can launch it as a local subprocess.
Keep stdout reserved for the MCP protocol; diagnostic messages belong in logs.
"""

from mcp.server import MCPServer


mcp = MCPServer(
    "local-ai-mcp",
    version="0.1.0",
    instructions=(
        "Local workspace MCP server. This initial version only exposes a "
        "connectivity check; filesystem tools will be added incrementally."
    ),
)


@mcp.tool()
def ping(message: str = "pong") -> str:
    """Confirm that the local MCP server is running."""

    return message


def main() -> None:
    """Run the MCP server over stdin/stdout."""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
