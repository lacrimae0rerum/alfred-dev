"""Dangerous-command policy.

Pure port of the detection logic from alfred-dev's
``hooks/dangerous-command-guard.py``: tokenization helpers, the ``_detect_*``
family, ``_find_dangerous_reason`` and the safe-helper allowlist. The hook
``main()`` (stdin JSON / exit codes) is intentionally NOT ported -- that is the
Claude Code transport, which a later phase re-adds as an adapter.

``evaluate_command`` is the public entry point and returns a :class:`Decision`.
The policy is **fail-closed**: any unexpected parsing error denies.
"""

import os
import re
import shlex

from .decision import Decision, allow, deny

_SAFE_ALFRED_HELPER_SUBCOMMANDS = frozenset(
    {
        "allow-stop-once",
        "blocked",
        "consume-prefetch",
        "discuss",
        "in-progress",
        "map-codebase",
        "memory-ui",
        "next",
        "pause",
        "progress",
        "quick",
        "resume",
        "search",
        "standup",
        "validate",
        "verify",
    }
)

_SHELL_CONTROL_TOKENS = frozenset(
    {
        ";",
        "&&",
        "||",
        "|",
        ">",
        ">>",
        "<",
        "<<",
        "2>",
        "&>",
        "&>>",
    }
)

_SHELL_CONTROL_SUBSTRINGS = (
    "$(",
    "`",
)

_SAFE_CAPTURE_SUFFIXES = (
    "2>&1",
    "2>/dev/null",
    "2>/dev/null 2>&1",
)


_DROP_SQL_REGEX = re.compile(r"\bDROP\s+(DATABASE|TABLE|SCHEMA)\b", re.IGNORECASE)
_DEVICE_REDIRECT_REGEX = re.compile(r">\s*/dev/(sd|hd|nvme|vd|xvd)\w*", re.IGNORECASE)
_SHELL_WRAPPERS = frozenset({"sh", "bash", "zsh"})
_SQL_CLIENTS = frozenset({"psql", "mysql", "mariadb", "sqlite3", "duckdb"})


def _command_basename(token: str) -> str:
    return os.path.basename(token or "")


def _strip_leading_wrappers(tokens):
    """Drop neutral leading wrappers: sudo, env and inline variable assignments."""
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        base = _command_basename(token)

        if base == "sudo":
            idx += 1
            while idx < len(tokens) and tokens[idx].startswith("-"):
                idx += 1
            continue

        if base == "env":
            idx += 1
            while idx < len(tokens) and "=" in tokens[idx] and not tokens[idx].startswith("-"):
                idx += 1
            continue

        if "=" in token and not token.startswith("-"):
            name, _value = token.split("=", 1)
            if name.replace("_", "").isalnum():
                idx += 1
                continue

        break

    return tokens[idx:]


def _strip_quoted_content(command: str) -> str:
    """Replace quoted content with spaces while preserving operators."""
    result = []
    in_single = False
    in_double = False
    escaped = False

    for char in command:
        if escaped:
            result.append(" " if (in_single or in_double) else char)
            escaped = False
            continue

        if char == "\\":
            escaped = True
            result.append(" " if (in_single or in_double) else char)
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            result.append(" ")
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            result.append(" ")
            continue

        result.append(" " if (in_single or in_double) else char)

    return "".join(result)


def _has_shell_controls_outside_quotes(command: str) -> bool:
    """Detect real shell operators, ignoring text inside quotes.

    Helpers with quoted arguments like ``--raw "login | signup"`` or
    ``--raw "funnel A > B"`` are allowed; what stays blocked is real use of
    operators outside quotes (``;``, ``&&``, ``||``, pipes, redirections).
    """
    in_single = False
    in_double = False
    escaped = False
    idx = 0

    while idx < len(command):
        char = command[idx]

        if escaped:
            escaped = False
            idx += 1
            continue

        if char == "\\":
            escaped = True
            idx += 1
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            idx += 1
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            idx += 1
            continue

        if in_single or in_double:
            idx += 1
            continue

        next_two = command[idx : idx + 2]
        if next_two in {"&&", "||", ">>", "<<"}:
            return True
        if char in {";", "|", ">", "<"}:
            return True
        idx += 1

    return False


