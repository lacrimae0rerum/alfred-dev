"""Tests for NoOpAgentRunner -- Port 1 test double.

Verifies that NoOpAgentRunner satisfies the AgentRunner protocol and
returns valid session handles that survive spawn/join/terminate/is_alive.
"""

import unittest

from alfred_core.ports import AgentRunner
from alfred_core.ports.noop import NoOpAgentRunner


class TestNoOpAgentRunnerProtocol(unittest.TestCase):
    """Ensure NoOpAgentRunner satisfies the AgentRunner ABC."""

    def test_satisfies_agent_runner_protocol(self):
        self.assertIsInstance(NoOpAgentRunner(), AgentRunner)

    def test_spawn_returns_agent_session(self):
        runner = NoOpAgentRunner()
        session = runner.spawn("test prompt")
        self.assertIsNotNone(session.session_id)
        self.assertTrue(session.session_id.startswith("noop-"))
        self.assertIsInstance(session.metadata, dict)
        self.assertEqual(session.metadata["type"], "noop")

    def test_spawn_passes_prompt_to_metadata(self):
        runner = NoOpAgentRunner()
        session = runner.spawn("spike: review PR")
        self.assertEqual(session.metadata["prompt"], "spike: review PR")

    def test_spawn_accepts_optional_args(self):
        runner = NoOpAgentRunner()
        session = runner.spawn(
            "test",
            project_dir="/tmp/proj",
            skills=["test-skill"],
            context_from=["job-123"],
            model={"provider": "openrouter", "model": "claude-sonnet-4"},
            deliver="local",
            workdir="/tmp/work",
        )
        self.assertTrue(session.session_id.startswith("noop-"))


class TestNoOpAgentRunnerLifecycle(unittest.TestCase):
    """Test the spawn/join/terminate/is_alive lifecycle."""

    def setUp(self):
        self.runner = NoOpAgentRunner()

    def test_is_alive_returns_true_for_new_session(self):
        session = self.runner.spawn("hello")
        self.assertTrue(self.runner.is_alive(session))

    def test_join_returns_json_status(self):
        session = self.runner.spawn("hello")
        result = self.runner.join(session, "follow-up message")
        self.assertIn("status", result)
        self.assertIn("noop", result)

    def test_terminate_does_not_raise(self):
        session = self.runner.spawn("hello")
        self.runner.terminate(session)  # should not raise
        # After terminate, is_alive may still return True (noop doesn't track state)

    def test_terminate_with_force_does_not_raise(self):
        session = self.runner.spawn("hello")
        self.runner.terminate(session, force=True)

    def test_multiple_spawns_yield_unique_ids(self):
        s1 = self.runner.spawn("first")
        s2 = self.runner.spawn("second")
        self.assertNotEqual(s1.session_id, s2.session_id)


if __name__ == "__main__":
    unittest.main()
