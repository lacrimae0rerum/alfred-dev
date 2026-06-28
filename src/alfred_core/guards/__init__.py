"""Guard policies as pure functions.

This package holds the *policy* half of Alfred's guards: given a tool action,
decide allow/deny/ask. The decision is returned as a :class:`Decision` value
object with no host coupling -- no exit codes, no hook JSON. A later phase
wraps these functions in the actual Claude Code hook scripts.
"""

from .commands import evaluate_command
from .decision import Decision, allow, ask, deny
from .reads import evaluate_read
from .secrets_guard import evaluate_write

__all__ = [
    "Decision",
    "allow",
    "deny",
    "ask",
    "evaluate_write",
    "evaluate_command",
    "evaluate_read",
]
