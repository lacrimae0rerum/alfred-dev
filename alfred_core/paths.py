"""Neutral project path helpers for Alfred Codex."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_DIR_ENV = "ALFRED_CODEX_PROJECT_DIR"
STATE_DIR_ENV = "ALFRED_CODEX_STATE_DIR"
MEMORY_DB_ENV = "ALFRED_CODEX_MEMORY_DB"


def resolve_project_dir(project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the active project directory without relying on Codex paths."""
    raw = project_dir or os.environ.get(PROJECT_DIR_ENV) or os.getcwd()
    return Path(raw).expanduser().resolve()


def state_root(project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Return the Alfred Codex state root for a project."""
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return resolve_project_dir(project_dir) / ".codex"


def state_path(project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Return the canonical flow state JSON path."""
    return state_root(project_dir) / "alfred-dev-state.json"


def config_path(project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Return the local Alfred Codex config path."""
    return state_root(project_dir) / "alfred-dev.local.md"


def memory_path(project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Return the canonical memory database path."""
    override = os.environ.get(MEMORY_DB_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return state_root(project_dir) / "alfred-memory.db"


def ensure_state_root(project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Create and return the state root."""
    root = state_root(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def is_codex_neutral_path(path: str | os.PathLike[str]) -> bool:
    """Return False for stale Claude-specific state paths."""
    parts = {part.lower() for part in Path(path).parts}
    text = str(path).lower()
    stale_fragments = {
        ".claude",
        ".claude-plugin",
        "claude_plugin_root",
        "${claude_plugin_root}",
    }
    return not any(fragment in parts or fragment in text for fragment in stale_fragments)
