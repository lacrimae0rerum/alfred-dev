"""Tests for the CC -> canonical tool-name map (T3.2)."""

import unittest

from alfred_core.compiler.tools_map import is_mapped, map_tool, map_tools


class TestMapTool(unittest.TestCase):
    def test_known_pairs(self):
        self.assertEqual(map_tool("Bash"), "shell")
        self.assertEqual(map_tool("Read"), "read_file")
        self.assertEqual(map_tool("Write"), "write_file")
        self.assertEqual(map_tool("Edit"), "edit_file")
        self.assertEqual(map_tool("Glob"), "glob")
        self.assertEqual(map_tool("Grep"), "grep")
        self.assertEqual(map_tool("WebSearch"), "web_search")
        self.assertEqual(map_tool("WebFetch"), "web_fetch")

    def test_agent_and_task_collapse_to_subagent(self):
        self.assertEqual(map_tool("Agent"), "subagent")
        self.assertEqual(map_tool("Task"), "subagent")

    def test_unknown_tool_is_preserved(self):
        self.assertEqual(map_tool("MysteryTool"), "MysteryTool")

    def test_is_mapped(self):
        self.assertTrue(is_mapped("Bash"))
        self.assertFalse(is_mapped("MysteryTool"))


class TestMapTools(unittest.TestCase):
    def test_csv_with_spaces(self):
        self.assertEqual(
            map_tools("Glob, Grep ,Read"), ["glob", "grep", "read_file"]
        )

    def test_list_input(self):
        self.assertEqual(map_tools(["Bash", "Edit"]), ["shell", "edit_file"])

    def test_empty_entries_ignored(self):
        self.assertEqual(map_tools("Bash,,  ,Read"), ["shell", "read_file"])

    def test_empty_value(self):
        self.assertEqual(map_tools(""), [])
        self.assertEqual(map_tools(None), [])


if __name__ == "__main__":
    unittest.main()
