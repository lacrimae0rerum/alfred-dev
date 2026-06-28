"""Tests for the unified guard facade (T2.4).

``CoreGuard.evaluate`` dispatches a ``GuardAction`` to the right policy
(``evaluate_write`` / ``evaluate_command`` / ``evaluate_read``) by ``kind``.
Each kind is exercised with one allow and one deny case, plus the protocol
conformance of ``CoreGuard`` to ``ToolGuard``.
"""

import unittest

from alfred_core.guards import CoreGuard, Decision, GuardAction, ToolGuard


class TestWriteDispatch(unittest.TestCase):
    def setUp(self):
        self.guard = CoreGuard()

    def test_write_secret_is_denied(self):
        fake_key = "sk-" + "d" * 24
        action = GuardAction(kind="write", path="/tmp/config.py", content=f'KEY="{fake_key}"')
        self.assertTrue(self.guard.evaluate(action).blocked)

    def test_write_clean_is_allowed(self):
        action = GuardAction(kind="write", path="/tmp/main.py", content="print('hi')\n")
        self.assertEqual(self.guard.evaluate(action).outcome, "allow")


class TestCommandDispatch(unittest.TestCase):
    def setUp(self):
        self.guard = CoreGuard()

    def test_dangerous_command_is_denied(self):
        action = GuardAction(kind="command", command="rm -rf /")
        self.assertTrue(self.guard.evaluate(action).blocked)

    def test_normal_command_is_allowed(self):
        action = GuardAction(kind="command", command="ls -la")
        self.assertEqual(self.guard.evaluate(action).outcome, "allow")


class TestReadDispatch(unittest.TestCase):
    def setUp(self):
        self.guard = CoreGuard()

    def test_sensitive_read_is_denied(self):
        action = GuardAction(kind="read", path="/project/.env")
        self.assertTrue(self.guard.evaluate(action).blocked)

    def test_normal_read_is_allowed(self):
        action = GuardAction(kind="read", path="/project/main.py")
        self.assertEqual(self.guard.evaluate(action).outcome, "allow")


class TestFacadeContract(unittest.TestCase):
    def test_coreguard_satisfies_tool_guard_protocol(self):
        self.assertIsInstance(CoreGuard(), ToolGuard)

    def test_evaluate_returns_decision(self):
        decision = CoreGuard().evaluate(GuardAction(kind="command", command="ls"))
        self.assertIsInstance(decision, Decision)

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            CoreGuard().evaluate(GuardAction(kind="bogus"))


if __name__ == "__main__":
    unittest.main()
