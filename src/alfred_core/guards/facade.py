"""Unified guard facade.

A single entry point that dispatches a :class:`GuardAction` to the matching
policy function. ``ToolGuard`` is the port (a ``Protocol``) so a host can swap
in its own implementation; ``CoreGuard`` is the default that routes to the
pure ``evaluate_*`` policies in this package.
"""

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from .commands import evaluate_command
from .decision import Decision
from .reads import evaluate_read
from .secrets_guard import evaluate_write


@dataclass(frozen=True)
class GuardAction:
    """A tool action to be judged by a guard.

    ``kind`` selects the policy; the other fields carry its inputs:
      - ``write``   -> ``path`` + ``content``
      - ``command`` -> ``command``
      - ``read``    -> ``path``
    """

    kind: str
    command: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None


@runtime_checkable
class ToolGuard(Protocol):
    """Port: judge a tool action and return a :class:`Decision`."""

    def evaluate(self, action: GuardAction) -> Decision: ...


class CoreGuard:
    """Default :class:`ToolGuard` dispatching to the pure core policies."""

    def evaluate(self, action: GuardAction) -> Decision:
        if action.kind == "write":
            return evaluate_write(action.path or "", action.content or "")
        if action.kind == "command":
            return evaluate_command(action.command or "")
        if action.kind == "read":
            return evaluate_read(action.path or "")
        raise ValueError(f"unknown guard action kind: {action.kind!r}")
