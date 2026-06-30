"""Tests for NoOpMemoryPort -- Port 2 test double.

Verifies that NoOpMemoryPort satisfies the MemoryPort protocol and
correctly stores, retrieves, deletes, and searches facts.
"""

import unittest

from alfred_core.ports import MemoryPort
from alfred_core.ports.noop import NoOpMemoryPort


class TestNoOpMemoryPortProtocol(unittest.TestCase):
    """Ensure NoOpMemoryPort satisfies the MemoryPort ABC."""

    def test_satisfies_memory_port_protocol(self):
        self.assertIsInstance(NoOpMemoryPort(), MemoryPort)


class TestNoOpMemoryPortSaveLoad(unittest.TestCase):
    """Test save and load operations."""

    def setUp(self):
        self.port = NoOpMemoryPort()

    def test_save_and_load_memory_target(self):
        self.port.save("memory", "User prefers concise responses")
        facts = self.port.load("memory")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0], "User prefers concise responses")

    def test_save_and_load_user_target(self):
        self.port.save("user", "User name is Alice")
        facts = self.port.load("user")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0], "User name is Alice")

    def test_multiple_saves_accumulate(self):
        self.port.save("memory", "fact one")
        self.port.save("memory", "fact two")
        facts = self.port.load("memory")
        self.assertEqual(len(facts), 2)
        self.assertIn("fact one", facts)
        self.assertIn("fact two", facts)

    def test_save_to_new_target_creates_it(self):
        self.port.save("new_target", "new fact")
        facts = self.port.load("new_target")
        self.assertEqual(len(facts), 1)

    def test_load_empty_target_returns_empty_list(self):
        facts = self.port.load("nonexistent")
        self.assertEqual(facts, [])


class TestNoOpMemoryPortDelete(unittest.TestCase):
    """Test delete operations."""

    def setUp(self):
        self.port = NoOpMemoryPort()

    def test_delete_existing_fact(self):
        self.port.save("memory", "delete me")
        self.assertTrue(self.port.delete("memory", "delete me"))

    def test_delete_nonexistent_fact(self):
        self.assertFalse(self.port.delete("memory", "does not exist"))

    def test_delete_partial_match(self):
        self.port.save("memory", "User prefers concise responses")
        self.assertTrue(self.port.delete("memory", "concise"))

    def test_delete_removes_from_store(self):
        self.port.save("memory", "fact one")
        self.port.save("memory", "fact two")
        self.port.delete("memory", "fact one")
        facts = self.port.load("memory")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0], "fact two")


class TestNoOpMemoryPortSearch(unittest.TestCase):
    """Test search operations."""

    def setUp(self):
        self.port = NoOpMemoryPort()

    def test_search_finds_matching_fact(self):
        self.port.save("memory", "User prefers concise responses")
        results = self.port.search("memory", "concise")
        self.assertEqual(len(results), 1)

    def test_search_case_insensitive(self):
        self.port.save("memory", "User prefers CONcise responses")
        results = self.port.search("memory", "concise")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        self.port.save("memory", "User prefers concise responses")
        results = self.port.search("memory", "verbose")
        self.assertEqual(results, [])

    def test_search_empty_store(self):
        results = self.port.search("memory", "anything")
        self.assertEqual(results, [])

    def test_search_across_multiple_facts(self):
        self.port.save("memory", "User prefers concise")
        self.port.save("memory", "User prefers Spanish")
        results = self.port.search("memory", "User")
        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
