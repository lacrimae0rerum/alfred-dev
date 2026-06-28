# Runner del loop autónomo — Fase 2

Este documento define el **protocolo** que ejecuta el loop y **cómo lo lanzas tú**.
El loop lo arrancas tú con `/loop`; Alfred no lo lanza por su cuenta.

## Cómo lanzarlo

En el prompt de Claude Code, dentro de `/Users/fedirosan/Projects/alfred-hermes`:

```
/loop Ejecuta el runner de docs/loop/loop-runner.md sobre el backlog
docs/loop/backlog-phase-2.md. Una tarea por iteración.
```

- Sin intervalo → modo self-paced (el modelo decide cuándo seguir). Recomendado.
- Puedes interrumpir en cualquier momento; el estado vive en el backlog y en git.

## Protocolo (qué hace cada iteración)

1. **Leer el backlog** `docs/loop/backlog-phase-2.md`. Coger la **primera** tarea con
   estado `[ ]` (pending) en orden.
2. **Condición de fin:** si no quedan `[ ]`, ejecutar `uv run pytest -q`, reportar el
   total verde y **TERMINAR el loop** (no reprogramar).
3. **Checkpoint de diseño:** si la siguiente tarea es `[DESIGN]`, **PARAR** y consultar
   al usuario. No ejecutarla en autónomo.
4. **Implementar con TDD estricto:**
   - Leer los ficheros fuente de referencia indicados en la tarea (en `alfred-dev`,
     solo lectura).
   - Escribir el test primero y verlo en **rojo**.
   - Implementar el mínimo para pasar a **verde**. Refactor si procede.
5. **Gate de calidad (obligatoria, ejecutada de verdad):**
   - `uv run pytest -q` → debe pasar TODA la suite (no solo el test nuevo).
   - `uv run ruff check src tests` → limpio (código nuevo bajo ruleset completo).
6. **Cierre de tarea:**
   - **Verde:** marcar la tarea `[x]` en el backlog, `git add -A` y `git commit` con
     mensaje descriptivo (`Phase 2: <tarea> ...` + la línea `Co-Authored-By` del repo).
     Pasar a la siguiente.
   - **Rojo:** intentar arreglar **una** vez más. Si sigue rojo → **PARAR**, dejar la
     tarea en `[ ]` con una nota del error bajo la tarea, y reportar. **No commitear en
     rojo.**
7. **Una tarea por iteración.** No encadenar varias sin pasar por la gate.

## Reglas innegociables

- **Honestidad operativa:** no marcar `[x]` ni commitear sin haber visto la gate en
  verde con salida real. Si algo falla, decirlo con el error.
- **TDD real:** el test va primero y se ve en rojo. Nada de test escrito después.
- **Sin secretos:** antes de cada commit, revisar que el diff no introduce credenciales.
- **Fidelidad de port:** al traer lógica de `alfred-dev`, portar la política pura, no el
  `main()` / transporte de hooks.
- **Límite de alcance:** el checkpoint de diseño T2.5 (`[DESIGN]`) se resolvió con Fer
  el 2026-06-28; sus decisiones de arquitectura están en el backlog. El loop cubre ahora
  T2.0–T2.4 (hechas) y T2.5a–T2.5c (desglose mecánico del adaptador de hooks). No quedan
  tareas `[DESIGN]` pendientes; si apareciera una nueva, aplicar el checkpoint y parar.
- **Parar ante lo inesperado:** si una tarea resulta ambigua, mal dimensionada o requiere
  una decisión de arquitectura no prevista, PARAR y reportar en vez de improvisar.

## Estado de arranque (al preparar este runner)

- Suite: **207 tests verdes**, ruff limpio.
- Backlog: T2.0–T2.4 pending, T2.5 marcada `[DESIGN]`.
- Último commit: `ed76b98` (Fase 1, HostContext).

## Progreso (2026-06-28)

- T2.0–T2.4 completadas vía loop (TDD, gate verde, un commit por tarea):
  `63cd8e0`, `0e0545f`, `0fe325c`, `1b1809d`, `a9b9efb`. Suite: **318 verdes**.
- Checkpoint T2.5 (`[DESIGN]`) resuelto con Fer: adaptador en `hooks/` con scripts finos
  por herramienta; transporte testeable en `src/alfred_core/adapters/claude_code.py`.
  Desglosado en T2.5a–T2.5c, ahora autónomas. Loop reanudado sobre ellas.
