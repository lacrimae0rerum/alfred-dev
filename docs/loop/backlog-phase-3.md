# Backlog — Fase 3: compilador de prompts a formato neutro

- **Objetivo de fase:** convertir los artefactos de prompt de Claude Code
  (`agents/*.md`, `commands/*.md`, `skills/*/SKILL.md`) a un **formato neutro**
  serializable, desacoplado del envoltorio CC, más un **mapa de tool names**
  CC → canónico. Es el paso 4 del plan de la auditoría de portabilidad
  (`docs/2026-06-28-auditoria-portabilidad.md`, sección 5).
- **Naturaleza:** mecánica, con gate de test clara → **apta para loop autónomo**.
- **Fuente de referencia (solo lectura):** `/Users/fedirosan/Projects/alfred-dev/agents/`,
  `/commands/`, `/skills/`. Los tests usan **fixtures propios** en
  `tests/fixtures/prompts/` para ser herméticos (no dependen de esa ruta).
- **Regla de oro:** cada tarea termina con `uv run pytest -q` **verde** y
  `uv run ruff check src tests` **limpio**. TDD estricto: test en rojo primero.

## Decisiones de diseño (por defecto, derivadas de la auditoría)

- **Formato neutro = dataclasses serializables.** `AgentSpec`, `CommandSpec`,
  `SkillSpec` con `to_dict()` → JSON. Capturan: `name`, `description`, `body`
  (system prompt / contenido), y los campos propios (tools mapeadas, model,
  argument_hint). El "envoltorio" CC se descarta; la inteligencia (el body) se
  conserva intacta.
- **Parser de frontmatter propio, cero dependencias.** Un subset de YAML
  suficiente para el frontmatter de Alfred (claves escalares + block scalar `|`).
  Mantiene el núcleo `alfred_core` sin dependencias obligatorias (portabilidad).
- **Mapa de tool names CC → canónico.** Tabla explícita (`Bash`→`shell`,
  `Read`→`read_file`, `Write`→`write_file`, `Edit`→`edit_file`, `Glob`→`glob`,
  `Grep`→`grep`, `WebSearch`→`web_search`, `WebFetch`→`web_fetch`,
  `Agent`/`Task`→`subagent`). Tool desconocida → se conserva el nombre original
  marcándola como no mapeada (honestidad: no inventar equivalencias).
- **Ubicación:** `src/alfred_core/compiler/` (`frontmatter.py`, `models.py`,
  `tools_map.py`, `compile.py`).

## Convención de estado

`[ ]` pending · `[x]` done. Tareas `[DESIGN]` NO se ejecutan en autónomo.

---

## [x] T3.0 — Parser de frontmatter (`parse_frontmatter`)

- **Crear:** `src/alfred_core/compiler/__init__.py`,
  `src/alfred_core/compiler/frontmatter.py`.
- **API:** `parse_frontmatter(text: str) -> tuple[dict, str]` → `(meta, body)`.
  - Soporta delimitadores `---` al inicio; sin frontmatter → `({}, text)`.
  - Claves escalares `key: value` (comillas opcionales recortadas).
  - Block scalar `key: |` → acumula líneas indentadas como string multilínea.
- **Tests:** `tests/test_compiler_frontmatter.py` — frontmatter con block scalar
  (`description: |` con HTML embebido), claves simples + comillas, fichero sin
  frontmatter, valor CSV (`tools: A,B,C`).
- **CA:** suite verde; ruff limpio.

## [x] T3.1 — Modelos neutros (`AgentSpec` / `CommandSpec` / `SkillSpec`)

- **Crear:** `src/alfred_core/compiler/models.py`.
- **Dataclasses inmutables** con `to_dict()` serializable a JSON:
  - `AgentSpec`: `name`, `description`, `tools: list[str]`, `model`, `body`.
  - `CommandSpec`: `name`, `description`, `argument_hint`, `body`.
  - `SkillSpec`: `name`, `description`, `body`.
- **Tests:** `tests/test_compiler_models.py` — construcción y `to_dict()`
  (round-trip de claves, JSON-serializable con `json.dumps`).
- **CA:** suite verde; ruff limpio.

## [x] T3.2 — Mapa de tool names (`map_tools`)

- **Crear:** `src/alfred_core/compiler/tools_map.py`.
- **API:** `map_tool(name: str) -> str` y `map_tools(value) -> list[str]`
  (acepta CSV o lista; recorta espacios; ignora vacíos). Tabla CC → canónico
  como arriba; desconocida → nombre original (marcada vía `is_mapped(name)`).
- **Tests:** `tests/test_compiler_tools_map.py` — cada par conocido, CSV con
  espacios, tool desconocida conservada, `Agent` y `Task` → `subagent`.
- **CA:** suite verde; ruff limpio.

## [x] T3.3 — Compiladores por artefacto

- **Crear:** `src/alfred_core/compiler/compile.py`.
- **API:** `compile_agent(text) -> AgentSpec`, `compile_command(name, text) ->
  CommandSpec`, `compile_skill(text) -> SkillSpec`. Usan `parse_frontmatter` +
  `map_tools` + modelos. `compile_command` recibe el `name` (deriva del fichero,
  no del frontmatter, que no lo lleva).
- **Tests:** `tests/test_compiler_compile.py` con **fixtures** en
  `tests/fixtures/prompts/` (un agent, un command, un skill mínimos pero
  realistas): el spec resultante tiene name/description/body correctos y tools
  mapeadas; el body conserva el contenido tras el frontmatter.
- **CA:** suite verde; ruff limpio.

## [x] T3.4 — Compilación de árbol + emisión JSON

- **Editar:** `src/alfred_core/compiler/compile.py` (+ export en `__init__`).
- **API:** `compile_tree(root: Path) -> dict` que recorre `agents/`,
  `commands/`, `skills/` bajo `root` y devuelve `{"agents": [...], "commands":
  [...], "skills": [...]}` con los specs en `to_dict()`. JSON-serializable.
- **Tests:** `tests/test_compiler_tree.py` — sobre un árbol de fixtures: cuenta
  artefactos por tipo, `json.dumps` del resultado no lanza, y un artefacto
  conocido aparece con sus campos. Cierra la fase 3.
- **CA:** suite verde; ruff limpio.

---

## Definición de "fase completa"

T3.0–T3.4 en `[x]`, suite verde, ruff limpio, y un commit por tarea. El
compilador queda validado contra fixtures; aplicarlo a los 108 artefactos reales
de `alfred-dev` y emitir a un host concreto es trabajo de Fase 4 (adaptador).

## Nota de alcance (honestidad operativa)

Fases 4 (adaptador Agent SDK) y 5 (degradaciones declaradas) **no se ejecutan en
este loop**: requieren el Claude Agent SDK (no instalado), credenciales de API y
un prototipo end-to-end de validación. La propia auditoría las marca como
dependientes de validar viabilidad con prototipo. Quedan como trabajo con
dependencias externas, fuera del alcance autónomo.
