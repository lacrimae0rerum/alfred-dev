# PRD 0002 — `HostContext`: puerto de resolución de rutas (Fase 1)

- **Fecha:** 2026-06-28
- **Tipo:** PRD ligero
- **Estado:** completado (2026-06-28)
- **Contexto:** `0001-extraccion-alfred-core.md`, `../2026-06-28-auditoria-portabilidad.md`
  (puerto `HostContext`), `../2026-06-28-nativeidad-claude-code.md` (deuda
  `CLAUDE_PROJECT_DIR`).

## Problema

El núcleo extraído seguía atado a Claude Code en dos puntos: `orchestrator` resolvía
el directorio de proyecto con `project_dir or os.getcwd()`, **ignorando la variable
oficial `CLAUDE_PROJECT_DIR`**; y `config_loader` tenía la convención `.claude/`
hardcodeada en varios sitios. Sin un punto único de resolución, ningún host distinto de
CC puede relocalizar el estado.

## Solución

Implementar el primero de los 6 puertos de la auditoría: `HostContext`
(`src/alfred_core/host.py`), una dataclass inmutable que centraliza la resolución:

- Precedencia de proyecto: **arg explícito > `CLAUDE_PROJECT_DIR` > `cwd`** (cierra la deuda).
- Convención de estado configurable vía `state_dir_name` (default `.claude`); un host
  no-CC puede usar `.alfred` u otro sin tocar el núcleo.
- Rutas derivadas en un solo lugar: `state_dir`, `config_path`, `state_path`,
  `memory_db_path`.

Integrado en los dos únicos puntos de consumo del núcleo:
- `orchestrator.run_flow` → `HostContext.from_env(project_dir).project_dir`.
- `config_loader` → `HostContext(project_dir).config_path` / `.state_path` (5 sitios;
  cero `os.path.join(..., ".claude", ...)` restantes).

`MemoryDB` ya recibía `db_path` explícito: no requería cambios.

## Fuera de alcance

- Los otros 5 puertos (ToolGuard, LifecycleSink, ContextProvider, AgentRunner, StateStore).
- El adaptador Claude Code y el adaptador Agent SDK.
- Limpieza de estilo del núcleo heredado.

## Criterios de aceptación

1. **Given** `CLAUDE_PROJECT_DIR` en el entorno y sin arg explícito, **then**
   `HostContext.from_env()` resuelve a esa ruta. ✅
2. **Given** un arg explícito, **then** gana sobre `CLAUDE_PROJECT_DIR` y `cwd`. ✅
3. **Given** `state_dir_name=".alfred"`, **then** todas las rutas derivadas se relocalizan. ✅
4. **Given** `run_flow`, **then** enruta su `project_dir` a través de `HostContext.from_env`
   (test de wiring). ✅
5. **Given** la suite completa, **then** sigue verde y sin findings de ruff en código nuevo. ✅

## Evidencia de cierre (2026-06-28)

- `uv run pytest` → **207 passed, 14 subtests** (11 nuevos en `test_host.py`:
  resolución, rutas derivadas, state dir configurable, inmutabilidad, wiring).
- `uv run ruff check src tests` → **All checks passed!** (`host.py` bajo ruleset completo).
- `grep` → cero `os.path.join(..., ".claude", ...)` en `config_loader`.
- TDD: `test_host.py` escrito en rojo (ModuleNotFoundError) antes de `host.py`.

**Deuda saldada:** la condición `CLAUDE_PROJECT_DIR` del spike de nativeidad queda cerrada
en el núcleo. Pendiente replicarla en los hooks/scripts cuando se construya el adaptador CC.
