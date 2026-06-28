"""HostContext -- the path-resolution port for alfred_core (phase 1).

The core used to hardcode the Claude Code ``.claude/`` layout and resolve the
project directory with ``project_dir or os.getcwd()``, silently ignoring the
official ``CLAUDE_PROJECT_DIR`` variable. ``HostContext`` centralizes both:

- Project-dir resolution follows ``explicit-arg > CLAUDE_PROJECT_DIR > cwd``,
  which closes the ``CLAUDE_PROJECT_DIR`` debt noted in the native-CC spike.
- Every filesystem convention (state dir, config file, state file, memory db)
  is derived from a single, configurable ``state_dir_name``. Non-Claude-Code
  hosts can relocate the state directory without touching the core.

The Claude Code adapter builds the context via :meth:`HostContext.from_env`;
other hosts construct it directly with whatever paths they own.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

#: Canonical state directory name used by the Claude Code host.
DEFAULT_STATE_DIR_NAME = ".claude"

#: Canonical artifact file names, relative to the state dir.
CONFIG_FILE_NAME = "alfred-dev.local.md"
STATE_FILE_NAME = "alfred-dev-state.json"
MEMORY_DB_FILE_NAME = "alfred-memory.db"


@dataclass(frozen=True)
class HostContext:
    """Resolves project paths independently of the hosting agent.

    Args:
        project_dir: project root. Normalized to an absolute path. May be given
            relative; it is resolved against the current working directory.
        state_dir_name: name of the per-project state directory. Defaults to
            ``.claude`` (Claude Code convention); override for other hosts.
    """

    project_dir: str
    state_dir_name: str = DEFAULT_STATE_DIR_NAME

    def __post_init__(self) -> None:
        # Frozen dataclass: bypass the immutability guard for normalization.
        object.__setattr__(self, "project_dir", os.path.abspath(self.project_dir))

    @classmethod
    def from_env(
        cls,
        project_dir: str | None = None,
        *,
        env: dict[str, str] | None = None,
        state_dir_name: str = DEFAULT_STATE_DIR_NAME,
    ) -> HostContext:
        """Build a context resolving the project dir from the environment.

        Precedence: explicit ``project_dir`` argument, then
        ``CLAUDE_PROJECT_DIR``, then the current working directory.

        Args:
            project_dir: explicit override; wins over everything else.
            env: environment mapping to read (defaults to ``os.environ``).
                Injectable for tests and non-CC hosts.
            state_dir_name: per-project state directory name.
        """
        environ = env if env is not None else os.environ
        resolved = project_dir or environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        return cls(project_dir=resolved, state_dir_name=state_dir_name)

    @property
    def state_dir(self) -> str:
        """Absolute path to the per-project state directory."""
        return os.path.join(self.project_dir, self.state_dir_name)

    @property
    def config_path(self) -> str:
        """Absolute path to the project config file."""
        return os.path.join(self.state_dir, CONFIG_FILE_NAME)

    @property
    def state_path(self) -> str:
        """Absolute path to the session state file."""
        return os.path.join(self.state_dir, STATE_FILE_NAME)

    @property
    def memory_db_path(self) -> str:
        """Absolute path to the SQLite memory database."""
        return os.path.join(self.state_dir, MEMORY_DB_FILE_NAME)
