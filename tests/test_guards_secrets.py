"""Tests for ``evaluate_write`` (the secrets-write policy).

Ported from ``alfred-dev/tests/test_secret_guard.py``, but exercising the pure
policy (``evaluate_write``) instead of the hook subprocess. Each upstream case
that tested *detection* (not the exit-code transport) has a counterpart here.
"""

import unittest

from alfred_core.guards import Decision, evaluate_write


class TestEvaluateWriteDetectsSecrets(unittest.TestCase):
    def test_secret_in_source_is_denied(self):
        fake_key = "sk-" + "d" * 24
        decision = evaluate_write("/tmp/config.py", f'OPENAI_API_KEY = "{fake_key}"')
        self.assertTrue(decision.blocked)
        self.assertEqual(decision.outcome, "deny")
        self.assertTrue(decision.reason)

    def test_private_key_header_is_denied(self):
        pem_header = "-----BEGIN " + "PRIVATE KEY-----"
        decision = evaluate_write("/tmp/credentials.py", pem_header)
        self.assertTrue(decision.blocked)

    def test_connection_string_is_denied(self):
        conn_str = "postgres://user:pass@example.com/app"
        decision = evaluate_write("/tmp/settings.py", f'DATABASE_URL = "{conn_str}"')
        self.assertTrue(decision.blocked)

    def test_example_env_does_not_whitelist_secret(self):
        fake_key = "sk-" + "c" * 24
        decision = evaluate_write("/tmp/.env.example", f'OPENAI_API_KEY="{fake_key}"')
        self.assertTrue(decision.blocked)


class TestEvaluateWriteAllows(unittest.TestCase):
    def test_secret_in_env_storage_path_is_allowed(self):
        fake_key = "sk-" + "a" * 24
        decision = evaluate_write("/tmp/.env", f'OPENAI_API_KEY="{fake_key}"')
        self.assertEqual(decision.outcome, "allow")
        self.assertFalse(decision.blocked)

    def test_local_env_storage_path_is_allowed(self):
        fake_key = "sk-" + "b" * 24
        decision = evaluate_write("/tmp/local.env", f'OPENAI_API_KEY="{fake_key}"')
        self.assertEqual(decision.outcome, "allow")

    def test_clean_content_is_allowed(self):
        decision = evaluate_write("/tmp/main.py", "print('hello world')\n")
        self.assertEqual(decision.outcome, "allow")


class TestEvaluateWriteFailClosed(unittest.TestCase):
    def test_scan_failure_denies(self):
        # If the underlying scan raises, the policy must fail closed (deny).
        from alfred_core.guards import secrets_guard

        def boom(_text):
            raise RuntimeError("scanner exploded")

        original = secrets_guard.find_secret_label
        secrets_guard.find_secret_label = boom
        try:
            decision = secrets_guard.evaluate_write("/tmp/x.py", "whatever")
        finally:
            secrets_guard.find_secret_label = original
        self.assertIsInstance(decision, Decision)
        self.assertTrue(decision.blocked)


if __name__ == "__main__":
    unittest.main()
