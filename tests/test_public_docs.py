from __future__ import annotations

import importlib.util
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
            "MVP " + "Loop " + "Hand" + "off",
            "/goal Build " + "Alfred",
        ]
        for fragment in forbidden:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, combined)

    def test_docs_do_not_present_claude_install_as_codex_install(self) -> None:
        docs_text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "docs").rglob("*.md"))
        forbidden_install_fragments = [
            "~/.claude",
            "claude -p",
            "CLAUDE_PLUGIN_ROOT",
        ]
        for fragment in forbidden_install_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, docs_text)

    def test_skill_contract_is_codex_native(self) -> None:
        text = (ROOT / "skills" / "alfred" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: alfred", text)
        self.assertIn(".codex/", text)
        self.assertIn("subagent", text)
        self.assertNotIn("user-invocable: false", text)

    def test_public_help_and_session_context_use_dollar_invocations(self) -> None:
        public_files = [
            ROOT / "commands" / "help.md",
            ROOT / "prompts" / "alfred-dev-help.md",
            ROOT / "hooks" / "session-start.sh",
            ROOT / "hooks" / "prefetch-finish-guard.py",
            ROOT / "core" / "config_cli.py",
            ROOT / "core" / "config_loader.py",
        ]
        for path in public_files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("| `/alfred", text)
                self.assertNotIn("ejecuta `/alfred-dev:", text.lower())
                self.assertNotIn("recomienda `/alfred-dev:", text.lower())
                self.assertNotIn("Usa /alfred-dev:", text)
                self.assertIn("$alfred-dev:", text)

    def test_session_start_context_stays_compact(self) -> None:
        text = (ROOT / "hooks" / "session-start.sh").read_text(encoding="utf-8")
        forbidden_fragments = [
            "### Comandos disponibles",
            "El usuario ha definido preferencias",
            "Muestra de tono de Alfred",
            "Personalidad:",
            "$alfred-dev:feature <descripción>",
            "$alfred-dev:sync-github",
            "memory_sync.py",
            "settings.local.json",
            "api.github.com",
            "Actualización disponible",
        ]
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, text)
        self.assertIn("CONTEXT=\"\"", text)
        self.assertIn("print('{}')", text)

    def test_activity_prefetch_accepts_codex_skill_mentions(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "activity_capture",
            ROOT / "hooks" / "activity-capture.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(
            module._parse_alfred_prefetch_prompt("$alfred-dev:feature login"),
            {"source_command": "feature", "raw_request": "login"},
        )
        self.assertEqual(
            module._parse_alfred_prefetch_prompt("$alfred-dev:alfred que toca"),
            {"source_command": "alfred", "raw_request": "que toca"},
        )
        self.assertEqual(
            module._parse_alfred_prefetch_prompt("/alfred-dev:quick fix"),
            {"source_command": "quick", "raw_request": "fix"},
        )
        self.assertEqual(module._format_alfred_invocation("quick"), "$alfred-dev:quick")
        self.assertEqual(module._format_alfred_invocation("alfred"), "$alfred-dev:alfred")

    def test_continuity_public_text_normalizes_legacy_slash_invocations(self) -> None:
        from core.continuity import _public_codex_text

        text = _public_codex_text(
            "Usa /alfred-dev:next, luego `/alfred-dev:verify aprobado` o /alfred."
        )
        self.assertIn("$alfred-dev:next", text)
        self.assertIn("`$alfred-dev:verify aprobado`", text)
        self.assertIn("$alfred-dev:alfred", text)
        self.assertNotIn("/alfred-dev:", text)


if __name__ == "__main__":
    unittest.main()
