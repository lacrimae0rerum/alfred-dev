"""Tests for ``evaluate_read`` (the sensitive-file-read policy).

Ported from ``alfred-dev/tests/test_sensitive_read_guard.py``. The upstream hook
was *informative* (warn, never block); T2.3 promotes the same detection to a
blocking policy: a sensitive file denies, anything else allows.
"""

import unittest

from alfred_core.guards import evaluate_read


def _denied(path: str) -> bool:
    return evaluate_read(path).blocked


class TestSensitiveByBaseName(unittest.TestCase):
    def test_dotenv_base(self):
        self.assertTrue(_denied("/project/.env"))

    def test_dotenv_local(self):
        self.assertTrue(_denied("/project/.env.local"))

    def test_dotenv_production(self):
        self.assertTrue(_denied("/project/.env.production"))

    def test_env_without_dot_is_allowed(self):
        self.assertFalse(_denied("/project/env"))

    def test_pem_file(self):
        self.assertTrue(_denied("/certs/server.pem"))

    def test_key_file(self):
        self.assertTrue(_denied("/certs/private.key"))

    def test_p12_file(self):
        self.assertTrue(_denied("/certs/cert.p12"))

    def test_pfx_file(self):
        self.assertTrue(_denied("/certs/cert.pfx"))

    def test_id_rsa(self):
        self.assertTrue(_denied("/home/user/id_rsa"))

    def test_id_ed25519(self):
        self.assertTrue(_denied("/home/user/id_ed25519"))

    def test_id_rsa_pub_is_allowed(self):
        self.assertFalse(_denied("/home/user/id_rsa.pub"))

    def test_credentials_json(self):
        self.assertTrue(_denied("/secrets/credentials.json"))

    def test_service_account_variant_json(self):
        self.assertTrue(_denied("/secrets/service-account.prod.json"))

    def test_firebase_adminsdk_json(self):
        self.assertTrue(_denied("/secrets/firebase-adminsdk-prod.json"))

    def test_npmrc(self):
        self.assertTrue(_denied("/home/user/.npmrc"))

    def test_pypirc(self):
        self.assertTrue(_denied("/home/user/.pypirc"))

    def test_terraform_state(self):
        self.assertTrue(_denied("/infra/terraform.tfstate"))

    def test_htpasswd(self):
        self.assertTrue(_denied("/etc/.htpasswd"))

    def test_jks(self):
        self.assertTrue(_denied("/app/keystore.jks"))

    def test_keystore(self):
        self.assertTrue(_denied("/app/app.keystore"))


class TestNormalFilesAllowed(unittest.TestCase):
    def test_readme(self):
        self.assertFalse(_denied("/project/README.md"))

    def test_python_file(self):
        self.assertFalse(_denied("/project/main.py"))

    def test_json_config(self):
        self.assertFalse(_denied("/project/config.json"))

    def test_package_json(self):
        self.assertFalse(_denied("/project/package.json"))


class TestSensitiveByPath(unittest.TestCase):
    def test_aws_credentials(self):
        self.assertTrue(_denied("/home/user/.aws/credentials"))

    def test_aws_config(self):
        self.assertTrue(_denied("/home/user/.aws/config"))

    def test_ssh_dir(self):
        self.assertTrue(_denied("/home/user/.ssh/known_hosts"))

    def test_gnupg_dir(self):
        self.assertTrue(_denied("/home/user/.gnupg/private-keys-v1.d/key"))

    def test_docker_config_path(self):
        self.assertTrue(_denied("/home/user/.docker/config.json"))

    def test_kube_config_path(self):
        self.assertTrue(_denied("/home/user/.kube/config"))

    def test_windows_docker_config_path(self):
        self.assertTrue(_denied("C:\\Users\\test\\.docker\\config.json"))

    def test_normal_path_allowed(self):
        self.assertFalse(_denied("/home/user/projects/app/main.py"))

    def test_aws_substring_not_in_path(self):
        self.assertFalse(_denied("/home/user/projects/aws-sdk/index.js"))


class TestEvaluateReadOutcomes(unittest.TestCase):
    def test_sensitive_carries_reason(self):
        decision = evaluate_read("/project/.env")
        self.assertEqual(decision.outcome, "deny")
        self.assertTrue(decision.reason)

    def test_normal_is_allow(self):
        self.assertEqual(evaluate_read("/project/main.py").outcome, "allow")

    def test_empty_path_is_allow(self):
        self.assertEqual(evaluate_read("").outcome, "allow")


if __name__ == "__main__":
    unittest.main()
