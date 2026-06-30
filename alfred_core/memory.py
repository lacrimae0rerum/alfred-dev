"""SQLite project memory for Alfred Codex."""

from __future__ import annotations

import json
import sqlite3
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import memory_path
from .secrets import sanitize_json_value, sanitize_text

DB_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS iterations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id INTEGER REFERENCES iterations(id),
    title TEXT NOT NULL,
    context TEXT,
    chosen TEXT NOT NULL,
    alternatives TEXT,
    rationale TEXT,
    impact TEXT,
    phase TEXT,
    tags TEXT DEFAULT '[]',
    status TEXT DEFAULT 'active',
    decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id INTEGER REFERENCES iterations(id),
    event_type TEXT NOT NULL,
    phase TEXT,
    payload TEXT,
    summary TEXT,
    content TEXT,
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_memory_db_path(project_dir: str | Path | None = None) -> Path:
    """Resolve the memory DB path without using Claude-specific defaults."""
    return memory_path(project_dir)


class MemoryDB:
    """Small SQLite memory API for Alfred Codex."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(SCHEMA_SQL)
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("schema_version", "1"),
        )
        self._conn.commit()
        try:
            self.db_path.chmod(DB_PERMISSIONS)
        except OSError:
            pass

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "MemoryDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start_iteration(self, command: str, description: str | None = None) -> int:
        """Start a memory iteration."""
        cursor = self._conn.execute(
            "INSERT INTO iterations (command, description, status, started_at) VALUES (?, ?, 'active', ?)",
            (sanitize_text(command), sanitize_text(description), _now()),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def complete_iteration(self, iteration_id: int, status: str = "completed") -> None:
        """Complete or abandon an iteration."""
        self._conn.execute(
            "UPDATE iterations SET status = ?, completed_at = ? WHERE id = ?",
            (sanitize_text(status), _now(), int(iteration_id)),
        )
        self._conn.commit()

    def get_active_iteration(self) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM iterations WHERE status = 'active' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def get_iteration(self, iteration_id: int | None = None) -> dict[str, Any] | None:
        if iteration_id is None:
            row = self._conn.execute("SELECT * FROM iterations ORDER BY id DESC LIMIT 1").fetchone()
        else:
            row = self._conn.execute("SELECT * FROM iterations WHERE id = ?", (int(iteration_id),)).fetchone()
        return dict(row) if row else None

    def log_decision(
        self,
        *,
        title: str,
        chosen: str,
        context: str | None = None,
        alternatives: list[str] | None = None,
        rationale: str | None = None,
        impact: str | None = None,
        phase: str | None = None,
        iteration_id: int | None = None,
        tags: list[str] | None = None,
    ) -> int:
        """Persist a sanitized decision."""
        if iteration_id is None:
            active = self.get_active_iteration()
            if active:
                iteration_id = int(active["id"])
        cursor = self._conn.execute(
            """
            INSERT INTO decisions
            (iteration_id, title, context, chosen, alternatives, rationale, impact, phase, tags, decided_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                iteration_id,
                sanitize_text(title),
                sanitize_text(context),
                sanitize_text(chosen),
                json.dumps([sanitize_text(item) for item in alternatives or []], ensure_ascii=False),
                sanitize_text(rationale),
                sanitize_text(impact),
                sanitize_text(phase),
                json.dumps([sanitize_text(item) for item in tags or []], ensure_ascii=False),
                _now(),
            ),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def log_event(
        self,
        *,
        event_type: str,
        phase: str | None = None,
        payload: dict[str, Any] | None = None,
        summary: str | None = None,
        content: str | None = None,
        iteration_id: int | None = None,
    ) -> int:
        """Persist a sanitized event."""
        if iteration_id is None:
            active = self.get_active_iteration()
            if active:
                iteration_id = int(active["id"])
        cursor = self._conn.execute(
            """
            INSERT INTO events
            (iteration_id, event_type, phase, payload, summary, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                iteration_id,
                sanitize_text(event_type) or "event",
                sanitize_text(phase),
                json.dumps(sanitize_json_value(payload), ensure_ascii=False) if payload is not None else None,
                sanitize_text(summary),
                sanitize_text(content),
                _now(),
            ),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search decisions and events with a safe LIKE fallback."""
        limit = max(1, min(int(limit), 100))
        pattern = f"%{query.replace('%', '').replace('_', '')}%"
        rows: list[dict[str, Any]] = []
        decision_rows = self._conn.execute(
            """
            SELECT 'decision' AS source_type, id, title, context, chosen, rationale, phase, decided_at AS created_at
            FROM decisions
            WHERE title LIKE ? OR context LIKE ? OR chosen LIKE ? OR rationale LIKE ?
            ORDER BY decided_at DESC
            LIMIT ?
            """,
            (pattern, pattern, pattern, pattern, limit),
        ).fetchall()
        rows.extend(dict(row) for row in decision_rows)
        remaining = limit - len(rows)
        if remaining > 0:
            event_rows = self._conn.execute(
                """
                SELECT 'event' AS source_type, id, event_type AS title, summary AS context, content AS chosen, phase, created_at
                FROM events
                WHERE event_type LIKE ? OR summary LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (pattern, pattern, pattern, remaining),
            ).fetchall()
            rows.extend(dict(row) for row in event_rows)
        return rows[:limit]

    def stats(self) -> dict[str, Any]:
        """Return lightweight memory stats."""
        counts = {}
        for table in ("iterations", "decisions", "events"):
            counts[table] = int(self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return {
            "db_path": str(self.db_path),
            "counts": counts,
            "schema_version": "1",
        }
