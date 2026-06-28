"""Per-artifact compilers: Markdown-with-frontmatter -> neutral specs.

Each compiler parses the frontmatter, maps the CC tool grant to canonical
names, and preserves the body (the artifact's intelligence) verbatim.
"""

from .frontmatter import parse_frontmatter
from .models import AgentSpec, CommandSpec, SkillSpec
from .tools_map import map_tools


def _body(raw: str) -> str:
    """Trim only the blank lines that separate frontmatter from content."""
    return raw.strip("\n")


def compile_agent(text: str) -> AgentSpec:
    meta, body = parse_frontmatter(text)
    return AgentSpec(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        tools=map_tools(meta.get("tools")),
        model=meta.get("model", ""),
        body=_body(body),
    )


def compile_command(name: str, text: str) -> CommandSpec:
    # Commands carry no name in frontmatter; it derives from the file name.
    meta, body = parse_frontmatter(text)
    return CommandSpec(
        name=name,
        description=meta.get("description", ""),
        argument_hint=meta.get("argument-hint", ""),
        body=_body(body),
    )


def compile_skill(text: str) -> SkillSpec:
    meta, body = parse_frontmatter(text)
    return SkillSpec(
        name=meta.get("name", ""),
        description=meta.get("description", ""),
        body=_body(body),
    )
