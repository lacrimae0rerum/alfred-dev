"""Secret scanning and sanitization shared by memory and tests."""

from __future__ import annotations

import re
from typing import Optional

SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_KEY"),
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "ANTHROPIC_KEY"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "SK_KEY"),
    (
        re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})"),
        "GITHUB_TOKEN",
    ),
    (re.compile(r"xox[bpsa]-[a-zA-Z0-9\-]{10,}"), "SLACK_TOKEN"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "GOOGLE_KEY"),
    (
        re.compile(r"SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}"),
        "SENDGRID_KEY",
    ),
    (
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "PRIVATE_KEY",
    ),
    (
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
        "JWT",
    ),
    (
        re.compile(
            r"(?:mysql|postgresql|postgres|mongodb(?:\+srv)?|redis|amqp)"
            r"://(?:(?:[^/\s\"':@]+:[^/\s\"'@]+)|(?:[^/\s\"'@]{8,}))@"
        ),
        "CONNECTION_STRING",
    ),
    (re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"), "SLACK_WEBHOOK"),
    (
        re.compile(r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"),
        "DISCORD_WEBHOOK",
    ),
    (
        re.compile(
            r"(?i)(?:password|passwd|api_key|apikey|api_secret|secret_key"
            r"|auth_token|access_token|private_key)"
            r"""\s*[:=]\s*["'](?!\[REDACTED:)[^"']{8,}["']"""
        ),
        "HARDCODED_CREDENTIAL",
    ),
]


def find_secret_label(text: str) -> Optional[str]:
    """Return the first detected secret label, if any."""
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(text):
            return label
    return None


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Replace detected secrets with stable redaction markers."""
    if text is None:
        return None
    result = str(text)
    for pattern, label in SECRET_PATTERNS:
        result = pattern.sub(f"[REDACTED:{label}]", result)
    return result


def sanitize_json_value(value):
    """Sanitize strings recursively inside JSON-compatible values."""
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {str(sanitize_text(str(key))): sanitize_json_value(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_json_value(item) for item in value]
    return value
