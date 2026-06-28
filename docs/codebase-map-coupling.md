# Mapa de codebase — Capa de acoplamiento a Claude Code

- **Fecha:** 2026-06-28
- **Alcance:** SOLO la capa de acoplamiento (superficies y código que tocan Claude Code).
  No es un mapa completo del codebase; es el mapa de "qué hay que abstraer para portar".
- **Objetivo:** preparar una versión de Alfred Dev usable por otro agente/harness fuera
  de Claude Code.
- **Fuentes:** dos mapeos paralelos (núcleo `core/` portable vs. acoplado; inventario
  exhaustivo de la frontera CC). Cifras reales: 19 agents, 27 commands (25 publicados),
  62 skills, 14 hooks, 1 MCP server, ~3500 LOC de núcleo portable.

---

## 0. Las tres capas de Alfred (clave mental)

Alfred no es "un programa Python". Son **tres capas** con portabilidad muy distinta:

| Capa | Qué es | Dónde vive | Portabilidad |
|---|---|---|---|
| **A — Núcleo de código** | Lógica de soporte: máquina de estados, memoria SQLite, secretos, personalidad | `core/*.py`, `mcp/memory_server.py` | **Alta** (~200 LOC acoplados de ~3500) |
| **B — Sistema de prompts** | El "producto" real: 19 agentes, 27 commands, 62 skills | `agents/`, `commands/`, `skills/` (Markdown + frontmatter CC) | **Depende del host destino** |
| **C — Runtime de plataforma** | Cómo se engancha a CC: hooks, eventos, MCP stdio, env vars | `hooks/`, `hooks.json`, `.mcp.json`, `.claude-plugin/` | **Baja** (lo más acoplado) |

> El error de evaluación más común es mirar solo la Capa A ("3500 LOC portables") y
> concluir que portar es fácil. El verdadero Alfred es la Capa B, expresada en las
> primitivas declarativas de CC (Capa C). Portar = re-anclar B y C a otro host.

---

## 1. Capa A — Núcleo de código (`core/` + `mcp/`)

### 1.1 Núcleo PURO (portable sin cambios, ~3500 LOC)

| Módulo | Rol | Acoplamiento |
|---|---|---|
| `core/orchestrator.py` | **Máquina de estados**: `FLOWS` (76-324), fases, gates, autonomía, composición de equipo | Mínimo: importa `has_frontend` (l.350) para condicionar la fase de estilo; `sync_session_state_to_kanban` (l.985) es fail-open |
| `core/memory.py` | Capa SQLite (decisiones, commits, eventos, iteraciones, FTS5, WAL, perms 0600) | Cero (solo `core.secrets`) |
| `core/memory_config.py` | Lee config de memoria desde frontmatter YAML | Cero |
| `core/secrets.py` | `SECRET_PATTERNS`, `sanitize_text()`, `is_secret_storage_path()` | Cero |
| `core/personality.py` | `AGENTS` (catálogo + frases + sarcasmo), `get_agent_intro/voice` | Cero |
| `core/optional_agents.py` | `OPTIONAL_AGENT_CATALOG`, menús de selección | Cero |
| `core/selina_*.py` (4) | Catálogos visuales + generadores HTML/JSON | Cero refs a CC |

**`orchestrator.py` es el activo más valioso**: la máquina de estados de fases/gates es
pura. El flujo (qué agente actúa, qué gate aplica) está en datos (`FLOWS`), no en código
atado a CC.

### 1.2 Núcleo ACOPLADO / MIXTO (~200 LOC, requiere abstracción)

