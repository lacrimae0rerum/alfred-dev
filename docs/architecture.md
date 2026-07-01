# Arquitectura

Alfred Dev for Codex porta la arquitectura de Alfred Dev a las superficies que
Codex carga hoy: plugins, skills, subagents, hooks y MCP.

## Capas

| Capa | Directorios | Responsabilidad |
|---|---|---|
| Plugin | `.codex-plugin/`, `.agents/plugins/` | Manifest y metadata de marketplace local. |
| Entrada | `skills/`, `commands/`, `prompts/` | Skill principal y contratos de flujos. En Codex se invocan como `$alfred-dev:*`. |
| Equipo | `agents/`, `.codex/agents/` | 19 especialistas: Markdown fuente y TOML instalable para subagents Codex. |
| Runtime | `core/`, `alfred_core/` | Orquestacion, configuracion, memoria, continuidad, seguridad y helpers deterministas. |
| Integracion | `hooks/`, `mcp/`, `.mcp.json` | Hooks de ciclo de vida y servidor MCP `alfred-memory`. |
| Artefactos | `templates/`, `visual/`, `docs/` | Plantillas, soporte visual y documentacion publica. |

## Flujo de invocacion

1. El usuario invoca un skill, por ejemplo `$alfred-dev:feature`.
2. El prompt consulta estado bajo `.codex/` y prepara la fase correspondiente.
3. Alfred coordina subagents Codex especializados segun el flujo.
4. El runtime persiste estado en `.codex/alfred-dev-state.json`.
5. El MCP `alfred-memory` guarda decisiones e iteraciones en
   `.codex/alfred-memory.db`.
6. Las quality gates bloquean avance si faltan tests, seguridad, aprobacion o
   evidencia.

## Equipo

El port publica 19 agentes:

- 10 de nucleo: `alfred`, `product-owner`, `architect`, `senior-dev`,
  `security-officer`, `qa-engineer`, `devops-engineer`, `tech-writer`,
  `project-manager`, `selina`.
- 9 opcionales: `data-engineer`, `ux-reviewer`, `performance-engineer`,
  `github-manager`, `seo-specialist`, `copywriter`, `librarian`,
  `i18n-specialist`, `lucius`.

Los ficheros `agents/*.md` mantienen el prompt humano del especialista. Los
ficheros `.codex/agents/*.toml` son la forma instalable que Codex usa para
descubrir subagents.

## Estado de proyecto

El port usa rutas Codex:

```text
.codex/alfred-dev.local.md
.codex/alfred-dev-state.json
.codex/alfred-handoff.json
.codex/alfred-uat.json
.codex/alfred-memory.db
```

No usa `.claude/`.

## Gates

Los flujos conservan la disciplina del Alfred original:

- aprobacion de producto o diseño cuando aplica;
- fase visual condicional si hay frontend;
- desarrollo con TDD;
- revision de calidad y seguridad;
- evidencia real de comandos/tests;
- entrega con aprobacion humana para produccion;
- autopilot limitado a gates de usuario configuradas.

## Limites del port

Codex no expone exactamente las mismas primitivas de comando que el runtime
original. Por eso:

- los slash commands namespaced se distribuyen como prompts;
- los agentes se instalan como TOML de subagent;
- la instalacion real debe verificarse en Codex App/CLI, no solo con tests.
