"""Hermes adapter: implements all 6 ports for the Hermes Agent platform.

This module bridges alfred_core's neutral interfaces to Hermes' actual
APIs (terminal, cronjob, memory, skills, browser, computer_use) so the
core policies can run inside a Hermes session without knowing the host.

Ports implemented:
    - AgentRunner  -> cronjob (create/run/list/manage scheduled jobs)
    - MemoryPort   -> memory tool (save/load/delete/search durable facts)
    - HooksPort    -> terminal + pre/post hook scripts via cronjob
    - SkillsPort   -> skill_manage tool (create/delete/list skills)
    - HostContextPort -> resolves state dir relative to Hermes project root
    - ToolRegistry  -> maps canonical tools to Hermes toolset names

The adapter is designed to be testable: every port method delegates to
a real Hermes tool, but the tools can be mocked for unit tests.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
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


# ---------------------------------------------------------------------------
# Port 1: AgentRunner (Hermes implementation)
# ---------------------------------------------------------------------------

class HermesAgentRunner(AgentRunner):
    """AgentRunner backed by Hermes' cronjob tool.

    Spawning a session creates a cron job with ``no_agent=False`` (LLM-driven)
    and ``deliver='local'`` (output saved, not delivered externally).
    Joining sends a follow-up message via the job's thread.
    """

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
        # Import here to avoid circular imports at module load time
        from hermes_tools import delegate_task as _delegate

        params: dict[str, Any] = {
            "goal": prompt,
        }
        if skills:
            params["context"] = f"Load skills: {', '.join(skills)}"
        if model:
            params["model"] = model

        result = _delegate(**params)
        # delegate_task returns a dict; extract an identifier if available
        session_id = str(id(result))  # fallback ID
        if isinstance(result, dict):
            session_id = result.get("session_id", result.get("id", session_id))
        return AgentSession(
            session_id=session_id,
            metadata={"type": "delegate_task", "result": result},
        )

    def join(self, session: AgentSession, message: str) -> str:
        # For cronjob-based sessions, we can't truly "join" — instead we
        # create a follow-up job with the message as context.
        from hermes_tools import cronjob

        result = cronjob(
            action="create",
            prompt=message,
            schedule="once",
            deliver="local",
            context_from=[session.session_id],
        )
        return json.dumps({"job_id": result.get("job_id", ""), "status": "queued"})

    def terminate(self, session: AgentSession, *, force: bool = False) -> None:
        from hermes_tools import cronjob

        cronjob(action="remove", job_id=session.session_id)

    def is_alive(self, session: AgentSession) -> bool:
        from hermes_tools import cronjob

        try:
            result = cronjob(action="list")
            jobs = result.get("jobs", []) if isinstance(result, dict) else []
            return any(j.get("job_id") == session.session_id for j in jobs)
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Port 2: MemoryPort (Hermes implementation)
# ---------------------------------------------------------------------------

class HermesMemoryPort(MemoryPort):
    """MemoryPort backed by Hermes' memory tool.

    Maps alfred_core's save/load/delete/search to the memory tool's
    action/content/target API.
    """

    def save(self, target: str, content: str) -> None:
        from hermes_tools import memory

        memory(target=target, action="add", content=content)

    def load(self, target: str) -> list[str]:
        # Memory tool doesn't have a direct "load all" — we read the
        # memory files directly as a fallback.
        mem_dir = Path(os.path.expanduser("~/.hermes"))
        memory_file = mem_dir / "memory.md"
        user_file = mem_dir / "user.md"

        target_file = user_file if target == "user" else memory_file
        if target_file.exists():
            return target_file.read_text().splitlines()
        return []

    def delete(self, target: str, content: str) -> bool:
        from hermes_tools import memory

        try:
            memory(target=target, action="remove", old_text=content)
            return True
        except Exception:
            return False

    def search(self, target: str, query: str) -> list[str]:
        # Memory tool doesn't have a direct search — use session_search
        # as a fallback for factual recall.
        from hermes_tools import session_search

        try:
            result = session_search(query=query, limit=10)
            sessions = result.get("sessions", []) if isinstance(result, dict) else []
            return [s.get("preview", "") for s in sessions if isinstance(s, dict)]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Port 3: HooksPort (Hermes implementation)
# ---------------------------------------------------------------------------

class HermesHooksPort(HooksPort):
    """HooksPort backed by CoreGuard policy directly (no subprocess).

    Evaluates guards by calling the pure policy functions from
    ``alfred_core.guards`` directly, eliminating the need for hook
    scripts and subprocess calls.
    """

    def evaluate_write(
        self, path: str, content: str
    ) -> dict[str, Any]:
        """Evaluate a write through CoreGuard."""
        from ..guards import CoreGuard, GuardAction

        guard = CoreGuard()
        decision = guard.evaluate(GuardAction(kind="write", path=path, content=content))
        return {"blocked": decision.blocked, "reason": decision.reason}

    def evaluate_command(self, command: str) -> dict[str, Any]:
        """Evaluate a command through CoreGuard."""
        from ..guards import CoreGuard, GuardAction

        guard = CoreGuard()
        decision = guard.evaluate(GuardAction(kind="command", command=command))
        return {"blocked": decision.blocked, "reason": decision.reason}

    def evaluate_read(self, path: str) -> dict[str, Any]:
        """Evaluate a read through CoreGuard."""
        from ..guards import CoreGuard, GuardAction

        guard = CoreGuard()
        decision = guard.evaluate(GuardAction(kind="read", path=path))
        return {"blocked": decision.blocked, "reason": decision.reason}

    def register_hook(
        self, hook_name: str, script_path: str, event: str
    ) -> None:
        """Register a hook with Hermes via cronjob.

        For Hermes, hooks are registered as cron jobs that run on demand
        (one-shot schedule) when the tool event fires.
        """
        from hermes_tools import cronjob

        cronjob(
            action="create",
            name=hook_name,
            prompt=f"Hermes hook: {event} — run {script_path}",
            schedule="once",
            deliver="local",
        )


# ---------------------------------------------------------------------------
# Port 4: SkillsPort (Hermes implementation)
# ---------------------------------------------------------------------------

class HermesSkillsPort(SkillsPort):
    """SkillsPort backed by Hermes' skill_manage tool.

    Maps alfred_core's create/delete/get/list to the skill_manage tool.
    """

    def create_skill(
        self,
        name: str,
        content: str,
        category: str | None = None,
    ) -> str:
        from hermes_tools import skill_manage

        skill_manage(
            action="create",
            name=name,
            content=content,
            category=category,
        )
        # Return the skill directory path
        if category:
            return f"~/.hermes/skills/{category}/{name}"
        return f"~/.hermes/skills/{name}"

    def delete_skill(self, name: str) -> bool:
        from hermes_tools import skill_manage

        try:
            skill_manage(action="delete", name=name)
            return True
        except Exception:
            return False

    def get_skill(self, name: str) -> dict[str, Any] | None:
        from hermes_tools import skill_view

        try:
            result = skill_view(name=name)
            if result and result.get("success", True):
                return {
                    "name": name,
                    "content": result.get("content", ""),
                    "category": result.get("category"),
                }
            return None
        except Exception:
            return None

    def list_skills(self) -> list[dict[str, str]]:
        from hermes_tools import skills_list

        try:
            result = skills_list()
            skills = result.get("skills", []) if isinstance(result, dict) else []
            return [
                {"name": s.get("name", ""), "category": s.get("category", "")}
                for s in skills
                if isinstance(s, dict)
            ]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Port 5: HostContextPort (Hermes implementation)
# ---------------------------------------------------------------------------

class HermesHostContextPort(HostContextPort):
    """HostContextPort that delegates to the existing HostContext.

    Hermes uses a different state directory convention than Claude Code.
    By default it uses ``.hermes`` instead of ``.claude``, but this is
    configurable via the ``state_dir_name`` parameter.
    """

    def __init__(
        self,
        state_dir_name: str = ".hermes",
        project_dir: str | None = None,
        env: dict[str, str] | None = None,
    ):
        """Initialize the host context.

        Args:
            state_dir_name: Name of the per-project state directory.
                Defaults to ``.hermes`` (Hermes convention).
            project_dir: Optional explicit project directory.
            env: Optional environment mapping (defaults to os.environ).
        """
        self._state_dir_name = state_dir_name
        self._env = env
        self._explicit_project_dir = project_dir

    def resolve_project_dir(self, explicit_dir: str | None = None) -> str:
        """Resolve the project directory.

        Precedence: explicit arg > self._explicit_project_dir > env var > cwd.
        """
        resolved = explicit_dir or self._explicit_project_dir or os.getcwd()
        return os.path.abspath(resolved)

    @property
    def state_dir(self) -> str:
        project_dir = self.resolve_project_dir()
        return os.path.join(project_dir, self._state_dir_name)

    @property
    def config_path(self) -> str:
        return os.path.join(self.state_dir, "alfred-dev.local.md")

    @property
    def state_path(self) -> str:
        return os.path.join(self.state_dir, "alfred-dev-state.json")

    @property
    def memory_db_path(self) -> str:
        return os.path.join(self.state_dir, "alfred-memory.db")


# ---------------------------------------------------------------------------
# Port 6: ToolRegistry (Hermes implementation)
# ---------------------------------------------------------------------------

class HermesToolRegistry(ToolRegistry):
    """ToolRegistry for Hermes.

    Maps canonical alfred_core tool names to Hermes toolset identifiers.
    Uses the DEFAULT_MAPPINGS as a base but can be customized per-project.
    """

    def __init__(self, mappings: dict[str, str] | None = None):
        """Initialize with optional custom mappings.

        Args:
            mappings: Optional override dict. If None, uses DEFAULT_MAPPINGS.
        """
        self._mappings = dict(self.DEFAULT_MAPPINGS)
        if mappings:
            self._mappings.update(mappings)

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
