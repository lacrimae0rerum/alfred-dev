"""Tests for the Claude Code hook transport adapter (T2.5a).

Exercise ``read_tool_input`` and ``emit`` with in-memory streams -- no
subprocess. The adapter maps a pure :class:`Decision` onto Claude Code's
PreToolUse transport (exit codes + optional permissionDecision JSON).
"""

import io
import json
import unittest

from alfred_core.adapters.claude_code import (
    HookInputError,
    emit,
    read_tool_input,
)
from alfred_core.guards import allow, ask, deny


class TestReadToolInput(unittest.TestCase):
    def test_parses_tool_input(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "ls"}}
        result = read_tool_input(io.StringIO(json.dumps(payload)))
        self.assertEqual(result, {"command": "ls"})

    def test_missing_tool_input_defaults_empty(self):
        result = read_tool_input(io.StringIO(json.dumps({"tool_name": "Read"})))
        self.assertEqual(result, {})

    def test_invalid_json_raises_hook_input_error(self):
        with self.assertRaises(HookInputError):
            read_tool_input(io.StringIO("not json{"))


class TestEmitDeny(unittest.TestCase):
    def test_deny_returns_2_and_writes_stderr(self):
        out, err = io.StringIO(), io.StringIO()
        code = emit(deny("hardcoded key"), out=out, err=err)
        self.assertEqual(code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("hardcoded key", err.getvalue())


class TestEmitAllow(unittest.TestCase):
    def test_plain_allow_is_silent_exit_0(self):
        out, err = io.StringIO(), io.StringIO()
        code = emit(allow(), out=out, err=err)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "")

    def test_allow_with_reason_emits_permission_allow_json(self):
        out, err = io.StringIO(), io.StringIO()
        code = emit(allow("recognized safe Alfred helper"), out=out, err=err)
        self.assertEqual(code, 0)
        response = json.loads(out.getvalue())
        self.assertEqual(
            response["hookSpecificOutput"]["permissionDecision"], "allow"
        )
        self.assertEqual(
            response["hookSpecificOutput"]["hookEventName"], "PreToolUse"
        )


class TestEmitAsk(unittest.TestCase):
    def test_ask_emits_permission_ask_json(self):
        out, err = io.StringIO(), io.StringIO()
        code = emit(ask("are you sure?"), out=out, err=err)
        self.assertEqual(code, 0)
        response = json.loads(out.getvalue())
        self.assertEqual(
            response["hookSpecificOutput"]["permissionDecision"], "ask"
        )


if __name__ == "__main__":
    unittest.main()