def _extract_shell_c_command(tokens):
    """Extract the command embedded in shell wrappers like sh -c / bash -lc."""
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens:
        return None

    base = _command_basename(core_tokens[0])
    if base not in _SHELL_WRAPPERS:
        return None

    idx = 1
    while idx < len(core_tokens):
        token = core_tokens[idx]
        if token == "-c" and idx + 1 < len(core_tokens):
            return core_tokens[idx + 1]
        if token.startswith("-") and "c" in token and idx + 1 < len(core_tokens):
            return core_tokens[idx + 1]
        idx += 1
    return None


def _is_recursive_force_rm(tokens):
    has_recursive = False
    has_force = False
    for token in tokens:
        if token == "--recursive":
            has_recursive = True
        elif token == "--force":
            has_force = True
        elif token.startswith("-") and token != "-":
            flags = token[1:]
            has_recursive = has_recursive or ("r" in flags)
            has_force = has_force or ("f" in flags)
    return has_recursive and has_force


def _is_sensitive_rm_target(target: str) -> bool:
    sensitive_roots = ("/", "/etc", "/usr", "/var", "/boot", "/System")
    home_markers = {"~", "~/", "$HOME", "${HOME}"}

    if target in home_markers or target.startswith("~/"):
        return True
    if target in {"/*", "~/*"}:
        return True
    if target in {"$HOME/*", "${HOME}/*"}:
        return True
    for root in sensitive_roots:
        if target == root or target == f"{root}/*":
            return True
        if root != "/" and target.startswith(root + "/"):
            return True
    return False


def _is_absolute_permission_target(target: str) -> bool:
    return target == "/" or target.startswith("/")


