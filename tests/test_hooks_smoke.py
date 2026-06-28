"""End-to-end smoke tests for the thin hook scripts (T2.5b).

Mirrors the upstream alfred-dev guard tests: drive each ``hooks/*.py`` script
as a real subprocess with a PreToolUse-shaped JSON payload and assert the exit
code (2 = blocked, 0 = allowed). The scripts bootstrap ``src/`` onto sys.path,
so no install step is required.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "hooks"


def _run(script: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = {"tool_name": "Test", "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


class TestWriteGuardScript(unittest.TestCase):
    def test_secret_write_is_blocked(self):
        fake_key = "sk-" + "d" * 24
        result = _run("write-guard.py", {"file_path": "/tmp/c.py", "content": f'K="{fake_key}"'})
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_clean_write_is_allowed(self):
        result = _run("write-guard.py", {"file_path": "/tmp/c.py", "content": "print('hi')"})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_edit_new_string_is_scanned(self):
        fake_key = "sk-" + "e" * 24
        result = _run("write-guard.py", {"file_path": "/tmp/c.py", "new_string": f'K="{fake_key}"'})
        self.assertEqual(result.returncode, 2, result.stderr)


class TestCommandGuardScript(unittest.TestCase):
    def test_dangerous_command_is_blocked(self):
        result = _run("command-guard.py", {"command": "rm -rf /"})
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_normal_command_is_allowed(self):
        result = _run("command-guard.py", {"command": "ls -la"})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_safe_helper_auto_approves(self):
        cmd = 'python3 .claude/alfred-continuity.py progress "$PWD"'
        result = _run("command-guard.py", {"command": cmd})
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(
            response["hookSpecificOutput"]["permissionDecision"], "allow"
        )


class TestReadGuardScript(unittest.TestCase):
    def test_sensitive_read_is_blocked(self):
        result = _run("read-guard.py", {"file_path": "/project/.env"})
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_normal_read_is_allowed(self):
        result = _run("read-guard.py", {"file_path": "/project/main.py"})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_path_key_fallback(self):
        result = _run("read-guard.py", {"path": "/home/user/.ssh/id_rsa"})
        self.assertEqual(result.returncode, 2, result.stderr)


class TestFailClosed(unittest.TestCase):
    def test_invalid_json_blocks(self):
        result = subprocess.run(
            [sys.executable, str(HOOKS / "command-guard.py")],
            input="not json{",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == "__main__":
    unittest.main()
