"""Read-only workspace operations built on top of the security policy."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .security import WorkspacePolicy, WorkspaceSecurityError


DEFAULT_MAX_ENTRIES = 200
MAX_ALLOWED_ENTRIES = 1_000


def workspace_info(policy: WorkspacePolicy) -> dict[str, Any]:
    """Return the active workspace boundary and limits."""

    return {
        "root": str(policy.root),
        "max_file_bytes": policy.max_file_bytes,
        "blocked_names": sorted(policy.blocked_names),
        "blocked_patterns": list(policy.blocked_patterns),
        "blocked_extensions": sorted(policy.blocked_extensions),
    }


def list_workspace_files(
    policy: WorkspacePolicy,
    path: str = ".",
    recursive: bool = False,
    max_entries: int = DEFAULT_MAX_ENTRIES,
) -> list[dict[str, Any]]:
    """List allowed files and directories below a workspace-relative path."""

    if not 1 <= max_entries <= MAX_ALLOWED_ENTRIES:
        raise ValueError(
            f"max_entries must be between 1 and {MAX_ALLOWED_ENTRIES}"
        )

    root = policy.resolve_path(path, must_exist=True)
    if not root.is_dir():
        raise WorkspaceSecurityError("The requested path is not a directory")

    entries: list[dict[str, Any]] = []
    pending = [root]

    while pending and len(entries) < max_entries:
        current = pending.pop(0)
        children = sorted(
            os.scandir(current),
            key=lambda entry: entry.name.casefold(),
        )

        for entry in children:
            if len(entries) >= max_entries:
                break

            candidate = Path(entry.path)
            relative_path = candidate.relative_to(policy.root).as_posix()

            try:
                resolved = policy.resolve_path(relative_path, must_exist=True)
            except (FileNotFoundError, WorkspaceSecurityError):
                # Protected paths and races are omitted from directory listings.
                continue

            is_directory = entry.is_dir(follow_symlinks=False)
            item: dict[str, Any] = {
                "path": relative_path,
                "type": "directory" if is_directory else "file",
            }

            if is_directory:
                if recursive:
                    pending.append(resolved)
            else:
                try:
                    item["size_bytes"] = resolved.stat().st_size
                except OSError:
                    continue

            entries.append(item)

    return entries


def read_workspace_file(
    policy: WorkspacePolicy,
    path: str,
    *,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """Read one allowed text file from the workspace."""

    resolved = policy.resolve_path(path, must_exist=True, expect_file=True)
    policy.validate_file_size(resolved)

    try:
        content = resolved.read_text(encoding=encoding)
    except UnicodeDecodeError as exc:
        raise WorkspaceSecurityError(
            "The requested file is not valid text for the selected encoding"
        ) from exc
    except LookupError as exc:
        raise ValueError(f"Unknown text encoding: {encoding}") from exc

    return {
        "path": resolved.relative_to(policy.root).as_posix(),
        "content": content,
        "size_bytes": resolved.stat().st_size,
        "encoding": encoding,
    }
