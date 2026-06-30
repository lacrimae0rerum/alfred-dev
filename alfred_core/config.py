"""Small config loader for Alfred Codex local project settings."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .optional_agents import build_optional_agent_flags
from .paths import config_path

AUTONOMY_DEFAULTS = {
    "producto": "autonomo",
    "arquitectura": "autonomo",
    "desarrollo": "autonomo",
    "calidad": "autonomo",
    "documentacion": "autonomo",
    "entrega": "autonomo",
}

DEFAULT_MEMORY_CONFIG = {
    "enabled": True,
    "sync_commits_limit": 10,
    "capture_decisions": True,
    "capture_commits": True,
    "retention_days": 365,
}

DEFAULT_CONFIG = {
    "autonomia": dict(AUTONOMY_DEFAULTS),
    "agentes_opcionales": build_optional_agent_flags(False),
    "memoria": dict(DEFAULT_MEMORY_CONFIG),
    "notas": "",
}


def _coerce_scalar(raw: str) -> Any:
    value = raw.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def _parse_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    collected = []
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(collected), "\n".join(lines[index + 1:])
        collected.append(line)
    return "", text


def _parse_simple_yaml(frontmatter: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: str | None = None
    current_indent = 0

    for line in frontmatter.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if indent == 0:
            if raw_value:
                data[key] = _coerce_scalar(raw_value)
                current_section = None
            else:
                data[key] = {}
                current_section = key
                current_indent = indent
            continue

        if current_section and indent > current_indent and isinstance(data.get(current_section), dict):
            data[current_section][key] = _coerce_scalar(raw_value)

    return data


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        elif key in merged:
            merged[key] = value
    return merged


def load_config(project_dir: str | Path | None = None) -> dict[str, Any]:
    """Load config from `.codex/alfred/config.local.md` with safe defaults."""
    path = config_path(project_dir)
    config = copy.deepcopy(DEFAULT_CONFIG)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return config
    frontmatter, body = _parse_frontmatter(text)
    if frontmatter:
        parsed = _parse_simple_yaml(frontmatter)
        config = _deep_merge(config, parsed)
    notes = body.strip()
    if notes:
        config["notas"] = notes
    return config


def is_autopilot_enabled(project_dir: str | Path | None = None) -> bool:
    """Return true when all configured autonomy phases are autonomous."""
    autonomy = load_config(project_dir).get("autonomia", {})
    return all(value == "autonomo" for value in autonomy.values())
