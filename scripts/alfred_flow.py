#!/usr/bin/env python3
"""Inspect and start Alfred Codex MVP flows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alfred_core.flows import FLOWS, create_session, save_state  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Alfred Codex flow helper")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List available flows")
    show = sub.add_parser("show", help="Show one flow definition")
    show.add_argument("flow")
    start = sub.add_parser("start", help="Create and persist a flow session")
    start.add_argument("flow")
    start.add_argument("description")
    start.add_argument("--project-dir", default=None)
    start.add_argument("--autopilot", action="store_true")
    args = parser.parse_args()

    if args.command == "list":
        print(json.dumps(sorted(FLOWS.keys()), indent=2))
        return 0
    if args.command == "show":
        if args.flow not in FLOWS:
            parser.error(f"Unknown flow: {args.flow}")
        print(json.dumps(FLOWS[args.flow], indent=2, ensure_ascii=False))
        return 0
    if args.command == "start":
        session = create_session(args.flow, args.description, autopilot=args.autopilot)
        path = save_state(session, args.project_dir)
        print(json.dumps({"state_path": str(path), "session": session}, indent=2, ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
