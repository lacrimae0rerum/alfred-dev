---
name: alfred-for-codex
description: "Codex-native Alfred workflow entrypoint. Use when the user explicitly asks for Alfred, Alfred Codex, Alfred-style software delivery, or wants structured feature, quick, fix, spike, audit, or ship flows with project memory and quality gates in Codex."
---

# Alfred for Codex

Use this skill as the single Alfred entrypoint in Codex. Classify the user's request, select the smallest useful flow, create or update an active `/goal` when the user wants sustained execution, and drive the work with Codex-native tools.

## Core Rules

- Use `feature` for new product functionality that needs requirements, architecture, implementation, quality, docs, and delivery.
- Use `quick` for small local changes that still need focused tests and security review.
- Use `fix` for bugs that need diagnosis, a regression test, correction, and validation.
- Use `spike` for research or proof of concept work where production code is not the deliverable.
- Use `audit` for a project review across quality, security, architecture, and documentation.
- Use `ship` for release preparation, packaging, and deployment gating.
- Store Alfred project state under `.codex/alfred/`; do not create `.claude/` as the primary state.
- Treat role names such as `senior-dev`, `qa-engineer`, and `security-officer` as routing guidance. Use actual Codex tools, subagents, or local execution surfaces only when they are available in the current session.
- Never invoke or promise Claude slash commands, Claude hooks, `${CLAUDE_PLUGIN_ROOT}`, or a Claude-only `Agent` tool.

## Runtime Helpers

Use the bundled runtime when deterministic flow data is needed:

```bash
python3 scripts/alfred_flow.py list
python3 scripts/alfred_flow.py show feature
python3 scripts/alfred_flow.py start quick "Small bounded change"
```

Use the memory MCP server when connected, or the Python memory API directly during local validation. Pass `project_dir` explicitly in memory tool arguments when the active project is known. The server stores data in that project's `.codex/alfred/memory.db`; `ALFRED_CODEX_PROJECT_DIR` or `ALFRED_CODEX_MEMORY_DB` may override it. If the server is launched from the plugin directory without project context, it refuses write/read tool calls instead of creating plugin-local memory by accident.

## Flow Execution

1. Read immediate project context before acting: existing task text, `docs/project/` files if present, current git diff, and available tests.
2. Start from the selected flow definition in `alfred_core.flows`.
3. For each phase, run only the work that phase implies and collect evidence before declaring the phase complete.
4. Respect gates:
   - `usuario`: user approval unless autopilot is active.
   - `automatico`: tests or deterministic checks must pass.
   - `libre`: deliverable evidence is enough.
   - `usuario+seguridad`: user approval plus security review.
   - `automatico+seguridad`: checks plus security review.
5. Do not auto-approve a `ship` deployment gate, even in autopilot.
6. If a gate fails, iterate up to the configured maximum. Escalate with concrete evidence when the maximum is reached.

## Progressive Disclosure

- Read `docs/PRD.md` for product scope.
- Read `docs/ROADMAP.md` when planning future parity work.
- Read `docs/BUGS.md` before claiming parity or hook support.
- Keep public docs sanitized for publication.
