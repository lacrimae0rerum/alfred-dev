from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from alfred_core.config import load_config
from alfred_core.flows import create_session, load_state, save_state
from alfred_core.paths import config_path, is_codex_neutral_path, memory_path, state_path, state_root


class StatePathTest(unittest.TestCase):
    def test_paths_are_codex_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.assertEqual(state_root(root), root / ".codex" / "alfred")
            self.assertEqual(state_path(root), root / ".codex" / "alfred" / "state.json")
            self.assertEqual(memory_path(root), root / ".codex" / "alfred" / "memory.db")
            self.assertTrue(is_codex_neutral_path(state_path(root)))
            self.assertFalse(is_codex_neutral_path(root / ".claude" / "alfred-dev-state.json"))

    def test_save_and_load_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session("quick", "save me")
            path = save_state(session, tmp)
            self.assertEqual(path, state_path(tmp))
            loaded = load_state(tmp)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["comando"], "quick")

    def test_load_config_from_codex_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = config_path(tmp)
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\nmemoria:\n  enabled: false\nautonomia:\n  entrega: interactivo\n---\nNotas locales\n",
                encoding="utf-8",
            )
            config = load_config(tmp)
            self.assertFalse(config["memoria"]["enabled"])
            self.assertEqual(config["autonomia"]["entrega"], "interactivo")
            self.assertEqual(config["notas"], "Notas locales")


if __name__ == "__main__":
    unittest.main()
