"""Tests for the ``Decision`` value type and its factory helpers.

Covers T2.0 of phase 2: an immutable decision object (allow/deny/ask) plus the
``allow()`` / ``deny()`` / ``ask()`` factories re-exported from the package
root, and the ``blocked`` convenience property.
"""

import dataclasses
import unittest

from alfred_core.guards import Decision, allow, ask, deny


class TestDecisionFactories(unittest.TestCase):
    def test_allow_builds_allow_outcome(self):
        decision = allow()
        self.assertEqual(decision.outcome, "allow")
        self.assertEqual(decision.reason, "")

    def test_deny_carries_reason(self):
        decision = deny("hardcoded AWS key")
        self.assertEqual(decision.outcome, "deny")
        self.assertEqual(decision.reason, "hardcoded AWS key")

    def test_ask_carries_reason(self):
        decision = ask("are you sure?")
        self.assertEqual(decision.outcome, "ask")
        self.assertEqual(decision.reason, "are you sure?")


class TestDecisionImmutability(unittest.TestCase):
    def test_is_frozen_dataclass(self):
        decision = allow()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            decision.outcome = "deny"  # type: ignore[misc]


class TestDecisionBlocked(unittest.TestCase):
    def test_deny_is_blocked(self):
        self.assertTrue(deny("nope").blocked)

    def test_allow_is_not_blocked(self):
        self.assertFalse(allow().blocked)

    def test_ask_is_not_blocked(self):
        self.assertFalse(ask("maybe").blocked)


class TestDecisionConstruction(unittest.TestCase):
    def test_direct_construction_defaults_reason(self):
        decision = Decision(outcome="allow")
        self.assertEqual(decision.reason, "")


if __name__ == "__main__":
    unittest.main()
