"""Zero-dependency frontmatter parser.

A deliberately small YAML subset, enough for Alfred's prompt frontmatter and
nothing more: scalar ``key: value`` pairs (optionally quoted), CSV values kept
raw, and the ``key: |`` block scalar (whose indented continuation lines may
contain embedded HTML such as ``<example>``). Keeping it dependency-free keeps
the core portable.

Anything outside that subset (flow mappings, anchors, nested structures) is not
supported by design -- the artifacts do not use it.
"""

import textwrap
from typing import Tuple

_DELIM = "---"


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _is_indented_or_blank(line: str) -> bool:
    return line.strip() == "" or line[:1].isspace()


def _parse_meta(lines: list) -> dict:
    meta: dict = {}
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.rstrip("\n")
        if stripped.strip() == "" or ":" not in stripped or stripped[:1].isspace():
            idx += 1
            continue

        key, _, raw_value = stripped.partition(":")
        key = key.strip()
        raw_value = raw_value.strip()

        if raw_value == "|" or raw_value.startswith("|"):
            # Block scalar: collect following indented/blank lines.
            block = []
            idx += 1
            while idx < len(lines) and _is_indented_or_blank(lines[idx]):
                block.append(lines[idx])
                idx += 1
            meta[key] = textwrap.dedent("".join(block)).strip("\n")
            continue

        meta[key] = _unquote(raw_value)
        idx += 1
    return meta


def parse_frontmatter(text: str) -> Tuple[dict, str]:
    """Split ``text`` into ``(meta, body)``.

    Returns ``({}, text)`` when there is no leading ``---`` frontmatter block or
    when the closing delimiter is missing.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n").strip() != _DELIM:
        return {}, text

    close_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\n").strip() == _DELIM:
            close_idx = idx
            break
    if close_idx is None:
        return {}, text

    meta = _parse_meta(lines[1:close_idx])
    body = "".join(lines[close_idx + 1 :])
    return meta, body
