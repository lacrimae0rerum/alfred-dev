"""The ``Decision`` value type shared by every guard policy.

A guard answers a single question about a tool action: should the host allow
it, deny it, or ask the user? That answer is pure data -- it carries no exit
codes, no JSON envelope, nothing host-specific. The hook adapter (a later
phase) is what maps a ``Decision`` onto Claude Code's transport.

Keeping the type immutable means a decision can be passed around, logged, and
compared without any risk of a downstream caller mutating it.
"""

from dataclasses import dataclass
from typing import Literal

Outcome = Literal["allow", "deny", "ask"]


@dataclass(frozen=True)
class Decision:
    """The verdict of a guard policy over a single tool action."""

    outcome: Outcome
    reason: str = ""

    @property
    def blocked(self) -> bool:
        """True when the action must not proceed (a ``deny``)."""
        return self.outcome == "deny"


def allow() -> Decision:
    """Permit the action; no reason needed."""
    return Decision(outcome="allow")


def deny(reason: str) -> Decision:
    """Block the action, recording why."""
    return Decision(outcome="deny", reason=reason)


def ask(reason: str) -> Decision:
    """Defer the action to the user, recording why."""
    return Decision(outcome="ask", reason=reason)
