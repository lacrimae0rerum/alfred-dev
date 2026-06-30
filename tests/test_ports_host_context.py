"""Tests for NoOpHostContextPort -- Port 5 test double.

Verifies that NoOpHostContextPort satisfies the HostContextPort protocol
and resolves paths correctly.
"""

import os
import unittest

from alfred_core.ports import HostContextPort
from alfred_core.ports.noop import NoOpHostContextPort


class TestNoOpHostContextPortProtocol(unittest.TestCase):
    """Ensure NoOpHostContextPort satisfies the HostContextPort ABC."""

    def test_satisfies_host_context_port_protocol(self):
        self.assertIsInstance(NoOpHostContextPort(), HostContextPort)


class TestNoOpHostContextPortPaths(unittest.TestCase):
    """Test path resolution."""

    def setUp(self):
        self.port = NoOpHostContextPort("/tmp/test-project")

    def test_state_dir(self):
        self.assertEqual(
            self.port.state_dir,
            os.path.join(os.path.abspath("/tmp/test-project"), ".hermes"),
        )

    def test_config_path(self):
        expected = os.path.join(self.port.state_dir, "alfred-dev.local.md")
        self.assertEqual(self.port.config_path, expected)

    def test_state_path(self):
        expected = os.path.join(self.port.state_dir, "alfred-dev-state.json")
        self.assertEqual(self.port.state_path, expected)

    def test_memory_db_path(self):
        expected = os.path.join(self.port.state_dir, "alfred-memory.db")
        self.assertEqual(self.port.memory_db_path, expected)

    def test_all_paths_are_absolute(self):
        self.assertTrue(os.path.isabs(self.port.state_dir))
        self.assertTrue(os.path.isabs(self.port.config_path))
        self.assertTrue(os.path.isabs(self.port.state_path))
        self.assertTrue(os.path.isabs(self.port.memory_db_path))


class TestNoOpHostContextPortResolve(unittest.TestCase):
    """Test project dir resolution."""

    def test_default_resolves_to_given_project(self):
        port = NoOpHostContextPort("/tmp/my-proj")
        self.assertEqual(port.resolve_project_dir(), "/tmp/my-proj")

    def test_resolve_accepts_explicit_override(self):
        port = NoOpHostContextPort("/tmp/default")
        self.assertEqual(port.resolve_project_dir("/tmp/override"), "/tmp/override")

    def test_resolve_normalizes_relative_path(self):
        port = NoOpHostContextPort("relative/path")
        resolved = port.resolve_project_dir()
        self.assertTrue(os.path.isabs(resolved))


if __name__ == "__main__":
    unittest.main()
