"""Smoke tests: the extracted package imports cleanly and is self-contained.

Covers acceptance criteria 2 and 3 of PRD 0001: every public module imports
without error, and the package carries no residual ``core.`` dependency.
"""

import importlib
import unittest


class TestPackageImports(unittest.TestCase):
    MODULES = [
        "alfred_core.secrets",
        "alfred_core.memory_config",
        "alfred_core.optional_agents",
        "alfred_core.personality",
        "alfred_core.memory",
        "alfred_core.config_loader",
        "alfred_core.orchestrator",
    ]

    def test_all_modules_import(self):
        for name in self.MODULES:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_package_version_exposed(self):
        import alfred_core

        self.assertTrue(hasattr(alfred_core, "__version__"))

    def test_no_residual_legacy_core_import(self):
        # The old plugin imported from ``core.*``; nothing should resolve that
        # name transitively. Importing the package must not pull a top-level
        # ``core`` module into sys.modules from our code.
        import sys

        for name in self.MODULES:
            importlib.import_module(name)
        # A stray top-level ``core`` module would indicate a missed rewrite.
        self.assertNotIn("core", sys.modules)


if __name__ == "__main__":
    unittest.main()
