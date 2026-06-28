"""Tests for ``evaluate_command`` (the dangerous-command policy).

Ported from ``alfred-dev/tests/test_dangerous_command_guard.py``, exercising the
pure policy (``evaluate_command``) instead of the hook subprocess. Behavioural
parity with the upstream cases is the acceptance criterion.
"""

import unittest

from alfred_core.guards import evaluate_command
from alfred_core.guards.commands import (
    _has_shell_controls_outside_quotes,
    _is_safe_alfred_helper_command,
)


def _is_dangerous(command: str) -> bool:
    return evaluate_command(command).blocked


class TestDangerousCommands(unittest.TestCase):
    # --- catastrophic deletion ---
    def test_rm_rf_root(self):
        self.assertTrue(_is_dangerous("rm -rf /"))

    def test_rm_rf_root_wildcard(self):
        self.assertTrue(_is_dangerous("rm -rf /*"))

    def test_rm_rf_home(self):
        self.assertTrue(_is_dangerous("rm -rf ~"))

    def test_rm_rf_home_var(self):
        self.assertTrue(_is_dangerous("rm -rf $HOME"))

    def test_rm_rf_etc(self):
        self.assertTrue(_is_dangerous("rm -rf /etc"))

    def test_rm_fr_root(self):
        self.assertTrue(_is_dangerous("rm -fr /"))

    def test_sudo_rm_rf_root(self):
        self.assertTrue(_is_dangerous("sudo rm -rf /"))

    def test_rm_separated_flags(self):
        self.assertTrue(_is_dangerous("rm -r -f /"))

    # --- safe rm ---
    def test_rm_rf_node_modules(self):
        self.assertFalse(_is_dangerous("rm -rf node_modules"))

    def test_rm_rf_dist(self):
        self.assertFalse(_is_dangerous("rm -rf dist/"))

    def test_rm_single_file(self):
        self.assertFalse(_is_dangerous("rm archivo.txt"))

    # --- force push ---
    def test_git_push_force_main(self):
        self.assertTrue(_is_dangerous("git push --force origin main"))

    def test_git_push_f_master(self):
        self.assertTrue(_is_dangerous("git push -f origin master"))

    def test_git_push_normal(self):
        self.assertFalse(_is_dangerous("git push origin feature/nueva"))

    def test_git_push_u(self):
        self.assertFalse(_is_dangerous("git push -u origin main"))

    # --- destructive SQL ---
    def test_drop_database(self):
        self.assertTrue(_is_dangerous("DROP DATABASE produccion"))

    def test_drop_table(self):
        self.assertTrue(_is_dangerous("DROP TABLE users"))

    def test_drop_schema(self):
        self.assertTrue(_is_dangerous("DROP SCHEMA public"))

    def test_drop_case_insensitive(self):
        self.assertTrue(_is_dangerous("drop database produccion"))

    # --- docker prune ---
    def test_docker_system_prune_af(self):
        self.assertTrue(_is_dangerous("docker system prune -af"))

    def test_docker_system_prune_fa(self):
        self.assertTrue(_is_dangerous("docker system prune -f -a"))

    # --- insecure permissions ---
    def test_chmod_777_root(self):
        self.assertTrue(_is_dangerous("chmod 777 /"))

    def test_chmod_R_777_var(self):
        self.assertTrue(_is_dangerous("chmod -R 777 /var"))

    # --- fork bomb ---
    def test_fork_bomb(self):
        self.assertTrue(_is_dangerous(":(){ :|:& };:"))

    # --- disk format / device writes ---
    def test_mkfs_ext4(self):
        self.assertTrue(_is_dangerous("mkfs.ext4 /dev/sda1"))

    def test_dd_to_device(self):
        self.assertTrue(_is_dangerous("dd if=/dev/zero of=/dev/sda"))

    def test_dd_to_nvme(self):
        self.assertTrue(_is_dangerous("dd if=/dev/zero of=/dev/nvme0n1"))

    def test_redirect_to_sda(self):
        self.assertTrue(_is_dangerous("> /dev/sda"))

    # --- git reset --hard ---
    def test_git_reset_hard_origin_main(self):
        self.assertTrue(_is_dangerous("git reset --hard origin/main"))

    def test_git_reset_hard_origin_master(self):
        self.assertTrue(_is_dangerous("git reset --hard origin/master"))

    # --- safe general commands ---
    def test_ls(self):
        self.assertFalse(_is_dangerous("ls -la"))

    def test_git_status(self):
        self.assertFalse(_is_dangerous("git status"))

    def test_npm_install(self):
        self.assertFalse(_is_dangerous("npm install"))

    def test_python_script(self):
        self.assertFalse(_is_dangerous("python3 script.py"))

    def test_docker_build(self):
        self.assertFalse(_is_dangerous("docker build -t myapp ."))

    def test_cat_file(self):
        self.assertFalse(_is_dangerous("cat /etc/hosts"))

    # --- shell wrappers and quoting ---
    def test_detects_shell_wrapper_rm_rf(self):
        self.assertTrue(_is_dangerous('sh -c "rm -rf /"'))

    def test_detects_bash_lc_force_push(self):
        self.assertTrue(_is_dangerous('bash -lc "git push --force origin main"'))

    def test_allows_documented_dangerous_text_in_printf(self):
        self.assertFalse(_is_dangerous("printf '%s\\n' 'git push --force origin main'"))

    def test_allows_grep_for_docker_prune_literal(self):
        self.assertFalse(_is_dangerous('grep -R "docker system prune -af" .'))

    def test_allows_echo_of_fork_bomb_literal(self):
        self.assertFalse(_is_dangerous('echo ":(){ :|:& };:"'))


