"""Prompt compiler: Claude Code artifacts -> neutral, host-agnostic specs.

Reads the Markdown-with-frontmatter artifacts (agents, commands, skills) and
produces serializable spec objects plus a CC -> canonical tool-name map. The
artifact *content* (the body / system prompt) is preserved verbatim; only the
CC-specific wrapper is shed. This is phase 4 of the portability audit plan.
"""

from .compile import (
    compile_agent,
    compile_command,
    compile_skill,
    compile_tree,
)
from .frontmatter import parse_frontmatter
from .models import AgentSpec, CommandSpec, SkillSpec
from .tools_map import map_tool, map_tools

__all__ = [
    "parse_frontmatter",
    "AgentSpec",
    "CommandSpec",
    "SkillSpec",
    "map_tool",
    "map_tools",
    "compile_agent",
    "compile_command",
    "compile_skill",
    "compile_tree",
]
