from __future__ import annotations

import json
import tempfile
import unittest

from alfred_core.memory import MemoryDB, resolve_memory_db_path
from mcp.memory_server import handle_request


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
        init = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init["result"]["serverInfo"]["name"], "alfred-memory")
        listed = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertIn("memory_stats", names)
        self.assertIn("memory_log_decision", names)

    def test_mcp_safe_tool_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            start = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "memory_start_iteration",
                        "arguments": {"command": "quick", "description": "MCP smoke"},
                    },
                },
                project_dir=tmp,
            )
            start_text = start["result"]["content"][0]["text"]
            iteration_id = json.loads(start_text)["iteration_id"]
            self.assertGreater(iteration_id, 0)

            stats = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "memory_stats", "arguments": {}},
                },
                project_dir=tmp,
            )
            stats_payload = json.loads(stats["result"]["content"][0]["text"])
            self.assertEqual(stats_payload["counts"]["iterations"], 1)
            self.assertIn(".codex/alfred/memory.db", stats_payload["db_path"])

    def test_mcp_requires_project_context_when_running_from_plugin_root(self) -> None:
        response = handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "memory_stats", "arguments": {}},
            }
        )
        self.assertIn("error", response)
        self.assertIn("Project directory is ambiguous", response["error"]["message"])

    def test_mcp_accepts_project_dir_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            response = handle_request(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {
                        "name": "memory_stats",
                        "arguments": {"project_dir": tmp},
                    },
                }
            )
            payload = json.loads(response["result"]["content"][0]["text"])
            self.assertIn(tmp, payload["db_path"])


if __name__ == "__main__":
    unittest.main()
