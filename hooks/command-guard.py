#!/usr/bin/env python3
"""PreToolUse hook for Bash: block dangerous commands.

Thin wiring only: bootstrap ``src/`` onto sys.path, read the tool input,
delegate the decision to the pure core policy, and emit the Claude Code
transport. All policy lives in ``alfred_core.guards``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alfred_core.adapters.claude_code import (  # noqa: E402  (after path bootstrap)
    HookInputError,
    emit,
    read_tool_input,
)
from alfred_core.guards import CoreGuard, GuardAction, deny  # noqa: E402


def main() -> int:
    try:
        tool_input = read_tool_input(sys.stdin)
    except HookInputError as exc:
        return emit(deny(str(exc)), out=sys.stdout, err=sys.stderr)

    action = GuardAction(kind="command", command=tool_input.get("command", ""))
    return emit(CoreGuard().evaluate(action), out=sys.stdout, err=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
