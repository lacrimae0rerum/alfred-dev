"""Prompt compiler: Claude Code artifacts -> neutral, host-agnostic specs.

Reads the Markdown-with-frontmatter artifacts (agents, commands, skills) and
produces serializable spec objects plus a CC -> canonical tool-name map. The
artifact *content* (the body / system prompt) is preserved verbatim; only the
CC-specific wrapper is shed. This is phase 4 of the portability audit plan.
"""

from .frontmatter import parse_frontmatter

__all__ = ["parse_frontmatter"]
