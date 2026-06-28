# Backlog — Fase 2: política de guards como funciones puras

- **Objetivo de fase:** extraer la *política* de los guards (decisión allow/deny/ask)
  a funciones puras en `alfred_core.guards`, desacopladas del transporte de Claude Code
  (exit codes / JSON de hooks). El adaptador de hooks (fase posterior) las envolverá.
- **Naturaleza:** mecánica, con gate de test claro → **apta para loop autónomo**.
- **Fuente de referencia (solo lectura):** `/Users/fedirosan/Projects/alfred-dev/hooks/`
  y `/Users/fedirosan/Projects/alfred-dev/tests/`.
- **Regla de oro:** cada tarea termina con `uv run pytest -q` **verde** y
  `uv run ruff check src tests` **limpio**. TDD estricto: test en rojo primero.

## Convención de estado

Marca el estado en el checkbox de cada tarea: `[ ]` pending · `[x]` done.
Las tareas marcadas `[DESIGN]` NO se ejecutan en modo autónomo: requieren decisión
humana — el loop debe PARAR y consultar.

---

## [ ] T2.0 — Tipo `Decision` y esqueleto del paquete `guards`

- **Crear:** `src/alfred_core/guards/__init__.py`, `src/alfred_core/guards/decision.py`.
- **Decision** (`decision.py`): dataclass inmutable `Decision` con:
  - `outcome: Literal["allow", "deny", "ask"]`
  - `reason: str = ""`
  - helpers de fábrica: `allow()`, `deny(reason)`, `ask(reason)`.
  - propiedades de conveniencia: `blocked` (True si `deny`).
- **Tests:** `tests/test_guards_decision.py` — construcción por fábricas, inmutabilidad,
  `blocked` correcto por outcome.
- **CA:** `from alfred_core.guards import Decision, allow, deny, ask` funciona; suite verde.

## [ ] T2.1 — `evaluate_write` (política de secretos)

- **Crear:** `src/alfred_core/guards/secrets_guard.py`.
- **API:** `evaluate_write(path: str, content: str) -> Decision`.
- **Lógica (envuelve la política ya pura de `alfred_core.secrets`):**
  - `label = find_secret_label(content)`.
  - Si hay `label` y `not is_secret_storage_path(path)` → `deny(...)` con la etiqueta
    (usa `describe_secret_label`).
  - En cualquier otro caso → `allow()`. Política **fail-closed** documentada: si el
    escaneo lanza, `deny`.
- **Tests:** `tests/test_guards_secrets.py` — porta los casos de
  `alfred-dev/tests/test_secret_guard.py` que ejercitan la *detección* (no el hook),
  adaptados a `evaluate_write`. Incluye: detecta secreto en código, permite en ruta de
  almacenamiento de secretos, permite contenido limpio.
- **CA:** suite verde; cubre deny y allow.

## [ ] T2.2 — `evaluate_command` (comandos peligrosos)

- **Crear:** `src/alfred_core/guards/commands.py`.
- **Portar la lógica PURA** desde `alfred-dev/hooks/dangerous-command-guard.py`:
  helpers de tokenización (`_strip_leading_wrappers`, `_strip_quoted_content`,
  `_has_shell_controls_outside_quotes`, `_extract_shell_c_command`), todos los
  detectores `_detect_*` / `_is_*`, `_find_dangerous_reason`,
  `_is_safe_alfred_helper_command`. **NO portar `main()`** (es el transporte CC).
- **API:** `evaluate_command(command: str) -> Decision`:
  - razón peligrosa encontrada → `deny(reason)`.
  - helper seguro de Alfred reconocido → `allow()` (equivalente al `permissionDecision`).
  - resto → `allow()`.
  - fail-closed: si el parseo lanza → `deny(...)`.
- **Tests:** `tests/test_guards_commands.py` — porta
  `alfred-dev/tests/test_dangerous_command_guard.py` adaptado a `evaluate_command`
  (mismos casos: `rm -rf` sensible, fork bomb, mkfs, dd a dispositivo, git push --force,
  drop table, chmod absoluto, helper seguro permitido, comando normal permitido).
- **CA:** suite verde; paridad de comportamiento con los casos del test original.
- **Nota:** tarea grande (~20 detectores). Si se atasca, reportar y parar; no trocear sola.

## [ ] T2.3 — `evaluate_read` (lectura de ficheros sensibles)

- **Crear:** `src/alfred_core/guards/reads.py`.
- **Portar** los detectores de `alfred-dev/hooks/sensitive-read-guard.py`
  (`_is_env_file`, `_is_private_key`, `_is_ssh_private_key`,
  `_is_service_credentials_file`, `_is_htpasswd`, `_is_java_keystore` y su registro).
  **NO portar `main()`**.
- **API:** `evaluate_read(path: str) -> Decision` → `deny` si es fichero sensible,
  `allow()` si no.
- **Tests:** `tests/test_guards_reads.py` — porta
  `alfred-dev/tests/test_sensitive_read_guard.py` adaptado.
- **CA:** suite verde.

## [ ] T2.4 — Puerto `ToolGuard` (fachada unificada)

- **Crear/editar:** `src/alfred_core/guards/__init__.py`.
- **Definir** el puerto `ToolGuard` (typing.Protocol) con un método
  `evaluate(action: GuardAction) -> Decision`, y una implementación por defecto
  `CoreGuard` que despacha a `evaluate_write` / `evaluate_command` / `evaluate_read`
  según el tipo de acción. Define `GuardAction` (dataclass: `kind`, `command?`,
  `path?`, `content?`).
- **Tests:** `tests/test_guards_facade.py` — despacho correcto por tipo de acción,
  con un caso allow y uno deny por cada kind.
- **CA:** suite verde; `from alfred_core.guards import ToolGuard, CoreGuard, GuardAction`.

---

## [DESIGN] T2.5 — Adaptador de hooks de Claude Code (NO autónomo)

Envolver las funciones `evaluate_*` en los scripts de hook reales (exit 2 / JSON
`permissionDecision`). Requiere decidir empaquetado y ubicación del adaptador. **Parar
y consultar**: fuera del alcance del loop autónomo.

---

## Definición de "fase completa"

T2.0–T2.4 en `[x]`, suite verde, ruff limpio, y un commit por tarea. T2.5 queda como
checkpoint humano para la siguiente sesión.