class TestEvaluateCommandOutcomes(unittest.TestCase):
    def test_dangerous_carries_reason(self):
        decision = evaluate_command("rm -rf /")
        self.assertEqual(decision.outcome, "deny")
        self.assertTrue(decision.reason)

    def test_safe_helper_is_allowed(self):
        command = 'python3 .claude/alfred-continuity.py progress "$PWD"'
        self.assertEqual(evaluate_command(command).outcome, "allow")

    def test_normal_command_is_allowed(self):
        self.assertEqual(evaluate_command("ls -la").outcome, "allow")


class TestSafeAlfredHelpers(unittest.TestCase):
    def test_safe_consume_prefetch_command(self):
        command = (
            'python3 .claude/alfred-continuity.py consume-prefetch "$PWD" '
            "--expected map-codebase"
        )
        self.assertTrue(_is_safe_alfred_helper_command(command))

    def test_safe_helper_with_capture_suffix(self):
        command = (
            'python3 .claude/alfred-continuity.py consume-prefetch "$PWD" '
            "--expected map-codebase 2>&1"
        )
        self.assertTrue(_is_safe_alfred_helper_command(command))

    def test_allows_quoted_pipe_like_text(self):
        self.assertTrue(
            _is_safe_alfred_helper_command(
                'python3 .claude/alfred-continuity.py search "$PWD" --raw "login | signup"'
            )
        )

    def test_rejects_shell_chaining(self):
        command = (
            'python3 .claude/alfred-continuity.py map-codebase "$PWD" --raw "login"; rm -rf /'
        )
        self.assertFalse(_is_safe_alfred_helper_command(command))

    def test_rejects_command_substitution_even_if_quoted(self):
        command = 'python3 .claude/alfred-continuity.py discuss "$PWD" --raw "$(whoami)"'
        self.assertFalse(_is_safe_alfred_helper_command(command))

    def test_has_shell_controls_outside_quotes(self):
        self.assertTrue(_has_shell_controls_outside_quotes("echo hola && whoami"))
        self.assertFalse(_has_shell_controls_outside_quotes('echo "hola && adios"'))
        self.assertFalse(_has_shell_controls_outside_quotes("echo 'a | b ; c > d'"))


if __name__ == "__main__":
    unittest.main()
