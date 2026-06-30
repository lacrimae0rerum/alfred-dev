# Alfred Codex

Alfred Codex is a Codex-native MVP port of Alfred Dev. It provides one main
Codex skill, six Alfred-style software delivery flows, neutral project state
paths, and a lightweight memory MCP server.

This is not full parity with Alfred Dev. Claude slash commands, Claude hooks,
`${CLAUDE_PLUGIN_ROOT}`, Claude `Agent` tool assumptions, Selina's full visual
workflow, and SonarQube automation are intentionally out of scope for this MVP.

## What is included

- Codex plugin manifest: `.codex-plugin/plugin.json`
- Main skill: `skills/alfred-for-codex/SKILL.md`
- Runtime helpers and core logic: `alfred_core/`
- Memory MCP server: `mcp/memory_server.py`
- Flow helper CLI: `scripts/alfred_flow.py`
- Validation tests: `tests/`
- Project docs: `docs/`

Supported MVP flows:

- `feature`
- `quick`
- `fix`
- `spike`
- `audit`
- `ship`

## Validate locally

Run from the repository root:

```bash
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -B "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" .
PYTHONDONTWRITEBYTECODE=1 python3 -B "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/alfred-for-codex
```

Expected result:

- `Ran 24 tests ... OK`
- `Plugin validation passed`
- `Skill is valid!`

## Install in Codex App

This repo is used as a standalone local marketplace.

```bash
codex plugin marketplace add .
codex plugin add alfred-codex@alfred-codex-local
codex plugin list
codex app .
```

Expected `codex plugin list` evidence:

```text
Marketplace `alfred-codex-local`
<repo>/.agents/plugins/marketplace.json

alfred-codex@alfred-codex-local  installed, enabled  0.1.0  <repo>
```

## Use the skill

After installation, start a new Codex thread so the plugin cache is loaded.
Ask for Alfred explicitly, for example:

```text
Use Alfred for Codex to plan this change.
Start an Alfred quick flow for this task.
Search Alfred memory for prior decisions.
```

The skill routes requests to the smallest useful flow and uses Codex-native
tools. It does not expose Claude slash commands.

## Flow helper

Inspect or start flow state locally:

```bash
python3 scripts/alfred_flow.py list
python3 scripts/alfred_flow.py show quick
python3 scripts/alfred_flow.py start quick "Small bounded change" --project-dir /path/to/project
```

State is written under:

```text
<project>/.codex/alfred/state.json
```

## Memory MCP

The MCP server stores project memory under:

```text
<project>/.codex/alfred/memory.db
```

Pass `project_dir` in MCP tool arguments when the active project is known. If
the server is launched from the plugin repository without project context, it
refuses tool calls instead of writing memory inside the plugin.

Smoke test:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import json, subprocess, tempfile

req = {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"memory_stats","arguments":{}}}
p = subprocess.run(["python3","-B","mcp/memory_server.py"], input=json.dumps(req)+"\n", text=True, capture_output=True, timeout=5)
print("no_context_returncode", p.returncode)
print(p.stdout.strip())

with tempfile.TemporaryDirectory() as tmp:
    req = {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"memory_stats","arguments":{"project_dir":tmp}}}
    p = subprocess.run(["python3","-B","mcp/memory_server.py"], input=json.dumps(req)+"\n", text=True, capture_output=True, timeout=5)
    print("with_context_returncode", p.returncode)
    print(p.stdout.strip())
PY
```

Expected behavior:

- without project context: clean JSON-RPC error;
- with `project_dir`: JSON-RPC result with a `.codex/alfred/memory.db` path.

## Known gaps

- No full Alfred Dev parity.
- No Claude slash commands.
- No Claude hooks.
- No Claude `Agent` tool assumptions.
- No full Selina visual workflow.
- No SonarQube/Docker automation.
- Memory MCP is intentionally minimal.

See `docs/BUGS.md` and `docs/ROADMAP.md` for current gaps and next steps.