| Módulo | Acoplamiento concreto | Fichero:línea |
|---|---|---|
| `core/continuity.py` | **FUERTE.** Catálogo de ficheros `.claude/*`, API prefetch/handoff, asume convención de rutas CC | `resolve_memory_dir` (106), `load_uat` (177) |
| `core/memory_sync.py` | **FUERTE.** Proyecta SQLite → memoria nativa CC (`~/.claude/projects/<-path->/memory/`), normaliza `/`→`-` | l.106, l.987 |
| `core/config_loader.py` | **MEDIO.** Ruta fija `.claude/alfred-dev.local.md`; `has_frontend()` | l.254, l.350, l.505 |
| `core/config_cli.py` | **FUERTE.** CLI pensada para el skill `/alfred-dev:config` | (todo) |
| `core/session_report.py` | **MEDIO.** Lee `../.claude-plugin/plugin.json`; escribe `docs/alfred-reports/`; usa `load_uat()` | l.732, l.173 |
| `core/memory_ui_server.py` | **FUERTE.** Servidor HTTP que lee `plugin.json` y asume estructura CC | l.1182 |

### 1.3 MCP server (`mcp/memory_server.py`) — casi portable

JSON-RPC 2.0 sobre stdio (`initialize`, `notifications/initialized`, `tools/list`,
`tools/call`, `ping`), 15 herramientas de memoria. Acoplamiento: resuelve la DB en
`$PWD/.claude/alfred-memory.db` (l.1975) y la versión desde `plugin.json`. El protocolo
MCP **no es acoplamiento a CC** (es un estándar abierto); cualquier host con cliente MCP
lo consume. → portable con cambio de resolución de ruta.

---

## 2. Capa C — Runtime de plataforma (lo más acoplado)

### 2.1 Variables de entorno

| Var | Uso | Ficheros | Criticidad |
|---|---|---|---|
| `CLAUDE_PLUGIN_ROOT` | Resolver raíz del plugin (hooks, MCP, imports de `core/`) | `.mcp.json:7`, `session-start.sh:467`, `session-bootstrap.sh:167`, `install.sh:505`, +tests | **Alta** |
| `ALFRED_MEMORY_LOG_LEVEL` | Log del MCP server | `memory_server.py:65` | Media (propia, no CC) |
| `ALFRED_MEMORY_RETENTION_DAYS` | Purga de memoria | `memory_server.py:1953` | Media (propia, no CC) |
| ~~`CLAUDE_PROJECT_DIR`~~ | **NO usada** — deriva raíz con `os.getcwd()`/`$PWD`/ascenso a `.claude/` | — | (deuda, ver spike nativeidad) |

### 2.2 Protocolo de hooks (8 eventos, `hooks/hooks.json`)

| Evento CC | Matcher | Scripts | Criticidad |
|---|---|---|---|
| `SessionStart` | `startup\|resume\|clear\|compact` | session-bootstrap.sh, session-start.sh | Alta |
| `UserPromptSubmit` | — | activity-capture.py | Media |
| `UserPromptExpansion` | — | activity-capture.py | Baja |
| `Stop` | — | activity-capture.py, **stop-hook.py** | Alta |
| `PreCompact` | — | activity-capture.py, memory-compact.py | Media |
| `PreToolUse` | `Read\|Write\|Edit\|Glob\|Grep` | prefetch-finish-guard.py | Alta |
| `PreToolUse` | `Write\|Edit` | secret-guard.sh | Alta |
| `PreToolUse` | `Bash` | dangerous-command-guard.py | Alta |
| `PreToolUse` | `Read` | sensitive-read-guard.py | Media |
| `PostToolUse` | `Bash` | activity-capture, quality-gate, evidence-guard | Media |
| `PostToolUse` | `Write\|Edit` | activity-capture, dependency-watch, spelling-guard | Baja |
| `PostToolUse` | `Read\|Glob\|Grep\|Agent\|WebFetch\|WebSearch\|NotebookEdit` | activity-capture | Baja |

**Entrada (stdin JSON):** `tool_name`, `hook_event_name`, `tool_input.*` (command,
file_path, content, new_string, …), `prompt`, `cwd`.
**Salida (3 canales de decisión):**
- `exit 2` + stderr → bloqueo (secret-guard, dangerous-command, prefetch-guard).
- `{"hookSpecificOutput":{"permissionDecision":"allow"}}` → autoaprobación (dangerous-command).
- `{"decision":"block","reason":...}` → bloqueo de Stop (stop-hook).
- `{"hookSpecificOutput":{"additionalContext":...}}` → inyección de contexto (session-start, memory-compact).

