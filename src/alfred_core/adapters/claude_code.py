"""Claude Code PreToolUse hook transport.

Maps a pure :class:`~alfred_core.guards.Decision` onto Claude Code's hook
transport so the thin scripts in ``hooks/`` stay free of policy logic:

    - ``deny``  -> warning on stderr, exit code 2 (blocks the tool).
    - ``ask``   -> ``permissionDecision: "ask"`` JSON, exit 0.
    - ``allow`` with a reason -> ``permissionDecision: "allow"`` JSON (an
      explicit auto-approve, e.g. a recognized safe helper), exit 0.
    - ``allow`` without a reason -> silent exit 0 (pass-through to Claude
      Code's normal permission flow).

Reading stdin is fail-closed: a malformed payload raises ``HookInputError``,
which the caller is expected to translate into a deny.
"""

import json
from typing import TextIO

from ..guards import Decision


class HookInputError(Exception):
    """Raised when the PreToolUse stdin payload cannot be parsed."""


def read_tool_input(stream: TextIO) -> dict:
    """Parse the PreToolUse JSON payload and return its ``tool_input`` dict.

    Raises :class:`HookInputError` if the stream does not hold valid JSON --
    callers must translate that into a deny (fail-closed).
    """
    try:
        data = json.load(stream)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HookInputError(f"could not parse hook input: {exc}") from exc
    if not isinstance(data, dict):
        raise HookInputError("hook input is not a JSON object")
    return data.get("tool_input", {})


def _permission_payload(decision: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
            }
        }
    )


def emit(decision: Decision, *, out: TextIO, err: TextIO) -> int:
    """Render ``decision`` to ``out``/``err`` and return the hook exit code."""
    if decision.outcome == "deny":
        err.write(f"\n[alfred-core] BLOCKED: {decision.reason}\n")
        return 2
    if decision.outcome == "ask":
        out.write(_permission_payload("ask"))
        return 0
    # allow
    if decision.reason:
        out.write(_permission_payload("allow"))
    return 0
