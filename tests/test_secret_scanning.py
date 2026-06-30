from __future__ import annotations

import unittest

from alfred_core.secrets import find_secret_label, sanitize_text


class SecretScanningTest(unittest.TestCase):
    def test_sanitize_common_secret_patterns(self) -> None:
        raw = "api_key='sk-abcdefghijklmnopqrstuvwxyz' and token ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ"
        sanitized = sanitize_text(raw)
        self.assertIn("[REDACTED:SK_KEY]", sanitized)
        self.assertIn("[REDACTED:GITHUB_TOKEN]", sanitized)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", sanitized)

    def test_find_secret_label(self) -> None:
        self.assertEqual(find_secret_label("AKIA1234567890ABCDEF"), "AWS_KEY")
        self.assertIsNone(find_secret_label("ordinary text"))


if __name__ == "__main__":
    unittest.main()
