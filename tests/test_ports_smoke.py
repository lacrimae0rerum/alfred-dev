"""Smoke test: all 6 ports work together as a cohesive adapter.

This test verifies that the full port stack can be instantiated and
used end-to-end without errors — a sanity check that the interfaces
are compatible and the adapter is complete.
"""

import unittest

from alfred_core.ports import (
    AgentRunner,
    HooksPort,
    HostContextPort,
    MemoryPort,
    SkillsPort,
    ToolRegistry,
)
from alfred_core.ports.noop import (
    NoOpAgentRunner,
    NoOpHooksPort,
    NoOpHostContextPort,
    NoOpMemoryPort,
    NoOpSkillsPort,
    NoOpToolRegistry,
)


class TestPortStackSmoke(unittest.TestCase):
    """Verify all 6 port implementations satisfy their protocols."""

    def test_agent_runner_protocol(self):
        runner = NoOpAgentRunner()
        self.assertIsInstance(runner, AgentRunner)
        session = runner.spawn("smoke test")
        self.assertTrue(session.session_id.startswith("noop-"))
        runner.terminate(session)

    def test_memory_port_protocol(self):
        memory = NoOpMemoryPort()
        self.assertIsInstance(memory, MemoryPort)
        memory.save("memory", "test fact")
        facts = memory.load("memory")
        self.assertEqual(len(facts), 1)

    def test_hooks_port_protocol(self):
        hooks = NoOpHooksPort()
        self.assertIsInstance(hooks, HooksPort)
        result = hooks.evaluate_command("echo hello")
        self.assertFalse(result["blocked"])

    def test_skills_port_protocol(self):
        skills = NoOpSkillsPort()
        self.assertIsInstance(skills, SkillsPort)
        skills.create_skill("smoke", "---\nname: s\n---\n\nBody")
        skill = skills.get_skill("smoke")
        self.assertIsNotNone(skill)

    def test_host_context_port_protocol(self):
        ctx = NoOpHostContextPort("/tmp/smoke-test")
        self.assertIsInstance(ctx, HostContextPort)
        self.assertTrue(ctx.state_dir.endswith(".hermes"))

    def test_tool_registry_protocol(self):
        registry = NoOpToolRegistry()
        self.assertIsInstance(registry, ToolRegistry)
        self.assertEqual(registry.resolve("terminal"), "terminal")

    def test_full_stack_integration(self):
        """All ports work together in a single instantiation."""
        runner = NoOpAgentRunner()
        memory = NoOpMemoryPort()
        hooks = NoOpHooksPort()
        skills = NoOpSkillsPort()
        ctx = NoOpHostContextPort("/tmp/integration-test")
        registry = NoOpToolRegistry()

        # Verify all satisfy protocols
        self.assertIsInstance(runner, AgentRunner)
        self.assertIsInstance(memory, MemoryPort)
        self.assertIsInstance(hooks, HooksPort)
        self.assertIsInstance(skills, SkillsPort)
        self.assertIsInstance(ctx, HostContextPort)
        self.assertIsInstance(registry, ToolRegistry)

        # Verify they all work without errors
        session = runner.spawn("integration test")
        memory.save("memory", "integration fact")
        hooks.evaluate_command("ls -la")
        skills.create_skill("int-skill", "---\nname: i\n---\n\nBody")
        _ = ctx.state_dir
        _ = registry.resolve("file")
        runner.terminate(session)


if __name__ == "__main__":
    unittest.main()
