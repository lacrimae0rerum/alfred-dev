"""Tests for the neutral prompt spec models (T3.1)."""

import json
import unittest

from alfred_core.compiler.models import AgentSpec, CommandSpec, SkillSpec


class TestAgentSpec(unittest.TestCase):
    def test_to_dict_round_trips_keys(self):
        spec = AgentSpec(
            name="architect",
            description="designs systems",
            tools=["read_file", "shell"],
            model="opus",
            body="# system prompt",
        )
        d = spec.to_dict()
        self.assertEqual(d["name"], "architect")
        self.assertEqual(d["tools"], ["read_file", "shell"])
        self.assertEqual(d["model"], "opus")
        self.assertEqual(d["body"], "# system prompt")

    def test_to_dict_is_json_serializable(self):
        spec = AgentSpec("a", "d", ["shell"], "opus", "b")
        json.dumps(spec.to_dict())  # must not raise


class TestCommandSpec(unittest.TestCase):
    def test_to_dict(self):
        spec = CommandSpec(
            name="feature",
            description="full cycle",
            argument_hint="feature description",
            body="prompt with $ARGUMENTS",
        )
        d = spec.to_dict()
        self.assertEqual(d["name"], "feature")
        self.assertEqual(d["argument_hint"], "feature description")
        self.assertIn("$ARGUMENTS", d["body"])
        json.dumps(d)


class TestSkillSpec(unittest.TestCase):
    def test_to_dict(self):
        spec = SkillSpec(name="choose-stack", description="pick tech", body="content")
        d = spec.to_dict()
        self.assertEqual(d, {"name": "choose-stack", "description": "pick tech", "body": "content"})
        json.dumps(d)


if __name__ == "__main__":
    unittest.main()
