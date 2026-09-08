"""Workspace boundary and sensitive-path protections.

All future filesystem tools should resolve user-provided paths through
``WorkspacePolicy`` before touching the filesystem.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path


class WorkspaceSecurityError(ValueError):
    """Raised when a path violates the workspace security policy."""


DEFAULT_BLOCKED_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
    }
)

DEFAULT_BLOCKED_PATTERNS = (".env", ".env.*")
DEFAULT_BLOCKED_EXTENSIONS = frozenset({".pem", ".key", ".p12", ".pfx"})


@dataclass(frozen=True)
class WorkspacePolicy:
    """Defines the only part of the local filesystem the MCP may access."""

    root: Path
    max_file_bytes: int = 1_048_576
    blocked_names: frozenset[str] = field(default=DEFAULT_BLOCKED_NAMES)
    blocked_patterns: tuple[str, ...] = DEFAULT_BLOCKED_PATTERNS
    blocked_extensions: frozenset[str] = field(
        default=DEFAULT_BLOCKED_EXTENSIONS
    )

    def __post_init__(self) -> None:
        resolved_root = self.root.expanduser().resolve(strict=True)
        if not resolved_root.is_dir():
            raise WorkspaceSecurityError(
                f"Workspace root is not a directory: {resolved_root}"
            )
        if self.max_file_bytes <= 0:
            raise WorkspaceSecurityError("max_file_bytes must be greater than zero")
        object.__setattr__(self, "root", resolved_root)

    @classmethod
    def from_environment(cls) -> "WorkspacePolicy":
        """Build a policy from environment variables.

        ``LOCAL_AI_WORKSPACE_ROOT`` defaults to the process working directory.
        Hosts should set it explicitly to the VS Code workspace.
        """

        root = Path(os.environ.get("LOCAL_AI_WORKSPACE_ROOT", Path.cwd()))
        max_file_bytes = int(
            os.environ.get("LOCAL_AI_MAX_FILE_BYTES", str(1_048_576))
        )
        return cls(root=root, max_file_bytes=max_file_bytes)

    def resolve_path(
        self,
        relative_path: str,
        *,
        must_exist: bool = False,
        expect_file: bool = False,
    ) -> Path:
        """Resolve and validate a path relative to the workspace root."""

        if not relative_path or not relative_path.strip():
            raise WorkspaceSecurityError("Path must not be empty")

        requested = Path(relative_path)
        if requested.is_absolute():
            raise WorkspaceSecurityError("Absolute paths are not allowed")

        candidate = (self.root / requested).resolve(strict=False)
        if not candidate.is_relative_to(self.root):
            raise WorkspaceSecurityError("Path escapes the workspace root")

        self._check_sensitive_path(candidate)

        if must_exist and not candidate.exists():
            raise FileNotFoundError(relative_path)
        if expect_file and candidate.exists() and not candidate.is_file():
            raise WorkspaceSecurityError("Expected a regular file")

        return candidate

    def validate_file_size(self, path: Path) -> None:
        """Reject files larger than the configured read limit."""

        size = path.stat().st_size
        if size > self.max_file_bytes:
            raise WorkspaceSecurityError(
                f"File exceeds the {self.max_file_bytes}-byte limit"
            )

    def _check_sensitive_path(self, path: Path) -> None:
        relative_parts = path.relative_to(self.root).parts
        for part in relative_parts:
            normalized = part.casefold()
            if normalized in self.blocked_names:
                raise WorkspaceSecurityError(
                    f"Access to protected path is not allowed: {part}"
                )
            if any(
                fnmatch.fnmatchcase(normalized, pattern.casefold())
                for pattern in self.blocked_patterns
            ):
                raise WorkspaceSecurityError(
                    f"Access to protected path is not allowed: {part}"
                )

        if path.suffix.casefold() in {
            extension.casefold() for extension in self.blocked_extensions
        }:
            raise WorkspaceSecurityError(
                f"Access to protected file type is not allowed: {path.suffix}"
            )
