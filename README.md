# alfred-core

Portable, host-agnostic core engine extracted from the [Alfred Dev](https://github.com/686f6c61/alfred-dev)
Claude Code plugin. This is **phase 0** of decoupling Alfred from Claude Code so it
can be driven by other agents/harnesses (see `docs/`).

## What this is

`alfred-core` packages the ~3500 LOC of pure logic that survives any host:

- **`orchestrator`** — the flow/gate state machine (feature, fix, quick, spike, ship, audit).
- **`memory`** — SQLite persistence for decisions, commits, events, iterations (WAL, FTS5).
- **`memory_config`** — memory configuration parsing.
- **`secrets`** — centralized secret patterns and sanitization.
- **`personality`** — agent catalog, voices and tone.
- **`optional_agents`** — optional-agent registry and selection menus.
- **`config_loader`** — project config and stack detection.

It carries **no hard dependency on Claude Code**. The only residual coupling
(path resolution under `.claude/`, and an optional fail-open import of `continuity`)
is tracked as debt for **phase 1** (the `HostContext` port).

## Layout

```
src/alfred_core/      # the package
tests/                # regression suite (carried over + new state-machine tests)
docs/                 # coupling map, portability audit, PRD
```

## Develop

Requires Python 3.12+ and [`uv`](https://github.com/astral-sh/uv).

```bash
uv venv
uv pip install -e ".[dev]"
uv run pytest          # regression gate
uv run ruff check src tests
```

## Status

Phase 0: extraction + regression gate. No public API stability guarantees yet.
See `docs/prd/0001-extraccion-alfred-core.md` for scope and acceptance criteria,
and `docs/2026-06-28-auditoria-portabilidad.md` for the full port plan.
