"""Tests for whole-tree compilation + JSON emission (T3.4)."""

import json
import unittest
from pathlib import Path

from alfred_core.compiler import compile_tree

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "prompts"


class TestCompileTree(unittest.TestCase):
    def setUp(self):
        self.result = compile_tree(FIXTURES)

    def test_counts_per_kind(self):
        self.assertEqual(len(self.result["agents"]), 1)
        self.assertEqual(len(self.result["commands"]), 1)
        # Two skills: one flat, one nested under a category folder.
        self.assertEqual(len(self.result["skills"]), 2)

    def test_nested_skill_is_found(self):
        names = {s["name"] for s in self.result["skills"]}
        self.assertEqual(names, {"choose-stack", "test-plan"})

    def test_result_is_json_serializable(self):
        json.dumps(self.result)  # must not raise

    def test_known_artifact_present_with_fields(self):
        architect = self.result["agents"][0]
        self.assertEqual(architect["name"], "architect")
        self.assertIn("shell", architect["tools"])
        self.assertIn("You are the architect.", architect["body"])

    def test_command_name_from_filename(self):
        self.assertEqual(self.result["commands"][0]["name"], "feature")

    def test_missing_subdir_yields_empty_list(self):
        result = compile_tree(FIXTURES / "agents")  # has no agents/ child
        self.assertEqual(result, {"agents": [], "commands": [], "skills": []})


if __name__ == "__main__":
    unittest.main()
