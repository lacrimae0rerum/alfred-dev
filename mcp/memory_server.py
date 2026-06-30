#!/usr/bin/env python3
"""Stdio MCP server for Alfred Codex project memory."""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from alfred_core.memory import MemoryDB, resolve_memory_db_path  # noqa: E402
from alfred_core.paths import PROJECT_DIR_ENV, resolve_project_dir  # noqa: E402

logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, os.environ.get("ALFRED_MEMORY_LOG_LEVEL", "WARNING").upper(), logging.WARNING),
    format="[alfred-memory] %(levelname)s: %(message)s",
)
LOG = logging.getLogger("alfred-memory")

SERVER_INFO = {"name": "alfred-memory", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"

TOOLS: list[dict[str, Any]] = [
    {
        "name": "memory_start_iteration",
        "description": "Start a new Alfred Codex memory iteration for the current project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "description": {"type": "string"},
                "project_dir": {"type": "string"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "memory_log_decision",
        "description": "Log a sanitized design or workflow decision.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "chosen": {"type": "string"},
                "context": {"type": "string"},
                "alternatives": {"type": "array", "items": {"type": "string"}},
                "rationale": {"type": "string"},
                "impact": {"type": "string"},
                "phase": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "iteration_id": {"type": "integer"},
                "project_dir": {"type": "string"},
            },
            "required": ["title", "chosen"],
        },
    },
    {
        "name": "memory_log_event",
        "description": "Log a sanitized flow event.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "phase": {"type": "string"},
                "payload": {"type": "object"},
                "summary": {"type": "string"},
                "content": {"type": "string"},
                "iteration_id": {"type": "integer"},
                "project_dir": {"type": "string"},
            },
            "required": ["event_type"],
        },
    },
    {
        "name": "memory_search",
        "description": "Search sanitized Alfred Codex memory entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                "project_dir": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "memory_get_iteration",
        "description": "Return an iteration by id, or the latest iteration when omitted.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "iteration_id": {"type": "integer"},
                "project_dir": {"type": "string"},
            },
        },
    },
    {
        "name": "memory_stats",
        "description": "Return memory database path, schema version, and row counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string"},
            },
        },
    },
]


def _jsonrpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _content(payload: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
        "isError": is_error,
    }


def _db_path_for_request(project_dir: str | Path | None = None) -> Path:
    resolved_project_dir = resolve_project_dir(project_dir)
    return resolve_memory_db_path(resolved_project_dir)


def _project_dir_from_args(args: dict[str, Any], project_dir: str | Path | None = None) -> str | Path | None:
    explicit = args.pop("project_dir", None)
    if explicit:
        return explicit
    if project_dir is not None:
        return project_dir
    if os.environ.get(PROJECT_DIR_ENV):
        return None
    cwd = Path.cwd().resolve()
    if cwd == PLUGIN_ROOT:
        raise RuntimeError(
            "Project directory is ambiguous. Pass 'project_dir' or set "
            f"{PROJECT_DIR_ENV} to avoid writing memory inside the plugin."
        )
    return cwd


def call_tool(name: str, arguments: dict[str, Any] | None = None, *, project_dir: str | Path | None = None) -> Any:
    """Dispatch one memory tool and return JSON-compatible data."""
    args = dict(arguments or {})
    resolved_project_dir = _project_dir_from_args(args, project_dir)
    with MemoryDB(_db_path_for_request(resolved_project_dir)) as db:
        if name == "memory_start_iteration":
            iteration_id = db.start_iteration(
                str(args["command"]),
                args.get("description"),
            )
            return {"iteration_id": iteration_id}
        if name == "memory_log_decision":
            decision_id = db.log_decision(
                title=str(args["title"]),
                chosen=str(args["chosen"]),
                context=args.get("context"),
                alternatives=args.get("alternatives"),
                rationale=args.get("rationale"),
                impact=args.get("impact"),
                phase=args.get("phase"),
                iteration_id=args.get("iteration_id"),
                tags=args.get("tags"),
            )
            return {"decision_id": decision_id}
        if name == "memory_log_event":
            event_id = db.log_event(
                event_type=str(args["event_type"]),
                phase=args.get("phase"),
                payload=args.get("payload"),
                summary=args.get("summary"),
                content=args.get("content"),
                iteration_id=args.get("iteration_id"),
            )
            return {"event_id": event_id}
        if name == "memory_search":
            return {"results": db.search(str(args["query"]), int(args.get("limit", 20)))}
        if name == "memory_get_iteration":
            return {"iteration": db.get_iteration(args.get("iteration_id"))}
        if name == "memory_stats":
            return db.stats()
    raise ValueError(f"Unknown tool: {name}")


def handle_request(payload: dict[str, Any], *, project_dir: str | Path | None = None) -> dict[str, Any] | None:
    """Handle one JSON-RPC request or notification."""
    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    try:
        if method == "initialize":
            return _jsonrpc_result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                },
            )
        if method == "initialized":
            return None
        if method == "tools/list":
            return _jsonrpc_result(request_id, {"tools": TOOLS})
        if method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str):
                return _jsonrpc_error(request_id, -32602, "tools/call requires string param 'name'")
            arguments = params.get("arguments") or {}
            if not isinstance(arguments, dict):
                return _jsonrpc_error(request_id, -32602, "tools/call param 'arguments' must be an object")
            result = call_tool(name, arguments, project_dir=project_dir)
            return _jsonrpc_result(request_id, _content(result))
        return _jsonrpc_error(request_id, -32601, f"Method not found: {method}")
    except KeyError as exc:
        return _jsonrpc_error(request_id, -32602, f"Missing required argument: {exc}")
    except RuntimeError as exc:
        return _jsonrpc_error(request_id, -32000, str(exc))
    except Exception as exc:  # pragma: no cover - exercised by manual MCP clients
        LOG.debug("tool failure", exc_info=True)
        return _jsonrpc_error(request_id, -32000, str(exc), traceback.format_exc())


def serve() -> int:
    """Serve newline-delimited JSON-RPC over stdio."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _jsonrpc_error(None, -32700, f"Parse error: {exc}")
        else:
            if not isinstance(payload, dict):
                response = _jsonrpc_error(None, -32600, "Invalid Request")
            else:
                response = handle_request(payload)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(serve())
