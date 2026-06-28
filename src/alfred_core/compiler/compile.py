"""Per-artifact compilers: Markdown-with-frontmatter -> neutral specs.

Each compiler parses the frontmatter, maps the CC tool grant to canonical
names, and preserves the body (the artifact's intelligence) verbatim.
``compile_tree`` walks a whole artifact tree and emits JSON-serializable data.
"""

from pathlib import Path

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


def compile_tree(root: Path) -> dict:
    """Compile every artifact under ``root`` into JSON-serializable specs.

    Looks for ``agents/*.md``, ``commands/*.md`` and ``skills/*/SKILL.md`` below
    ``root``. Missing subdirectories simply yield empty lists.
    """
    root = Path(root)
    agents_dir = root / "agents"
    commands_dir = root / "commands"
    skills_dir = root / "skills"

    agents = [
        compile_agent(path.read_text()).to_dict()
        for path in sorted(agents_dir.glob("*.md"))
        if agents_dir.is_dir()
    ]
    commands = [
        compile_command(path.stem, path.read_text()).to_dict()
        for path in sorted(commands_dir.glob("*.md"))
        if commands_dir.is_dir()
    ]
    # Skills may be nested under category folders (skills/<cat>/<skill>/SKILL.md),
    # so search at any depth rather than a single level.
    skills = [
        compile_skill(skill_md.read_text()).to_dict()
        for skill_md in sorted(skills_dir.rglob("SKILL.md"))
        if skills_dir.is_dir()
    ]
    return {"agents": agents, "commands": commands, "skills": skills}
