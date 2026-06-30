# Alfred Dev for Codex

Codex-native port of Alfred Dev: an automated software engineering workflow
system with 19 specialist agents, 62 skills across 15 domains, persistent
project memory, gated delivery flows, lifecycle hooks, visual direction support,
autopilot rules, and European compliance guidance.

This branch targets Codex. It preserves Alfred Dev's product behavior as far as
Codex surfaces allow:

- **Agents:** 19 Alfred roles are available as Codex custom agents under
  `.codex/agents/`.
- **Skills:** the 62 Alfred skills are flattened into Codex-compatible skill
  packages under `skills/`.
- **Commands:** Claude slash commands are ported to Codex custom prompts under
  `prompts/`. The installer also creates the direct personal alias
  `/alfred:dev` for the main Alfred entrypoint.
- **Hooks:** Alfred lifecycle hooks are bundled under `hooks/hooks.json` using
  Codex hook events.
- **Memory:** `alfred-memory` is exposed as a bundled MCP server.
- **State:** project state is written under `.codex/`, not `.claude/`.

## Install Locally

From this repository:

```bash
bash ./install.sh
```

The installer:

- registers this repo as a local Codex marketplace;
- installs `alfred-codex@alfred-codex-local`;
- copies Alfred custom prompts into `~/.codex/prompts`;
- copies Alfred custom agents into `~/.codex/agents`;
- installs the direct personal skill alias `/alfred:dev`;
- refreshes the plugin cache.

After installation, start a new Codex session.

## Invocation

Use `/alfred:dev` as the direct Alfred entrypoint:

```text
/alfred:dev
/alfred:dev crea una feature de autenticación con OAuth2
/alfred:dev revisa el estado del proyecto y dime qué toca ahora
```

Subcommands are also available as Codex custom prompts:

```text
/prompts:alfred
/prompts:alfred-dev-feature sistema de autenticación con OAuth2
/prompts:alfred-dev-quick cambio pequeño y acotado
/prompts:alfred-dev-fix el endpoint de login devuelve 500
/prompts:alfred-dev-spike evaluar cola de eventos
/prompts:alfred-dev-audit
/prompts:alfred-dev-ship
```

You can also invoke the installed skill directly in natural language:

```text
Use Alfred to run a feature flow for this change.
Ask Alfred to audit this project with specialist agents.
Start an Alfred quick flow for this task.
```

## Team

Core agents:

- `alfred`
- `project-manager`
- `product-owner`
- `selina`
- `architect`
- `senior-dev`
- `security-officer`
- `qa-engineer`
- `devops-engineer`
- `tech-writer`

Optional agents:

- `data-engineer`
- `ux-reviewer`
- `performance-engineer`
- `github-manager`
- `seo-specialist`
- `copywriter`
- `librarian`
- `i18n-specialist`
- `lucius`

## Flows

Alfred keeps the six delivery flows:

- `feature`: product, conditional visual style, architecture, development,
  quality, documentation, delivery.
- `quick`: scoped implementation and focused validation.
- `fix`: diagnosis, correction, regression validation.
- `spike`: exploration and conclusions.
- `audit`: parallel quality, security, architecture, and docs review.
- `ship`: final audit, docs, packaging, deployment gate.

Autopilot may auto-approve user gates, but it does not bypass tests, security,
evidence, or explicit deployment confirmation.

## Memory MCP

The bundled MCP server is `alfred-memory`. It stores project memory under:

```text
<project>/.codex/alfred-memory.db
```

The MCP launcher is portable: it works when Codex starts the server from the
user home directory, the plugin cache, or a local development checkout.

## Validate

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -B "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" .
```

For all inherited Alfred Dev tests, install `pytest` in your environment and run:

```bash
python3 -m pytest tests/ -v
```

## Known Codex Differences

- Bare `/alfred-dev:*` slash commands are not a plugin-distributed Codex
  surface. They are available as `/prompts:alfred-dev-*` custom prompts after
  running `install.sh`.
- Codex subagents are explicit: Alfred asks Codex to spawn named subagents
  instead of relying on Claude's `Agent` tool.
- Hook handlers are command hooks only; prompt/agent hook handlers parsed by
  Codex are not relied upon.
- Project state and memory use `.codex/` paths.

Alfred Dev remains an independent open-source project. This Codex port is not
affiliated with or endorsed by OpenAI.
