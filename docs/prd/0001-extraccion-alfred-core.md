# PRD 0001 — Extracción de `alfred_core` (Fase 0 del port)

- **Fecha:** 2026-06-28
- **Tipo:** PRD ligero
- **Estado:** completado (2026-06-28)
- **Contexto:** `../codebase-map-coupling.md`, `../2026-06-28-auditoria-portabilidad.md`

## Problema

Alfred Dev vive hoy acoplado a Claude Code. La auditoría de portabilidad concluyó que
~3500 LOC del núcleo (`core/`) son lógica pura reutilizable, pero están dentro del plugin
y mezclados con la cáscara de plataforma. No hay un paquete instalable ni una red de
tests que sirva de señal verde/roja para construir de forma incremental (ni para un loop
autónomo).

## Solución

Extraer el núcleo puro a un paquete Python instalable e independiente (`alfred-core`),
con layout `src/`, `pyproject.toml`, `uv` y una suite de regresión que pase en verde.
**Sin rediseño**: extracción fiel. La abstracción de rutas (HostContext) es Fase 1.

Módulos extraídos: `secrets`, `memory_config`, `optional_agents`, `personality`,
`memory`, `config_loader`, `orchestrator`. El acoplamiento residual (rutas `.claude/` en
`config_loader`; `continuity` opcional vía import fail-open en `orchestrator`) se conserva
sin romper y queda documentado como deuda de Fase 1.

## Fuera de alcance (Fase 0)

- Diseñar/implementar los 6 puertos (HostContext, ToolGuard, …).
- Tocar hooks, MCP, commands o skills.
- Adaptadores de otros hosts (Agent SDK, etc.).

## Criterios de aceptación

1. **Given** un entorno limpio, **when** ejecuto `uv run pytest`, **then** la suite de
   regresión del núcleo pasa en verde.
2. **Given** el paquete instalado, **when** hago `from alfred_core import orchestrator,
   memory, secrets, personality, optional_agents, config_loader, memory_config`, **then**
   todos importan sin error.
3. **Given** `orchestrator`, **when** se ejecuta sin `continuity` disponible, **then** el
   import fail-open cae a `None` y el flujo continúa (no se rompe).
4. **Given** el código extraído, **when** lo reviso, **then** no queda ninguna referencia
   `from core.` / `import core.` (todo reapunta a `alfred_core`).
5. **Given** `ruff check`, **then** no hay errores nuevos introducidos por la extracción.

## Evidencia de cierre (2026-06-28)

- **CA1** ✅ `uv run pytest` → **195 passed, 14 subtests passed** en 0.70s.
- **CA2** ✅ `tests/test_smoke_imports.py` importa los 7 módulos sin error.
- **CA3** ✅ `test_save_and_load_roundtrip_under_claude_dir` ejercita el path
  `.claude/` y el import fail-open de `continuity` cae a `None` sin romper.
- **CA4** ✅ `grep` confirma cero `from core.` / `import core.` en `src/`.
- **CA5** ✅ `uv run ruff check src tests` → **All checks passed!**

**Notas de honestidad:**
- `test_orchestrator.py` original (84 tests) **no se portó**: estaba acoplado a
  `continuity` (kanban/UAT, 57 usos) — es test de integración de la cáscara, no del
  núcleo. Se sustituyó por `test_orchestrator_core.py` (state machine pura).
- `TestConfigCli` se descartó: dependía de `core/config_cli.py` (cáscara CC no extraída).
- El núcleo extraído se mantiene **fiel al original** (sin reformatear); su estilo
  heredado (E/I/UP/B) queda como deuda declarada en `pyproject.toml`, linteado solo
  contra defectos funcionales (F). Limpieza de estilo → Fase 1.
- **No se ha inicializado git ni hecho commit** (pendiente de tu visto bueno).
