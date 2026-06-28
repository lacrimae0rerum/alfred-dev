"""Claude Code -> canonical tool-name map.

Translates CC tool names into host-agnostic canonical names. An unknown tool is
preserved verbatim (and reported as unmapped via :func:`is_mapped`) rather than
guessed at -- inventing an equivalence would be dishonest about coverage. A host
adapter (phase 4) maps these canonical names onto its own tools.
"""

from typing import List, Union

_CC_TO_CANONICAL = {
    "Bash": "shell",
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "edit_file",
    "Glob": "glob",
    "Grep": "grep",
    "WebSearch": "web_search",
    "WebFetch": "web_fetch",
    "Agent": "subagent",
    "Task": "subagent",
}


def is_mapped(name: str) -> bool:
    """True if ``name`` is a known CC tool with a canonical equivalent."""
    return name.strip() in _CC_TO_CANONICAL


def map_tool(name: str) -> str:
    """Map one CC tool name; unknown names pass through unchanged."""
    return _CC_TO_CANONICAL.get(name.strip(), name.strip())


def map_tools(value: Union[str, List[str], None]) -> List[str]:
    """Map a CSV string or a list of CC tool names to canonical names.

    Whitespace is trimmed and empty entries are dropped.
    """
    if not value:
        return []
    items = value.split(",") if isinstance(value, str) else value
    return [map_tool(item) for item in items if item and item.strip()]
