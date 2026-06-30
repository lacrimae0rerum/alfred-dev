"""Ports: neutral interfaces that bind alfred_core to a hosting agent.

Each port is a protocol (ABC) that the core uses to delegate to the host.
An adapter implements the protocol for a specific host (Hermes, Claude Code, etc.).

Ports:
    - AgentRunner: spawn/manage agent sessions
    - MemoryPort: bridge between alfred_core memory and host persistent memory
    - HooksPort: bridge between alfred_core guards and host pre-post tool hooks
    - SkillsPort: bridge between alfred_core compilers and host skill system
    - HostContextPort: path-resolution port for the host's state directory
    - ToolRegistry: map alfred_core tool grants to host toolsets

The Claude Code adapter lives in ``alfred_core.adapters.claude_code`` and
implements all ports.  The Hermes adapter (Phase 4) will provide its own
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class AgentSession:
    """Opaque handle returned by ``AgentRunner.spawn``.

    Holds everything a host needs to identify and address a running session.
    The core never inspects the payload — it only forwards it to ``join``,
    ``terminate``, or ``send_message``.
    """

    session_id: str
    metadata: dict = field(default_factory=dict)


class AgentRunner(ABC):
    """Neutral interface for spawning and managing agent sessions.

    The core uses this port to:
    - Start a new agent run with a given prompt and context
    - Join an existing session to send follow-up messages
    - Terminate a session (graceful or force)
    - Check whether a session is still alive

    Implementations (Claude Code adapter, Hermes adapter) map these
    operations to the host's actual session API.
    """

    @abstractmethod
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
        """Start a new agent session and return its handle.

        Args:
            prompt: Self-contained task instruction for the agent.
            project_dir: Optional project root for context injection.
            skills: Ordered list of skill names to load before execution.
            context_from: Optional job IDs whose output is injected as context.
            model: Optional per-session model override (dict with 'provider'/'model').
            deliver: Delivery target (e.g. 'origin', 'telegram', 'all').
            workdir: Working directory for the session.

        Returns:
            A handle to the new session.
        """

    @abstractmethod
    def join(self, session: AgentSession, message: str) -> str:
        """Send a follow-up message to an existing session.

        Args:
            session: Handle returned by ``spawn``.
            message: The message to send.

        Returns:
            The agent's response text (or a partial/streamed reply).
        """

    @abstractmethod
    def terminate(self, session: AgentSession, *, force: bool = False) -> None:
        """End a session.

        Args:
            session: Handle to terminate.
            force: If True, kill immediately; if False, allow graceful shutdown.
        """

    @abstractmethod
    def is_alive(self, session: AgentSession) -> bool:
        """Return whether the session is still running."""


class MemoryPort(ABC):
    """Bridge between alfred_core memory operations and host persistent memory.

    The core calls these methods to store and retrieve durable facts.
    Implementations map to the host's memory store (Hermes uses
    ~/.hermes/memory/ or the session DB; Claude Code uses a local file).
    """

    @abstractmethod
    def save(self, target: str, content: str) -> None:
        """Save a fact.

        Args:
            target: Memory store name ('memory' or 'user').
            content: The fact text (one entry).
        """

    @abstractmethod
    def load(self, target: str) -> list[str]:
        """Load all facts from a memory store.

        Args:
            target: Memory store name.

        Returns:
            List of fact strings, each on its own line.
        """

    @abstractmethod
    def delete(self, target: str, content: str) -> bool:
        """Delete a fact.

        Args:
            target: Memory store name.
            content: Substring identifying the entry to remove.

        Returns:
            True if the fact was found and removed, False otherwise.
        """

    @abstractmethod
    def search(self, target: str, query: str) -> list[str]:
        """Search facts in a memory store.

        Args:
            target: Memory store name.
            query: Search query (simple text, no regex).

        Returns:
            Matching fact strings.
        """


class HooksPort(ABC):
    """Bridge between alfred_core guards and host pre-post tool hooks.

    The core evaluates policy via ``CoreGuard.evaluate()`` and gets a
    ``Decision``. This port translates the decision into a host-specific
    protocol (Hermes toolsets use pre/post hooks; Claude Code uses
    permissionDecision JSON).
    """

    @abstractmethod
    def evaluate_write(
        self, path: str, content: str
    ) -> dict[str, Any]:
        """Evaluate a write operation through the host's hook system.

        Args:
            path: File path being written.
            content: Content being written.

        Returns:
            Host-specific result dict (may contain 'blocked', 'reason', etc.).
        """

    @abstractmethod
    def evaluate_command(self, command: str) -> dict[str, Any]:
        """Evaluate a shell command through the host's hook system.

        Args:
            command: Shell command string.

        Returns:
            Host-specific result dict.
        """

    @abstractmethod
    def evaluate_read(self, path: str) -> dict[str, Any]:
        """Evaluate a read operation through the host's hook system.

        Args:
            path: File path being read.

        Returns:
            Host-specific result dict.
        """

    @abstractmethod
    def register_hook(
        self, hook_name: str, script_path: str, event: str
    ) -> None:
        """Register a pre/post tool hook with the host.

        Args:
            hook_name: Human-readable hook identifier.
            script_path: Path to the hook script (Python or shell).
            event: Event type ('PreToolUse', 'PostToolUse', 'PreSessionStart', etc.).
        """


class SkillsPort(ABC):
    """Bridge between alfred_core compilers and the host skill system.

    The core compiles Markdown artifacts (agents, commands, skills) into
    data structures. This port persists those artifacts into the host's
    skill store.
    """

    @abstractmethod
    def create_skill(
        self,
        name: str,
        content: str,
        category: str | None = None,
    ) -> str:
        """Create or update a skill in the host's skill store.

        Args:
            name: Skill name (lowercase, hyphens/underscores).
            content: Full SKILL.md content (YAML frontmatter + body).
            category: Optional category for grouping.

        Returns:
            Absolute path to the created/updated skill directory.
        """

    @abstractmethod
    def delete_skill(self, name: str) -> bool:
        """Delete a skill from the host's skill store.

        Args:
            name: Skill name to delete.

        Returns:
            True if the skill was found and deleted.
        """

    @abstractmethod
    def get_skill(self, name: str) -> dict[str, Any] | None:
        """Retrieve a skill from the host's skill store.

        Args:
            name: Skill name.

        Returns:
            Skill dict with 'name', 'content', 'category', or None.
        """

    @abstractmethod
    def list_skills(self) -> list[dict[str, str]]:
        """List all skills in the host's skill store.

        Returns:
            List of dicts with at least 'name' and 'category' keys.
        """


class HostContextPort(ABC):
    """Path-resolution port for the host's state directory.

    Resolves project dir, state dir, config path, state file path,
    and memory DB path in a host-agnostic way.  The core uses this
    to find artifacts without knowing the host's conventions.
    """

    @abstractmethod
    def resolve_project_dir(self, explicit_dir: str | None = None) -> str:
        """Resolve the project root directory.

        Precedence: explicit dir > environment variable > cwd.

        Returns:
            Absolute path to the project root.
        """

    @property
    @abstractmethod
    def state_dir(self) -> str:
        """Absolute path to the per-project state directory."""

    @property
    @abstractmethod
    def config_path(self) -> str:
        """Absolute path to the project config file."""

    @property
    @abstractmethod
    def state_path(self) -> str:
        """Absolute path to the session state file."""

    @property
    @abstractmethod
    def memory_db_path(self) -> str:
        """Absolute path to the SQLite memory database."""


class ToolRegistry(ABC):
    """Map alfred_core tool grants to host toolsets.

    The core uses canonical tool names (e.g. 'terminal', 'file', 'web')
    defined in the compiler. This registry maps them to host-specific
    toolset identifiers so the agent knows which capabilities to load.
    """

    # Canonical tool-to-host mapping (overridable by adapters)
    DEFAULT_MAPPINGS: dict[str, str] = {
        "terminal": "terminal",
        "file": "file",
        "web": "web",
        "browser": "browser",
        "computer_use": "computer_use",
        "coding": "coding",
        "skills": "skills",
        "memory": "memory",
        "cronjob": "cronjob",
        "delegate_task": "delegation",
        "session_search": "session_search",
        "vision": "vision",
        "text_to_speech": "tts",
    }

    @abstractmethod
    def register_mapping(self, tool: str, toolset: str) -> None:
        """Register or override a tool-to-toolset mapping.

        Args:
            tool: Canonical tool name from alfred_core.
            toolset: Host-specific toolset identifier.
        """

    @abstractmethod
    def resolve(self, tool: str) -> str | None:
        """Resolve a canonical tool name to a host toolset.

        Args:
            tool: Canonical tool name.

        Returns:
            Host toolset name, or None if no mapping exists.
        """

    @abstractmethod
    def resolve_for_spec(self, spec: dict[str, Any]) -> list[str]:
        """Resolve all tools in a compiled spec to host toolsets.

        Args:
            spec: Compiled AgentSpec dict with a 'tools' list.

        Returns:
            Unique list of resolved toolset names (order preserved).
        """

    @abstractmethod
    def to_dict(self) -> dict[str, str]:
        """Return the current tool-to-toolset mapping as a dict."""
