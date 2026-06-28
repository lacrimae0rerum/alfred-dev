"""Tests for the per-artifact compilers (T3.3), driven by hermetic fixtures."""

import unittest
from pathlib import Path

from alfred_core.compiler.compile import (
    compile_agent,
    compile_command,
    compile_skill,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "prompts"


class TestCompileAgent(unittest.TestCase):
    def setUp(self):
        self.spec = compile_agent((FIXTURES / "agents" / "architect.md").read_text())

    def test_name_and_model(self):
        self.assertEqual(self.spec.name, "architect")
        self.assertEqual(self.spec.model, "opus")

    def test_tools_are_mapped(self):
        self.assertEqual(
            self.spec.tools, ["glob", "grep", "read_file", "write_file", "shell"]
        )

    def test_description_kept(self):
        self.assertIn("system architecture", self.spec.description)

    def test_body_preserved_after_frontmatter(self):
        self.assertIn("You are the architect.", self.spec.body)
        self.assertNotIn("name: architect", self.spec.body)


class TestCompileCommand(unittest.TestCase):
    def setUp(self):
        text = (FIXTURES / "commands" / "feature.md").read_text()
        self.spec = compile_command("feature", text)

    def test_name_from_argument(self):
        self.assertEqual(self.spec.name, "feature")

    def test_argument_hint(self):
        self.assertEqual(self.spec.argument_hint, "Description of the feature to build")

    def test_body_keeps_arguments_placeholder(self):
        self.assertIn("$ARGUMENTS", self.spec.body)


class TestCompileSkill(unittest.TestCase):
    def setUp(self):
        text = (FIXTURES / "skills" / "choose-stack" / "SKILL.md").read_text()
        self.spec = compile_skill(text)

    def test_name_and_description(self):
        self.assertEqual(self.spec.name, "choose-stack")
        self.assertIn("weighted decision matrix", self.spec.description)

    def test_body_kept(self):
        self.assertIn("evaluates technology alternatives", self.spec.body)


if __name__ == "__main__":
    unittest.main()
