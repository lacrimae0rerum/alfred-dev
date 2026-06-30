"""Tests for NoOpHooksPort -- Port 3 test double.

Verifies that NoOpHooksPort satisfies the HooksPort protocol and
always allows operations (fail-open behavior).
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from alfred_core.ports import HooksPort
from alfred_core.ports.noop import NoOpHooksPort


class TestNoOpHooksPortProtocol(unittest.TestCase):
    """Ensure NoOpHooksPort satisfies the HooksPort ABC."""

    def test_satisfies_hooks_port_protocol(self):
        self.assertIsInstance(NoOpHooksPort(), HooksPort)


class TestNoOpHooksPortEvaluate(unittest.TestCase):
    """Test that evaluate methods always allow (fail-open)."""

    def setUp(self):
        self.port = NoOpHooksPort()

    def test_evaluate_write_allows(self):
        result = self.port.evaluate_write("/tmp/test.py", "print('hi')")
        self.assertFalse(result["blocked"])
        self.assertEqual(result["reason"], "")

    def test_evaluate_write_allows_secret_content(self):
        # NoOp always allows — real hooks would deny secrets
        result = self.port.evaluate_write("/tmp/test.py", "KEY=sk-abc123")
        self.assertFalse(result["blocked"])

    def test_evaluate_command_allows(self):
        result = self.port.evaluate_command("rm -rf /")
        self.assertFalse(result["blocked"])

    def test_evaluate_command_allows_dangerous(self):
        result = self.port.evaluate_command("sudo rm -rf /")
        self.assertFalse(result["blocked"])

    def test_evaluate_read_allows(self):
        result = self.port.evaluate_read("/tmp/test.py")
        self.assertFalse(result["blocked"])

    def test_evaluate_read_allows_sensitive(self):
        # NoOp always allows — real hooks would deny sensitive files
        result = self.port.evaluate_read("/project/.env")
        self.assertFalse(result["blocked"])


class TestNoOpHooksPortRegister(unittest.TestCase):
    """Test register_hook does not raise."""

    def setUp(self):
        self.port = NoOpHooksPort()

    def test_register_hook_does_not_raise(self):
        self.port.register_hook(
            hook_name="test-hook",
            script_path="/tmp/test-hook.py",
            event="PreToolUse",
        )

    def test_register_hook_with_various_events(self):
        for event in ["PreToolUse", "PostToolUse", "PreSessionStart", "PostSessionEnd"]:
            self.port.register_hook("test", "/tmp/script.py", event)


class TestNoOpHooksPortWithRealHooksDir(unittest.TestCase):
    """Test NoOpHooksPort always allows regardless of hooks directory."""

    def test_evaluate_write_allows_even_with_hooks_dir(self):
        port = NoOpHooksPort()
        result = port.evaluate_write("/tmp/test.py", "content")
        self.assertFalse(result["blocked"])

    def test_evaluate_command_allows_even_with_hooks_dir(self):
        port = NoOpHooksPort()
        result = port.evaluate_command("ls -la")
        self.assertFalse(result["blocked"])

    def test_evaluate_read_allows_even_with_hooks_dir(self):
        port = NoOpHooksPort()
        result = port.evaluate_read("/tmp/test.py")
        self.assertFalse(result["blocked"])


if __name__ == "__main__":
    unittest.main()
