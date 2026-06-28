"""Tests for HostContext -- the path-resolution port (phase 1).

HostContext centralizes every filesystem convention the core used to hardcode
(``.claude/`` layout) and closes the ``CLAUDE_PROJECT_DIR`` debt: project-dir
resolution follows explicit-arg > CLAUDE_PROJECT_DIR > cwd. The state dir name
is configurable so non-Claude-Code hosts can relocate it.
"""

import os
import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import patch

import alfred_core.orchestrator as orch
from alfred_core.host import HostContext


class TestProjectDirResolution(unittest.TestCase):
    def test_explicit_arg_wins_over_env_and_cwd(self):
        env = {"CLAUDE_PROJECT_DIR": "/from/env"}
        ctx = HostContext.from_env("/explicit/dir", env=env)
        self.assertEqual(ctx.project_dir, os.path.abspath("/explicit/dir"))

    def test_claude_project_dir_used_when_no_explicit_arg(self):
        env = {"CLAUDE_PROJECT_DIR": "/from/env"}
        ctx = HostContext.from_env(env=env)
        self.assertEqual(ctx.project_dir, os.path.abspath("/from/env"))

    def test_falls_back_to_cwd_when_nothing_set(self):
        ctx = HostContext.from_env(env={})
        self.assertEqual(ctx.project_dir, os.path.abspath(os.getcwd()))

    def test_project_dir_is_normalized_absolute(self):
        ctx = HostContext("relative/path")
        self.assertTrue(os.path.isabs(ctx.project_dir))


class TestDerivedPaths(unittest.TestCase):
    def setUp(self):
        self.ctx = HostContext("/proj")

    def test_state_dir_default_is_dot_claude(self):
        self.assertEqual(self.ctx.state_dir, os.path.join(os.path.abspath("/proj"), ".claude"))

    def test_config_path(self):
        self.assertEqual(
            self.ctx.config_path,
            os.path.join(self.ctx.state_dir, "alfred-dev.local.md"),
        )

    def test_state_path(self):
        self.assertEqual(
            self.ctx.state_path,
            os.path.join(self.ctx.state_dir, "alfred-dev-state.json"),
        )

    def test_memory_db_path(self):
        self.assertEqual(
            self.ctx.memory_db_path,
            os.path.join(self.ctx.state_dir, "alfred-memory.db"),
        )


class TestConfigurableStateDir(unittest.TestCase):
    def test_non_claude_host_can_relocate_state_dir(self):
        ctx = HostContext("/proj", state_dir_name=".alfred")
        self.assertTrue(ctx.state_dir.endswith(".alfred"))
        self.assertTrue(ctx.config_path.endswith(os.path.join(".alfred", "alfred-dev.local.md")))

    def test_from_env_propagates_state_dir_name(self):
        ctx = HostContext.from_env("/proj", env={}, state_dir_name=".alfred")
        self.assertEqual(ctx.state_dir_name, ".alfred")


class TestImmutability(unittest.TestCase):
    def test_context_is_frozen(self):
        ctx = HostContext("/proj")
        with self.assertRaises(FrozenInstanceError):
            ctx.project_dir = "/other"  # type: ignore[misc]


class TestOrchestratorWiring(unittest.TestCase):
    """The orchestrator must resolve its project dir through HostContext, so
    CLAUDE_PROJECT_DIR is honored end-to-end (not just in the unit)."""

    def test_run_flow_routes_project_dir_through_hostcontext(self):
        with patch.object(
            orch.HostContext, "from_env", wraps=orch.HostContext.from_env
        ) as spy:
            orch.run_flow("spike", "x", project_dir="/tmp/whatever")
            spy.assert_called_once()
            args, kwargs = spy.call_args
            passed = args[0] if args else kwargs.get("project_dir")
            self.assertEqual(passed, "/tmp/whatever")


if __name__ == "__main__":
    unittest.main()
