"""No-op port implementations for testing without a real Hermes API.

These implementations satisfy all port protocols but perform no actual
host interaction. They return safe defaults (allow decisions, empty
lists, etc.) so the core policies can be tested end-to-end.

Usage:
    runner = NoOpAgentRunner()
    session = runner.spawn("test prompt")
    assert session.session_id  # non-empty placeholder
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from . import (
    AgentRunner,
    AgentSession,
    HooksPort,
    HostContextPort,
    MemoryPort,
    SkillsPort,
    ToolRegistry,
)


class NoOpAgentRunner(AgentRunner):
    """AgentRunner that generates fake session IDs."""

    def spawn(
        self,
        prompt: str,
        *,
        project_dir: str | None = None,
        skills: list[str] | None = None,
        context_from: list[str] | None = None,
        model: dict[str, str] | None = None,
        deliver: str | None = None,
        workdir: str | None = None,
    ) -> AgentSession:
        return AgentSession(
            session_id=f"noop-{uuid.uuid4().hex[:8]}",
            metadata={"type": "noop", "prompt": prompt},
        )

    def join(self, session: AgentSession, message: str) -> str:
        return json.dumps({"status": "noop", "message": message})

    def terminate(self, session: AgentSession, *, force: bool = False) -> None:
        pass

    def is_alive(self, session: AgentSession) -> bool:
        return True


class NoOpMemoryPort(MemoryPort):
    """MemoryPort that stores facts in memory (no persistence)."""

    def __init__(self):
        self._store: dict[str, list[str]] = {"memory": [], "user": []}

    def save(self, target: str, content: str) -> None:
        self._store.setdefault(target, []).append(content)

    def load(self, target: str) -> list[str]:
        return list(self._store.get(target, []))

    def delete(self, target: str, content: str) -> bool:
        store = self._store.get(target, [])
        for i, entry in enumerate(store):
            if content in entry:
                store.pop(i)
                return True
        return False

    def search(self, target: str, query: str) -> list[str]:
        return [
            entry for entry in self._store.get(target, [])
            if query.lower() in entry.lower()
        ]


class NoOpHooksPort(HooksPort):
    """HooksPort that always allows (fail-open)."""

    def evaluate_write(self, path: str, content: str) -> dict[str, Any]:
        return {"blocked": False, "reason": ""}

    def evaluate_command(self, command: str) -> dict[str, Any]:
        return {"blocked": False, "reason": ""}

    def evaluate_read(self, path: str) -> dict[str, Any]:
        return {"blocked": False, "reason": ""}

    def register_hook(self, hook_name: str, script_path: str, event: str) -> None:
        pass


class NoOpSkillsPort(SkillsPort):
    """SkillsPort that stores skills in memory."""

    def __init__(self):
        self._skills: dict[str, dict[str, Any]] = {}

    def create_skill(
        self,
        name: str,
        content: str,
        category: str | None = None,
    ) -> str:
        self._skills[name] = {
            "name": name,
            "content": content,
            "category": category,
        }
        if category:
            return f"~/.hermes/skills/{category}/{name}"
        return f"~/.hermes/skills/{name}"

    def delete_skill(self, name: str) -> bool:
        return self._skills.pop(name, None) is not None

    def get_skill(self, name: str) -> dict[str, Any] | None:
        return self._skills.get(name)

    def list_skills(self) -> list[dict[str, str]]:
        return [
            {"name": s["name"], "category": s.get("category", "")}
            for s in self._skills.values()
        ]


class NoOpHostContextPort(HostContextPort):
    """HostContextPort that uses a fixed project directory."""

    def __init__(self, project_dir: str = "/tmp/noop-project"):
        self._project_dir = project_dir

    def resolve_project_dir(self, explicit_dir: str | None = None) -> str:
        return os.path.abspath(explicit_dir or self._project_dir)

    @property
    def state_dir(self) -> str:
        return os.path.join(self.resolve_project_dir(), ".hermes")

    @property
    def config_path(self) -> str:
        return os.path.join(self.state_dir, "alfred-dev.local.md")

    @property
    def state_path(self) -> str:
        return os.path.join(self.state_dir, "alfred-dev-state.json")

    @property
    def memory_db_path(self) -> str:
        return os.path.join(self.state_dir, "alfred-memory.db")


class NoOpToolRegistry(ToolRegistry):
    """ToolRegistry that uses DEFAULT_MAPPINGS without overrides."""

    def __init__(self):
        self._mappings = dict(self.DEFAULT_MAPPINGS)

    def register_mapping(self, tool: str, toolset: str) -> None:
        self._mappings[tool] = toolset

    def resolve(self, tool: str) -> str | None:
        return self._mappings.get(tool)

    def resolve_for_spec(self, spec: dict[str, Any]) -> list[str]:
        tools = spec.get("tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",") if t.strip()]
        resolved = []
        seen = set()
        for tool in tools:
            ts = self.resolve(tool)
            if ts and ts not in seen:
                resolved.append(ts)
                seen.add(ts)
        return resolved

    def to_dict(self) -> dict[str, str]:
        return dict(self._mappings)
