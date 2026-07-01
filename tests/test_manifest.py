from __future__ import annotations

import json
import os
import subprocess
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManifestTest(unittest.TestCase):
    def test_plugin_manifest_is_valid_shape(self) -> None:
        payload = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "alfred-dev")
        self.assertEqual(payload["version"], "0.6.1+codex.1")
        self.assertEqual(payload["skills"], "./skills/")
        self.assertEqual(payload["mcpServers"], "./.mcp.json")
        self.assertIn("author", payload)
        self.assertIn("interface", payload)
        self.assertNotIn("commands", payload)
        self.assertNotIn("hooks", payload)
        self.assertNotIn("[TODO:", json.dumps(payload))

    def test_main_skill_and_mcp_files_are_discoverable(self) -> None:
        skill = ROOT / "skills" / "alfred" / "SKILL.md"
        mcp = ROOT / ".mcp.json"
        self.assertTrue(skill.is_file())
        self.assertTrue(mcp.is_file())
        mcp_payload = json.loads(mcp.read_text(encoding="utf-8"))
        server = mcp_payload["mcpServers"]["alfred-memory"]
        self.assertEqual(server["command"], "python3")
        self.assertEqual(server["args"][:2], ["-B", "-c"])
        self.assertIn("plugins", server["args"][2])
        self.assertIn("cache", server["args"][2])
        self.assertNotIn("/" + "Users" + "/", json.dumps(server))
        env_text = json.dumps(server.get("env", {})).lower()
        self.assertNotIn("claude", env_text)

    def test_mcp_launcher_starts_outside_plugin_root(self) -> None:
        payload = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        server = payload["mcpServers"]["alfred-memory"]
        request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        env = os.environ.copy()
        env["ALFRED_CODEX_PLUGIN_ROOT"] = str(ROOT)
        process = subprocess.run(
            [server["command"], *server["args"]],
            input=json.dumps(request) + "\n",
            text=True,
            capture_output=True,
            cwd=Path.home(),
            env=env,
            timeout=5,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        response = json.loads(process.stdout)
        self.assertEqual(response["result"]["serverInfo"]["name"], "alfred-memory")

    def test_repo_local_marketplace_metadata_exists(self) -> None:
        payload = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "alfred-dev-local")
        [entry] = payload["plugins"]
        self.assertEqual(entry["name"], "alfred-dev")
        self.assertEqual(entry["source"]["source"], "local")
        self.assertIn("policy", entry)
        self.assertIn("category", entry)

    def test_alfred_surface_counts_match_public_contract(self) -> None:
        self.assertEqual(len(list((ROOT / "agents").glob("*.md"))), 19)
        self.assertEqual(len(list((ROOT / ".codex" / "agents").glob("*.toml"))), 19)
        self.assertEqual(len(list((ROOT / "skills").glob("*/SKILL.md"))), 87)
        self.assertEqual(len(list((ROOT / "prompts").glob("*.md"))), 26)
        self.assertEqual(len(list((ROOT / "commands").glob("*.md"))), 27)
        self.assertEqual(len(list((ROOT / "templates").glob("*.md"))), 7)
        self.assertTrue((ROOT / "hooks" / "hooks.json").is_file())

    def test_codex_agent_and_hook_files_parse(self) -> None:
        agent_contracts = {path.stem for path in (ROOT / "agents").glob("*.md")}
        codex_agents = {path.stem for path in (ROOT / ".codex" / "agents").glob("*.toml")}
        self.assertEqual(codex_agents, agent_contracts)

        for path in sorted((ROOT / ".codex" / "agents").glob("*.toml")):
            with self.subTest(path=path.name):
                tomllib.loads(path.read_text(encoding="utf-8"))

        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(hooks), {"hooks"})
        self.assertIn("SessionStart", hooks["hooks"])

    def test_alfred_dev_command_skills_are_packaged(self) -> None:
        command_contracts = {
            path.stem
            for path in (ROOT / "commands").glob("*.md")
            if path.stem not in {"_composicion", "alfred"}
        }
        command_skills = {
            path.parent.name
            for path in (ROOT / "skills").glob("*/SKILL.md")
            if path.read_text(encoding="utf-8").startswith("---\nname:")
            and "Alfred Dev command:" in path.read_text(encoding="utf-8")
        }
        self.assertEqual(command_skills, command_contracts)
        self.assertTrue((ROOT / "skills" / "alfred" / "SKILL.md").is_file())

        commands = command_contracts
        for name in sorted(commands):
            with self.subTest(name=name):
                skill = ROOT / "skills" / name / "SKILL.md"
                self.assertTrue(skill.is_file())
                text = skill.read_text(encoding="utf-8")
                self.assertIn(f"name: {name}", text)
                self.assertIn(f"$alfred-dev:{name}", text)
                self.assertIn(f"../../commands/{name}.md", text)


if __name__ == "__main__":
    unittest.main()
