from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManifestTest(unittest.TestCase):
    def test_plugin_manifest_is_valid_shape(self) -> None:
        payload = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "alfred-codex")
        self.assertEqual(payload["version"], "0.1.0")
        self.assertEqual(payload["skills"], "./skills/")
        self.assertEqual(payload["mcpServers"], "./.mcp.json")
        self.assertIn("author", payload)
        self.assertIn("interface", payload)
        self.assertNotIn("commands", payload)
        self.assertNotIn("hooks", payload)
        self.assertNotIn("[TODO:", json.dumps(payload))

    def test_main_skill_and_mcp_files_are_discoverable(self) -> None:
        skill = ROOT / "skills" / "alfred-for-codex" / "SKILL.md"
        mcp = ROOT / ".mcp.json"
        self.assertTrue(skill.is_file())
        self.assertTrue(mcp.is_file())
        mcp_payload = json.loads(mcp.read_text(encoding="utf-8"))
        server = mcp_payload["mcpServers"]["alfred-memory"]
        self.assertEqual(server["command"], "python3")
        self.assertEqual(server["args"], ["mcp/memory_server.py"])
        env_text = json.dumps(server.get("env", {})).lower()
        self.assertNotIn("claude", env_text)

    def test_repo_local_marketplace_metadata_exists(self) -> None:
        payload = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "alfred-codex-local")
        [entry] = payload["plugins"]
        self.assertEqual(entry["name"], "alfred-codex")
        self.assertEqual(entry["source"]["source"], "local")
        self.assertIn("policy", entry)
        self.assertIn("category", entry)


if __name__ == "__main__":
    unittest.main()
