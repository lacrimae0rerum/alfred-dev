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

## [x] T2.0 — Tipo `Decision` y esqueleto del paquete `guards`

- **Crear:** `src/alfred_core/guards/__init__.py`, `src/alfred_core/guards/decision.py`.
- **Decision** (`decision.py`): dataclass inmutable `Decision` con:
  - `outcome: Literal["allow", "deny", "ask"]`
  - `reason: str = ""`
  - helpers de fábrica: `allow()`, `deny(reason)`, `ask(reason)`.
  - propiedades de conveniencia: `blocked` (True si `deny`).
- **Tests:** `tests/test_guards_decision.py` — construcción por fábricas, inmutabilidad,
  `blocked` correcto por outcome.
- **CA:** `from alfred_core.guards import Decision, allow, deny, ask` funciona; suite verde.

## [x] T2.1 — `evaluate_write` (política de secretos)

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

## [x] T2.2 — `evaluate_command` (comandos peligrosos)

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

## [x] T2.3 — `evaluate_read` (lectura de ficheros sensibles)

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

## [x] T2.4 — Puerto `ToolGuard` (fachada unificada)

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

## [x] T2.5 — Checkpoint de diseño del adaptador de hooks (RESUELTO)

Envolver las funciones `evaluate_*` en los scripts de hook reales (exit 2 / JSON
`permissionDecision`). El checkpoint `[DESIGN]` se resolvió con Fer el 2026-06-28: las
decisiones de arquitectura están tomadas (ver abajo) y la implementación se desglosa en
T2.5a–T2.5c, que son **mecánicas con gate de test clara → aptas para loop autónomo**.

### Diseño aprobado (decisiones de Fer, 2026-06-28)

- **Ubicación:** carpeta `hooks/` en la raíz del repo con **scripts finos** (estilo
  plugin `alfred-dev`), uno **por herramienta**: `hooks/write-guard.py`,
  `hooks/command-guard.py`, `hooks/read-guard.py`. Cada script es solo wiring
  (importar + leer stdin + emitir).
- **Transporte testeable en el paquete:** el mapeo `Decision → transporte CC` vive en
  `src/alfred_core/adapters/claude_code.py` (no en los scripts), para poder testearlo
  sin `subprocess`. API propuesta:
  - `read_tool_input(stream) -> dict` (parsea el JSON de stdin; fail-closed si rompe).
  - `emit(decision: Decision) -> int` → traduce a transporte y devuelve exit code:
    - `deny` → escribe el aviso en stderr y **exit 2**.
    - `allow` con autoaprobación (helper seguro) → JSON `permissionDecision:"allow"`, exit 0.
    - `allow` normal → **exit 0** silencioso.
    - `ask` → JSON `permissionDecision:"ask"`, exit 0.
  - fallo de parseo de stdin → **deny / exit 2** (fail-closed, igual que el original).
- **Bootstrap de `sys.path`:** cada script en `hooks/` añade `<repo>/src` calculado desde
  `__file__` para no depender de instalación previa del paquete.
- **Registro:** un `hooks/hooks.json` con bloques `PreToolUse` por matcher
  (`Write|Edit` → write-guard; `Bash` → command-guard; `Read|Glob|Grep` → read-guard).

El desglose implementable vive como tareas autónomas T2.5a–T2.5c más abajo.

---

## [x] T2.5a — Transporte del adaptador (`emit` / `read_tool_input`)

- **Crear:** `src/alfred_core/adapters/__init__.py`, `src/alfred_core/adapters/claude_code.py`.
- **API:**
  - `read_tool_input(stream) -> dict`: parsea el JSON de stdin de PreToolUse.
    Fail-closed: si el parseo lanza, propaga un sentinel que el caller traduce a deny.
  - `emit(decision: Decision, *, out, err) -> int`: traduce a transporte y devuelve
    exit code, escribiendo en los streams dados (no en `sys.*`, para testear):
    - `deny` → aviso a `err` y **return 2**.
    - `allow` con `reason` de autoaprobación → JSON `permissionDecision:"allow"` a `out`, return 0.
    - `allow` normal → return 0 silencioso.
    - `ask` → JSON `permissionDecision:"ask"` a `out`, return 0.
- **Tests:** `tests/test_adapter_claude_code.py` — cada outcome → exit/stdout/stderr
  esperado; stdin inválido → deny/exit 2. Sin `subprocess`: streams en memoria (`io.StringIO`).
- **CA:** suite verde; ruff limpio.

## [ ] T2.5b — Scripts finos de hook por herramienta

- **Crear:** `hooks/write-guard.py`, `hooks/command-guard.py`, `hooks/read-guard.py`.
- **Cada script:** bootstrap de `sys.path` (añade `<repo>/src` desde `__file__`),
  `read_tool_input(sys.stdin)`, construye el `GuardAction` correspondiente
  (`write`→`file_path`+`content`/`new_string`; `command`→`command`; `read`→`file_path`/`path`),
  llama a `CoreGuard().evaluate(...)`, y `sys.exit(emit(decision, out=sys.stdout, err=sys.stderr))`.
  Solo wiring; nada de lógica de política en el script.
- **Tests:** `tests/test_hooks_smoke.py` — por `subprocess`, un payload allow y uno deny
  por script (espejo de los end-to-end de `alfred-dev`): write de secreto → exit 2;
  `rm -rf /` → exit 2; lectura de `.env` → exit 2; y sus contrapartes allow → exit 0.
- **CA:** suite verde; ruff limpio.

## [ ] T2.5c — Registro `hooks/hooks.json`

- **Crear:** `hooks/hooks.json` con bloques `PreToolUse` por matcher:
  `Write|Edit` → write-guard; `Bash` → command-guard; `Read|Glob|Grep` → read-guard.
- **Tests:** `tests/test_hooks_registration.py` — el JSON parsea; cada entrada apunta a
  un script existente en `hooks/`; los matchers esperados están presentes.
- **CA:** suite verde; ruff limpio. Cierra la fase 2.

---

## Definición de "fase completa"

T2.0–T2.5c en `[x]`, suite verde, ruff limpio, y un commit por tarea. El checkpoint de
diseño T2.5 se resolvió con Fer (2026-06-28); T2.5a–c completan el adaptador de hooks.
