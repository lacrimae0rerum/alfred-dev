"""Validate the PreToolUse hook registration (T2.5c).

``hooks/hooks.json`` wires each guard script to its tool matcher. These tests
check it is well-formed JSON, that every referenced script exists on disk, and
that the expected matchers are present.
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"
REGISTRATION = HOOKS / "hooks.json"


class TestHooksRegistration(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(REGISTRATION.read_text())

    def test_is_well_formed_object(self):
        self.assertIsInstance(self.data, dict)
        self.assertIn("PreToolUse", self.data["hooks"])

    def test_expected_matchers_present(self):
        matchers = {entry["matcher"] for entry in self.data["hooks"]["PreToolUse"]}
        self.assertEqual(matchers, {"Write|Edit", "Bash", "Read|Glob|Grep"})

    def test_referenced_scripts_exist(self):
        for entry in self.data["hooks"]["PreToolUse"]:
            for hook in entry["hooks"]:
                script_arg = hook["args"][-1]
                script_name = script_arg.rsplit("/", 1)[-1]
                self.assertTrue(
                    (HOOKS / script_name).is_file(),
                    f"missing hook script: {script_name}",
                )

    def test_each_matcher_maps_to_expected_script(self):
        expected = {
            "Write|Edit": "write-guard.py",
            "Bash": "command-guard.py",
            "Read|Glob|Grep": "read-guard.py",
        }
        for entry in self.data["hooks"]["PreToolUse"]:
            script_name = entry["hooks"][0]["args"][-1].rsplit("/", 1)[-1]
            self.assertEqual(script_name, expected[entry["matcher"]])


if __name__ == "__main__":
    unittest.main()
