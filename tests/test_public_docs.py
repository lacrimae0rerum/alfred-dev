from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicDocsTest(unittest.TestCase):
    def test_public_files_do_not_include_local_machine_paths_or_internal_logs(self) -> None:
        public_paths = [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and path.suffix in {".md", ".py", ".json"}
        ]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in public_paths)
        forbidden = [
            "/" + "Users" + "/",
            "fedi" + "rosan",
            "AUTO" + "EXEC_" + "PRO" + "MPT",
            "BITA" + "CORA",
            "Hand" + "off",
            "MVP " + "Loop " + "Hand" + "off",
            "/goal Build " + "Alfred",
        ]
        for fragment in forbidden:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, combined)

    def test_docs_do_not_present_claude_install_as_codex_install(self) -> None:
        docs_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "docs").glob("*.md"))
        forbidden_install_fragments = [
            "~/.claude",
            "claude -p",
            "install.sh",
            "install.ps1",
        ]
        for fragment in forbidden_install_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, docs_text)

    def test_skill_contract_is_codex_native(self) -> None:
        text = (ROOT / "skills" / "alfred-for-codex" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: alfred-for-codex", text)
        self.assertIn(".codex/alfred/", text)
        self.assertIn("Never invoke or promise Claude slash commands", text)
        self.assertNotIn("description: \"Alias global /alfred", text)
        self.assertNotIn("user-invocable: false", text)


if __name__ == "__main__":
    unittest.main()