> **Este es el núcleo del acoplamiento.** El modelo "un proceso externo intercepta cada
> tool-call y decide vía exit code / JSON" es específico de CC. Un host sin punto de
> intercepción PreToolUse no puede ejecutar estos guards tal cual.

### 2.3 Dependencia de tool names de CC

Los matchers de `hooks.json` y los campos `tools:` de `agents/*.md` referencian los
nombres exactos de las herramientas CC: `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`,
`Agent`, `WebFetch`, `WebSearch`, `NotebookEdit`. Otro host con otra nomenclatura rompe
los matchers y la asignación de capacidades por agente.

### 2.4 Estado en disco (`.claude/` del proyecto)

`alfred-dev-state.json` (fase activa), `alfred-memory.db` (SQLite), `alfred-dev.local.md`
(prefs), `alfred-prefetch.json`/`-consumed.json` (helper-first), `alfred-handoff.json`,
`alfred-stop-hook-bypass.json`, `alfred-uat.json`, etc. Catálogo en `continuity.py:50-74`.
Fichero-céntrico y atómico por proyecto (bien), pero la **ruta `.claude/` y la convención
de nombres** son de CC.

---

## 3. Capa B — Sistema de prompts (el "producto")

| Superficie | Conteo | Primitiva CC | Qué la ata a CC |
|---|---|---|---|
| Agents | 19 | Subagentes (frontmatter `name/description/tools/model`) | `tools:` con nombres CC; `description` con `<example>` para auto-routing; `model: opus/sonnet` (alias CC) |
| Commands | 27 (25 pub.) | Slash commands (`$ARGUMENTS`, `argument-hint`, `${CLAUDE_PLUGIN_ROOT}`) | Invocación `/alfred-dev:*`; sustitución `$ARGUMENTS`; helper-first llama `python3 .claude/...` |
| Skills | 62 | Agent Skills (`SKILL.md`, progressive disclosure, flags) | `disable-model-invocation`, `user-invocable`; descubrimiento por carpeta |
| Manifest | 2 | `plugin.json` + `marketplace.json` | Esquema de plugin CC; el instalador reescribe flags |

Esta capa **es Markdown**, no ejecuta nada por sí misma: la conduce el modelo del host.
Su portabilidad = ¿el host destino tiene primitivas equivalentes (subagentes con system
prompt, comandos, skills, hooks)? Ver auditoría de portabilidad para el veredicto por host.

---

## 4. Resumen de acoplamiento (qué abstraer)

| # | Punto de acoplamiento | Capa | Criticidad | Abstracción necesaria |
|---|---|---|---|---|
| 1 | `CLAUDE_PLUGIN_ROOT` + rutas `.claude/` | A/C | Alta | Resolver de rutas inyectable (`HostContext`) |
| 2 | Protocolo de hooks (entrada/salida, exit codes) | C | Alta | Interfaz de guard/política neutral + adaptador por host |
| 3 | Matchers por tool name CC | B/C | Alta | Mapa de nombres de tools host→canónico |
| 4 | Sistema de prompts en frontmatter CC | B | Alta | Compilador de agents/commands/skills al formato del host |
| 5 | MCP stdio (resolución de DB) | A | Media | Inyección de ruta de DB (estándar MCP se mantiene) |
| 6 | `continuity.py` / `memory_sync.py` (memoria nativa CC) | A | Media | Backend de proyección de estado conmutable |
| 7 | Inyección de contexto (`additionalContext`) | C | Media | Proveedor de contexto de sesión por host |

**Conclusión del mapa:** el acoplamiento de *código* es pequeño y bien localizado
(~200 LOC + resolución de rutas). El acoplamiento *real* y caro está en (a) el modelo de
hooks/intercepción de tools y (b) el sistema de prompts declarativo. La estrategia de
desacople se desarrolla en `docs/spikes/2026-06-28-auditoria-portabilidad.md`.
