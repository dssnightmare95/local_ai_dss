"""Minimal MCP client for the local workspace server.

This is intentionally separate from the future Ollama agent. It only handles
the MCP connection lifecycle, tool discovery, and tool calls.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from mcp import Client, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass(frozen=True)
class LocalServerConfig:
    """Parameters required to launch the local MCP server."""

    workspace_root: Path
    server_dir: Path

    @property
    def source_dir(self) -> Path:
        return self.server_dir / "src"

    def parameters(self) -> StdioServerParameters:
        """Build secure stdio subprocess parameters for the server."""

        workspace_root = self.workspace_root.expanduser().resolve(strict=True)
        server_dir = self.server_dir.expanduser().resolve(strict=True)

        return StdioServerParameters(
            command=sys.executable,
            args=["-m", "local_ai_mcp.server"],
            cwd=server_dir,
            env={
                "LOCAL_AI_WORKSPACE_ROOT": str(workspace_root),
                # Supports local development before the server package is installed.
                "PYTHONPATH": str(self.source_dir.resolve(strict=True)),
            },
        )


class LocalMCPClient:
    """Small high-level client for the local MCP server."""

    def __init__(self, config: LocalServerConfig) -> None:
        self.config = config

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[Client]:
        """Launch the server and yield a connected MCP client."""

        async with Client(stdio_client(self.config.parameters())) as client:
            yield client

    async def list_tools(self) -> list[dict[str, Any]]:
        """Discover tools exposed by the server."""

        async with self.connect() as client:
            result = await client.list_tools()
            return [_model_to_dict(tool) for tool in result.tools]

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call one server tool and return its protocol result."""

        async with self.connect() as client:
            result = await client.call_tool(name, arguments or {})
            return _model_to_dict(result)


def _model_to_dict(value: Any) -> dict[str, Any]:
    """Convert an SDK model to JSON-compatible data."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    raise TypeError(f"Unsupported MCP result type: {type(value)!r}")


def _default_server_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "mcp_server"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local MCP client")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace passed to the server (default: current directory)",
    )
    parser.add_argument(
        "--server-dir",
        type=Path,
        default=_default_server_dir(),
        help="Directory containing the mcp_server project",
    )

    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-tools", help="List tools exposed by the server")

    call_parser = commands.add_parser("call-tool", help="Call one server tool")
    call_parser.add_argument("name", help="Tool name")
    call_parser.add_argument(
        "--arguments",
        default="{}",
        help="Tool arguments as a JSON object",
    )
    return parser


async def _run(args: argparse.Namespace) -> None:
    config = LocalServerConfig(
        workspace_root=args.workspace_root,
        server_dir=args.server_dir,
    )
    client = LocalMCPClient(config)

    if args.command == "list-tools":
        result = await client.list_tools()
    else:
        arguments = json.loads(args.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("--arguments must contain a JSON object")
        result = await client.call_tool(args.name, arguments)

    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    args = _build_parser().parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
