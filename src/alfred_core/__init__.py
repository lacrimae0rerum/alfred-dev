"""alfred_core -- portable engine extracted from the Alfred Dev plugin.

This package holds the host-agnostic core of Alfred Dev: the flow/gate state
machine, the SQLite memory layer, secret sanitization, the agent/personality
catalogs and the optional-agent registry. It carries no hard dependency on
Claude Code; the only remaining coupling (path resolution under ``.claude/``)
is tracked as debt for the upcoming HostContext port (phase 1).

See ``docs/`` for the coupling map and portability audit that motivate this
extraction.
"""

from __future__ import annotations

from . import ports

__version__ = "0.1.0"

__all__ = [
    "memory",
    "memory_config",
    "secrets",
    "personality",
    "optional_agents",
    "orchestrator",
    "config_loader",
    "ports",
]
