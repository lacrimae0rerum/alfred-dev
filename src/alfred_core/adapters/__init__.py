"""Host adapters: bind the pure core policies to a concrete host transport.

The core (``alfred_core.guards``) returns host-agnostic :class:`Decision`
values. An adapter translates those into a specific host's protocol -- here,
Claude Code's PreToolUse hook transport (exit codes + permissionDecision JSON).
"""