def _detect_rm(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens or _command_basename(core_tokens[0]) != "rm":
        return None
    if not _is_recursive_force_rm(core_tokens[1:]):
        return None
    targets = [token for token in core_tokens[1:] if not token.startswith("-")]
    if any(_is_sensitive_rm_target(target) for target in targets):
        return "Catastrophic deletion: rm -rf over root or system directory"
    return None


def _detect_git_push(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 2:
        return None
    if _command_basename(core_tokens[0]) != "git" or core_tokens[1] != "push":
        return None

    force = any(
        token in {"--force", "--force-with-lease", "-f"}
        or (token.startswith("-") and "f" in token[1:])
        for token in core_tokens[2:]
    )
    if not force:
        return None

    protected_refs = {
        "main",
        "master",
        "origin/main",
        "origin/master",
        "refs/heads/main",
        "refs/heads/master",
    }
    if any(token in protected_refs for token in core_tokens[2:] if not token.startswith("-")):
        return "Force push to protected branch (main/master): risk of history loss"
    return "Force push without an explicit branch: verify you are not on main/master"


def _detect_sql_drop(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens:
        return None
    first = _command_basename(core_tokens[0]).lower()
    if first == "drop":
        if len(core_tokens) > 1 and core_tokens[1].upper() in {"DATABASE", "TABLE", "SCHEMA"}:
            return "Data destruction: DROP DATABASE/TABLE/SCHEMA"
        return None
    if _command_basename(core_tokens[0]) not in _SQL_CLIENTS:
        return None
    if any(_DROP_SQL_REGEX.search(token) for token in core_tokens[1:]):
        return "Data destruction: DROP DATABASE/TABLE/SCHEMA"
    return None


def _detect_docker_prune(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 3:
        return None
    if (
        _command_basename(core_tokens[0]) != "docker"
        or core_tokens[1] != "system"
        or core_tokens[2] != "prune"
    ):
        return None

    has_all = any(
        token in {"-a", "--all"} or (token.startswith("-") and "a" in token[1:])
        for token in core_tokens[3:]
    )
    has_force = any(
        token in {"-f", "--force"} or (token.startswith("-") and "f" in token[1:])
        for token in core_tokens[3:]
    )
    if has_all and has_force:
        return "Docker system prune with -af: removes all container data"
    return None


def _detect_chmod(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 3 or _command_basename(core_tokens[0]) != "chmod":
        return None

    mode_tokens = [token for token in core_tokens[1:] if not token.startswith("-")]
    if not mode_tokens or mode_tokens[0] != "777":
        return None
    targets = mode_tokens[1:]
    if any(_is_absolute_permission_target(target) for target in targets):
        return "Insecure permissions: recursive chmod 777 over root directory"
    return None


def _detect_fork_bomb(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if core_tokens[:3] == [":(){", ":|:&", "};:"]:
        return "Fork bomb: local denial of service"
    return None


def _detect_mkfs(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 2:
        return None
    if not _command_basename(core_tokens[0]).startswith("mkfs."):
        return None
    if any(token.startswith("/dev/") for token in core_tokens[1:]):
        return "Disk format: mkfs over a block device"
    return None


def _detect_dd(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if not core_tokens or _command_basename(core_tokens[0]) != "dd":
        return None
    if any(re.match(r"of=/dev/(sd|hd|nvme|vd|xvd)\w*", token) for token in core_tokens[1:]):
        return "Direct write to block device with dd"
    return None


def _detect_redirection_to_device(command: str):
    stripped = _strip_quoted_content(command)
    if _DEVICE_REDIRECT_REGEX.search(stripped):
        return "Output redirection to a block device"
    return None


def _detect_git_reset(tokens):
    core_tokens = _strip_leading_wrappers(tokens)
    if len(core_tokens) < 4:
        return None
    if _command_basename(core_tokens[0]) != "git" or core_tokens[1] != "reset":
        return None
    if "--hard" in core_tokens[2:] and any(
        token in {"origin/main", "origin/master"} for token in core_tokens[2:]
    ):
        return "git reset --hard to origin/main: discards all local changes"
    return None


def _find_dangerous_reason(command: str):
    """Return the block reason if the command is genuinely dangerous."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = []

    embedded = _extract_shell_c_command(tokens) if tokens else None
    if embedded:
        return _find_dangerous_reason(embedded)

    detectors = (
        _detect_rm,
        _detect_git_push,
        _detect_sql_drop,
        _detect_docker_prune,
        _detect_chmod,
        _detect_fork_bomb,
        _detect_mkfs,
        _detect_dd,
        _detect_git_reset,
    )
    for detector in detectors:
        reason = detector(tokens)
        if reason:
            return reason

    return _detect_redirection_to_device(command)


def _is_safe_alfred_helper_command(command: str) -> bool:
    """Recognize deterministic local helpers that Alfred may self-approve.

    The allowlist is narrow: ``python3`` invoking the local
    ``.claude/alfred-continuity.py`` wrapper with a deterministic operational
    subcommand and no real shell control operators.
    """
    normalized = command.strip()
    for suffix in _SAFE_CAPTURE_SUFFIXES:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)].rstrip()
            break

    if any(marker in normalized for marker in _SHELL_CONTROL_SUBSTRINGS):
        return False

    if _has_shell_controls_outside_quotes(normalized):
        return False

    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return False

    if len(tokens) < 3:
        return False
    if tokens[0] != "python3":
        return False
    if tokens[1] != ".claude/alfred-continuity.py":
        return False
    if tokens[2] not in _SAFE_ALFRED_HELPER_SUBCOMMANDS:
        return False
    if any(token in _SHELL_CONTROL_TOKENS for token in tokens):
        return False
    return True


def evaluate_command(command: str) -> Decision:
    """Decide whether ``command`` is safe to run.

    Allows recognized Alfred helpers, denies a command matching any dangerous
    pattern, allows everything else. Fails closed (deny) on any parse error.
    """
    try:
        if _is_safe_alfred_helper_command(command):
            return allow("recognized safe Alfred helper")
        reason = _find_dangerous_reason(command)
        if reason:
            return deny(reason)
        return allow()
    except Exception as exc:  # fail-closed: never let an unparsed command pass
        return deny(f"command parse failed, blocking by precaution: {exc}")
