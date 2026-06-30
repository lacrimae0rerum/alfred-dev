# Alfred Codex MVP PRD

## Purpose

Alfred Codex is a Codex-native MVP port of the Alfred Dev workflow system. It keeps the useful workflow behavior while removing Claude-only integration points. The MVP gives Codex one main skill, six reusable software delivery flows, neutral project state paths, a lightweight project memory MCP server, and validation tests.

## Problem

Alfred Dev is currently shaped around Claude Code surfaces: slash commands, `Agent` tool assumptions, `.claude/` state, hooks, and `${CLAUDE_PLUGIN_ROOT}`. Those contracts cannot be copied directly into Codex without creating broken entrypoints. The MVP must preserve the workflow semantics and evidence discipline while adopting Codex plugin, skill, MCP, and local runtime conventions.

## Goals

- Provide a valid standalone Codex plugin.
- Expose one main invocable skill, `alfred-for-codex`, as the user entrypoint.
- Preserve MVP flow behavior for `feature`, `quick`, `fix`, `spike`, `audit`, and `ship`.
- Use neutral project state under `.codex/alfred/` instead of `.claude/`.
- Provide a reusable memory MCP server that starts without Claude environment variables.
- Include tests that validate manifest shape, flow definitions, memory behavior, state paths, and public documentation safety.
- Document known compatibility gaps clearly.

## Non-Goals

- Full parity with the 63k-line Claude plugin and its entire test surface.
- Claude slash commands, Claude hooks, or Claude `Agent` tool contracts.
- Visual Selina browser flows beyond documenting the compatibility gap.
- SonarQube automation, Docker setup, installer scripts, or release packaging beyond plugin validation.

## Users

- A Codex user who wants Alfred-style software workflow structure inside a project.
- A maintainer comparing Alfred Dev source behavior against the Codex MVP.
- A future agent continuing the port toward parity.

## MVP Behavior

The main skill classifies user requests into one of six flows:

| Flow | Use | MVP Phases |
| --- | --- | --- |
| `feature` | New product functionality | product, optional visual style, architecture, development, quality, documentation, delivery |
| `quick` | Small local change | bounded execution, quick validation |
| `fix` | Bug correction | diagnosis, correction, validation |
| `spike` | Technical investigation | exploration, conclusions |
| `audit` | Project review | parallel audit |
| `ship` | Release preparation | final audit, documentation, packaging, deployment |

Each phase has agents as role labels, execution mode, gate type, and a short description. Codex may use available subagent or tool orchestration surfaces when present, but the MVP does not depend on a Claude-style `Agent` tool.

## State and Memory

- State root: `<project>/.codex/alfred/`
- Flow state: `<project>/.codex/alfred/state.json`
- Local config: `<project>/.codex/alfred/config.local.md`
- Memory DB: `<project>/.codex/alfred/memory.db`

The memory server exposes safe MCP tools for search, decision logging, event logging, stats, and iteration inspection. Text is sanitized before persistence with the same broad secret categories used by Alfred Dev.

## Success Criteria

- Codex plugin validator passes.
- Skill validation passes.
- Python tests pass.
- `.mcp.json` contains no Claude-specific environment variables.
- Generated docs do not present Claude-only installation instructions as Codex instructions.
- Known gaps are recorded in `docs/BUGS.md`.
