"""Tests for NoOpSkillsPort -- Port 4 test double.

Verifies that NoOpSkillsPort satisfies the SkillsPort protocol and
correctly creates, retrieves, lists, and deletes skills.
"""

import unittest

from alfred_core.ports import SkillsPort
from alfred_core.ports.noop import NoOpSkillsPort


class TestNoOpSkillsPortProtocol(unittest.TestCase):
    """Ensure NoOpSkillsPort satisfies the SkillsPort ABC."""

    def test_satisfies_skills_port_protocol(self):
        self.assertIsInstance(NoOpSkillsPort(), SkillsPort)


class TestNoOpSkillsPortCreateGet(unittest.TestCase):
    """Test create and get operations."""

    def setUp(self):
        self.port = NoOpSkillsPort()

    def test_create_skill(self):
        skill_md = "---\nname: test-skill\ndescription: A test skill\n---\n\nTest content."
        path = self.port.create_skill("test-skill", skill_md)
        self.assertTrue(path.endswith("test-skill"))

    def test_create_skill_with_category(self):
        skill_md = "---\nname: cat-skill\ndescription: Categorized\n---\n\nBody."
        path = self.port.create_skill("cat-skill", skill_md, category="devops")
        self.assertTrue(path.endswith("devops/cat-skill"))

    def test_get_existing_skill(self):
        skill_md = "---\nname: my-skill\ndescription: My skill\n---\n\nBody."
        self.port.create_skill("my-skill", skill_md)
        skill = self.port.get_skill("my-skill")
        self.assertIsNotNone(skill)
        assert skill is not None  # narrow for type checker
        self.assertEqual(skill["name"], "my-skill")
        self.assertIn("My skill", skill["content"])

    def test_get_nonexistent_skill(self):
        result = self.port.get_skill("does-not-exist")
        self.assertIsNone(result)

    def test_get_skill_preserves_content(self):
        content = "---\nname: c\n---\n\nFull body text."
        self.port.create_skill("c", content)
        skill = self.port.get_skill("c")
        assert skill is not None
        self.assertEqual(skill["content"], content)


class TestNoOpSkillsPortList(unittest.TestCase):
    """Test list operations."""

    def setUp(self):
        self.port = NoOpSkillsPort()

    def test_empty_list(self):
        skills = self.port.list_skills()
        self.assertEqual(skills, [])

    def test_list_after_create(self):
        self.port.create_skill("skill-a", "---\nname: a\n---\n\nA")
        skills = self.port.list_skills()
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["name"], "skill-a")

    def test_list_multiple_skills(self):
        self.port.create_skill("skill-a", "---\nname: a\n---\n\nA")
        self.port.create_skill("skill-b", "---\nname: b\n---\n\nB")
        skills = self.port.list_skills()
        self.assertEqual(len(skills), 2)
        names = {s["name"] for s in skills}
        self.assertEqual(names, {"skill-a", "skill-b"})

    def test_list_includes_category(self):
        self.port.create_skill("cat-skill", "---\nname: c\n---\n\nC", category="test")
        skills = self.port.list_skills()
        self.assertEqual(skills[0]["category"], "test")


class TestNoOpSkillsPortDelete(unittest.TestCase):
    """Test delete operations."""

    def setUp(self):
        self.port = NoOpSkillsPort()

    def test_delete_existing_skill(self):
        self.port.create_skill("del-me", "---\nname: x\n---\n\nX")
        self.assertTrue(self.port.delete_skill("del-me"))

    def test_delete_nonexistent_skill(self):
        self.assertFalse(self.port.delete_skill("no-such-skill"))

    def test_delete_removes_from_list(self):
        self.port.create_skill("keep", "---\nname: k\n---\n\nK")
        self.port.create_skill("remove", "---\nname: r\n---\n\nR")
        self.port.delete_skill("remove")
        skills = self.port.list_skills()
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]["name"], "keep")


if __name__ == "__main__":
    unittest.main()
