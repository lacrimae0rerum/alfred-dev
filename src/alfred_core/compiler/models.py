"""Neutral, host-agnostic prompt spec models.

Each spec captures the portable essence of a Claude Code prompt artifact -- its
name, description, body (the actual intelligence), and type-specific fields --
with the CC wrapper shed. ``to_dict`` yields JSON-serializable data that a host
adapter (phase 4) renders into its own format.
"""

from dataclasses import asdict, dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentSpec:
    """A subagent: system prompt plus its tool grant and model."""

    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    model: str = ""
    body: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CommandSpec:
    """A slash command: a prompt template driven by ``$ARGUMENTS``."""

    name: str
    description: str
    argument_hint: str = ""
    body: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SkillSpec:
    """A skill: a description-triggered body of guidance."""

    name: str
    description: str
    body: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
