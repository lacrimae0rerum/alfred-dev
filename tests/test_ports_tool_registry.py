"""Tests for NoOpToolRegistry -- Port 6 test double.

Verifies that NoOpToolRegistry satisfies the ToolRegistry protocol and
correctly maps canonical tool names to host toolset identifiers.
"""

import unittest

from alfred_core.ports import ToolRegistry
from alfred_core.ports.noop import NoOpToolRegistry


class TestNoOpToolRegistryProtocol(unittest.TestCase):
    """Ensure NoOpToolRegistry satisfies the ToolRegistry ABC."""

    def test_satisfies_tool_registry_protocol(self):
        self.assertIsInstance(NoOpToolRegistry(), ToolRegistry)


class TestNoOpToolRegistryResolve(unittest.TestCase):
    """Test tool-to-toolset resolution."""

    def setUp(self):
        self.registry = NoOpToolRegistry()

    def test_terminal_resolves_to_terminal(self):
        self.assertEqual(self.registry.resolve("terminal"), "terminal")

    def test_file_resolves_to_file(self):
        self.assertEqual(self.registry.resolve("file"), "file")

    def test_web_resolves_to_web(self):
        self.assertEqual(self.registry.resolve("web"), "web")

    def test_browser_resolves_to_browser(self):
        self.assertEqual(self.registry.resolve("browser"), "browser")

    def test_delegation_resolves_to_delegation(self):
        self.assertEqual(self.registry.resolve("delegate_task"), "delegation")

    def test_unknown_tool_returns_none(self):
        self.assertIsNone(self.registry.resolve("nonexistent-tool"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self.registry.resolve(""))


class TestNoOpToolRegistryRegister(unittest.TestCase):
    """Test custom mapping registration."""

    def setUp(self):
        self.registry = NoOpToolRegistry()

    def test_register_mapping(self):
        self.registry.register_mapping("terminal", "coding")
        self.assertEqual(self.registry.resolve("terminal"), "coding")

    def test_register_overrides_default(self):
        # Default: file -> file
        self.assertEqual(self.registry.resolve("file"), "file")
        self.registry.register_mapping("file", "devops")
        self.assertEqual(self.registry.resolve("file"), "devops")

    def test_register_does_not_affect_other_tools(self):
        self.registry.register_mapping("terminal", "coding")
        self.assertEqual(self.registry.resolve("web"), "web")


class TestNoOpToolRegistryResolveForSpec(unittest.TestCase):
    """Test resolving tools from a compiled spec."""

    def setUp(self):
        self.registry = NoOpToolRegistry()

    def test_resolve_agent_spec(self):
        spec = {"tools": ["terminal", "file", "web"]}
        resolved = self.registry.resolve_for_spec(spec)
        self.assertEqual(resolved, ["terminal", "file", "web"])

    def test_resolve_csv_tools(self):
        spec = {"tools": "terminal, file, web"}
        resolved = self.registry.resolve_for_spec(spec)
        self.assertEqual(resolved, ["terminal", "file", "web"])

    def test_resolve_duplicate_tools(self):
        spec = {"tools": ["terminal", "terminal", "file"]}
        resolved = self.registry.resolve_for_spec(spec)
        self.assertEqual(resolved, ["terminal", "file"])

    def test_resolve_unknown_tool_skipped(self):
        spec = {"tools": ["terminal", "nonexistent"]}
        resolved = self.registry.resolve_for_spec(spec)
        self.assertEqual(resolved, ["terminal"])

    def test_resolve_empty_spec(self):
        spec = {"tools": []}
        resolved = self.registry.resolve_for_spec(spec)
        self.assertEqual(resolved, [])

    def test_resolve_unknown_tools_in_spec(self):
        spec = {"tools": ["bogus-tool"]}
        resolved = self.registry.resolve_for_spec(spec)
        self.assertEqual(resolved, [])


class TestNoOpToolRegistryToDict(unittest.TestCase):
    """Test to_dict serialization."""

    def setUp(self):
        self.registry = NoOpToolRegistry()

    def test_to_dict_returns_mapping(self):
        mapping = self.registry.to_dict()
        self.assertIsInstance(mapping, dict)

    def test_to_dict_contains_default_mappings(self):
        mapping = self.registry.to_dict()
        self.assertIn("terminal", mapping)
        self.assertIn("file", mapping)
        self.assertIn("web", mapping)

    def test_to_dict_reflects_custom_mappings(self):
        self.registry.register_mapping("terminal", "coding")
        mapping = self.registry.to_dict()
        self.assertEqual(mapping["terminal"], "coding")


if __name__ == "__main__":
    unittest.main()
