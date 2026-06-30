from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from alfred_core.memory import MemoryDB, resolve_memory_db_path


ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = ROOT / "mcp" / "memory_server.py"


def call_mcp(project_dir: str, *requests: dict) -> list[dict]:
    payload = "".join(json.dumps(request) + "\n" for request in requests)
    process = subprocess.run(
        [sys.executable, "-B", str(MCP_SERVER)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=project_dir,
        timeout=10,
    )
    if process.returncode != 0:
        raise AssertionError(process.stderr)
    return [
        json.loads(line)
        for line in process.stdout.splitlines()
        if line.strip()
    ]


class MemoryAndMCPTest(unittest.TestCase):
    def test_memory_sanitizes_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = MemoryDB(resolve_memory_db_path(tmp))
            db.start_iteration("feature", "OAuth work")
            db.log_decision(
                title="Token storage",
                chosen="Use vault",
                context="Do not store sk-abcdefghijklmnopqrstuvwxyz in config",
                tags=["security"],
            )
            results = db.search("Token")
            self.assertEqual(len(results), 1)
            self.assertIn("[REDACTED:SK_KEY]", results[0]["context"])
            db.close()

    def test_mcp_initialize_and_tools_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            init, listed = call_mcp(
                tmp,
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            )
            self.assertEqual(init["result"]["serverInfo"]["name"], "alfred-memory")
            names = {tool["name"] for tool in listed["result"]["tools"]}
            self.assertIn("memory_stats", names)
            self.assertIn("memory_log_decision", names)

    def test_mcp_safe_tool_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            start, stats = call_mcp(
                tmp,
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "memory_manage_iteration",
                        "arguments": {
                            "action": "start",
                            "command": "quick",
                            "description": "MCP smoke",
                        },
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "memory_stats", "arguments": {}},
                },
            )
            start_text = start["result"]["content"][0]["text"]
            iteration_id = json.loads(start_text)["iteration_id"]
            self.assertGreater(iteration_id, 0)

            stats_payload = json.loads(stats["result"]["content"][0]["text"])
            self.assertEqual(stats_payload["total_iterations"], 1)
            self.assertIn(".codex/alfred-memory.db", stats_payload["db_path"])

    def test_mcp_uses_cwd_as_project_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            [response] = call_mcp(
                tmp,
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {"name": "memory_stats", "arguments": {}},
                },
            )
            payload = json.loads(response["result"]["content"][0]["text"])
            self.assertIn(tmp, payload["db_path"])
            self.assertIn(".codex/alfred-memory.db", payload["db_path"])


if __name__ == "__main__":
    unittest.main()
