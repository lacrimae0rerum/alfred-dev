# Host Degradations: Hermes vs Claude Code

> Fecha: 2026-06-30
> Fase: 5 del plan de portabilidad

Esta tabla documenta qué garantías y funcionalidades de Alfred Dev se conservan,
degradan o pierden al correr bajo Hermes en lugar de Claude Code.

## Tabla de degradaciones

| Garantía / Feature | Claude Code | Hermes | Notas |
|---|---|---|---|
| **Bloqueo pre-acción** (guards de seguridad) | ✅ Vía hooks `PreToolUse` con exit code 2 | ✅ Vía `CoreGuard.evaluate()` in-process, sin subprocess | Misma política de seguridad. Más fiable por eliminar subprocesos. |
| **Subagentes interactivos** (spawn de agentes) | ✅ Vía tool `Agent`/`Task` nativa | ✅ Vía `delegate_task()` | Distinto mecanismo, mismo resultado: spawn + resultado recuperable. |
| **Slash commands** (`/alfred-dev:feature`, `/alfred-dev:quick`) | ✅ Nativo en CC | ❌ No existe en Hermes | Reemplazado por prompt conversacional al agente orquestador. |
| **Plugin system** (`plugin.json`, `.claude-plugin/`) | ✅ Marketplace + plugin.json | ❌ No existe | Reemplazado por personalidad `/personality alfred` + skills en `~/.hermes/skills/`. |
| **Modelo por agente** (opus vs sonnet) | ✅ Configurable por agente | ❌ No controlable | Hermes decide el modelo. Todos los subagentes usan el modelo configurado en Hermes. |
| **Routing automático por `description`** | ✅ CC selecciona skill según descripción | ❌ No existe | El agente orquestador (Alfred) decide qué subagente invocar según la fase del flujo. |
| **MCP memory server** | ✅ `alfred-memory` como MCP stdio | ⚠️ No verificado | El servidor MCP existe; depende de si Hermes soporta MCP externo. |
| **Continuidad no-parada** (Stop hook) | ✅ Vía hook `Stop` bloqueante | ⚠️ Cooperativa | Sin Stop hook en Hermes; el estado se relee al inicio de cada turno. |
| **Skills declarativos** (SKILL.md) | ✅ SKILL.md en `skills/` del plugin | ✅ SKILL.md en `~/.hermes/skills/` | Portables con adaptación de frontmatter (añadir version, author, license, metadata). |
| **Quality gates entre fases** | ✅ Vía orchestrator + evidencia | ✅ Misma lógica en `alfred_core.orchestrator` | El núcleo de orquestación es el mismo. |
| **Detectión de stack** | ✅ Vía `session-start.sh` hook | ⚠️ No verificado | La lógica existe en `alfred_core.config_loader`. Depende de que se ejecute al inicio de sesión. |
| **Memoria persistente SQLite** | ✅ `alfred_memory.db` en `.claude/` | ✅ Misma DB, distinta ruta | El motor es el mismo. La ruta cambia según `HostContext.state_dir`. |
| **Autopilot** (auto-aprobar gates) | ✅ Configurable por fase | ✅ Misma lógica | El núcleo es el mismo. La UX de "preguntar al usuario" es conversacional en Hermes. |

## Resumen

| Estado | Conteo |
|---|---|
| ✅ Conservado sin cambios | 4 (guards, quality gates, memoria, autopilot) |
| ⚠️ Degradado / no verificado | 3 (MCP, continuidad, stack detection) |
| ❌ No disponible (reemplazado) | 4 (slash commands, plugin system, modelo por agente, routing automático) |

## Riesgos abiertos

1. **MCP**: No se ha probado si Hermes puede cargar el servidor MCP de Alfred.
   Alternativa: usar `alfred_core.memory` como librería importable directamente.
2. **Continuidad cooperativa**: Sin Stop hook, la continuidad no está garantizada
   si la sesión se interrumpe abruptamente. Funciona en el caso normal (turno a turno).
3. **Stack detection**: El hook `session-start.sh` de CC no tiene equivalente directo.
   La lógica de detección debe invocarse manualmente o integrarse en el AGENTS.md.