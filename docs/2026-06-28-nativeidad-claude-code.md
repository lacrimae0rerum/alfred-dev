# Spike: qué hace de Alfred Dev un plugin nativo de Claude Code

- **Fecha:** 2026-06-28
- **Tipo:** Spike (investigación, sin código de producción)
- **Equipo:** Alfred (orquestación), Architect (superficies declarativas), Senior Dev (runtime/hooks/MCP)
- **Veredicto global:** Nativeidad alta y mayoritariamente idiomática. **Aprobado con condiciones cosméticas.** Cero hallazgos bloqueantes.

---

## 1. Tesis

Alfred Dev no *imita* a Claude Code ni envuelve scripting genérico en un plugin: se
**apoya sobre las primitivas oficiales** de la plataforma y deja que el runtime
**descubra y enrute** sus superficies. El plugin **declara**; Claude Code **ejecuta**.
Ese es el patrón correcto de un plugin nativo.

Cubre **las siete superficies nativas** que ofrece Claude Code:

| Superficie nativa | Mecanismo | Conteo real | Veredicto |
|---|---|---|---|
| Plugin manifest | `.claude-plugin/plugin.json` | 1 | Idiomático |
| Marketplace | `.claude-plugin/marketplace.json` | 1 | Idiomático |
| Subagentes (tool `Agent`) | `agents/*.md` | 19 | Idiomático |
| Slash commands | `commands/*.md` | 27 (25 publicados) | Idiomático |
| Agent Skills | `skills/*/SKILL.md` | 62 | Idiomático (uso avanzado) |
| MCP server | `.mcp.json` + `mcp/memory_server.py` | 1 (15 tools) | Idiomático y robusto |
| Hooks de ciclo de vida | `hooks/hooks.json` | 8 eventos / 14 scripts | Idiomático |

---

## 2. Superficies declarativas (lo que Claude Code descubre y enruta)

### 2.1 Plugin manifest — `.claude-plugin/plugin.json`
- Ruta canónica y esquema oficial: `name`, `version` (semver `0.6.1`), `description`,
  `author{}`, `homepage`, `repository`, `license`, `keywords`.
- `commands` como **array de rutas relativas con `./`**; `skills` como **array de
  directorios terminados en `/`** (un skill es la carpeta, no el `SKILL.md`).
- **Detalle clave de nativeidad:** NO declara `agents`, `hooks` ni `mcpServers`.
  No es un olvido: Claude Code los **auto-descubre por convención** (`agents/*.md`,
  `hooks/hooks.json`, `.mcp.json`). El plugin usa declaración explícita solo donde
  aporta (orden/selección de commands y skills) y descubrimiento por convención
  para el resto. Uso correcto de ambos modelos.

### 2.2 Marketplace — `.claude-plugin/marketplace.json`
- Estructura oficial (`name`, `owner.name`, `plugins[]`) con `source: "./"`
  (repo como fuente, patrón self-hosted) y catálogo correcto (`displayName`,
  `category: development`, `homepage`).

### 2.3 Subagentes — `agents/*.md` (19)
- Frontmatter canónico: `name`, `description`, `tools`, `model` (alias `opus`/`sonnet`,
  no IDs largos), `color`.
- **Mínimo privilegio por rol** en `tools`: `architect` y `qa-engineer` sin `Edit`
  (diseñan / prueban), `senior-dev` con `Edit` (implementa). Separación de
  responsabilidades a nivel de tooling.
- **El `description` está diseñado para el auto-routing**: multilínea, patrón
  "Usar cuando…" + triggers + bloques `<example>` con `<commentary>`. Es justo lo
  que el orquestador usa para decidir a quién delegar. Los triggers citan los slash
  commands con namespace (`/alfred-dev:feature`), cerrando el grafo command → agente.
- **Condición del architect RESUELTA:** los agentes listan `Agent` en `tools` como
  tool de orquestación. Verificado en runtime: en la versión actual de Claude Code el
  tool se expone **como `Agent`** (es el que usa esta propia sesión). No hay
  divergencia con `Task`.

### 2.4 Slash commands — `commands/*.md` (27, 25 publicados)
- Frontmatter con `description` + `argument-hint`; uso correcto de **`$ARGUMENTS`**
  para inyectar el input; cuerpo como prompt en segunda persona ("Eres Alfred…").
- **`${CLAUDE_PLUGIN_ROOT}`** dentro de los commands para resolver rutas del plugin
  instalado sin hardcodear (`config.md`, `audit.md`), con fallback documentado para
  desarrollo local.
- `_composicion.md` (prefijo `_`, no publicado) es un "protocolo compartido" que el
  resto de commands leen: DRY sobre la primitiva. Convención limpia, no canónica pero
  inocua.

### 2.5 Agent Skills — `skills/*/SKILL.md` (62)
- Estructura canónica `skills/<categoria>/<skill>/SKILL.md`; `plugin.json` apunta a
  las **categorías**.
- `description` cargado de triggers/sinónimos para invocación automática +
  **progressive disclosure** real en el cuerpo (resumen barato → detalle bajo demanda).
- **Uso avanzado de flags nativos:** `skills/alfred/alfred/SKILL.md` usa
  `disable-model-invocation: true` y `user-invocable: false`. El instalador lo copia a
  `~/.claude/skills/alfred/` cambiando `user-invocable` a `true` para ofrecer el alias
  corto `/alfred` sin colisionar con `/alfred-dev:*`. Uso sofisticado y correcto.

### 2.6 MCP server — `.mcp.json` + `mcp/memory_server.py`
- `.mcp.json` con estructura oficial `mcpServers.<nombre>`, transporte stdio,
  resolución vía **`CLAUDE_PLUGIN_ROOT` con fallback a `cwd`** (portable, no hardcoded).
- **Servidor MCP real, no un stub:** JSON-RPC 2.0 sobre stdio con doble framing
  (JSONL moderno + `Content-Length` legacy), `initialize` (negocia
  `protocolVersion`, default **`2025-06-18`**), `notifications/initialized`
  (sin respuesta, correcto), `tools/list` (con JSON Schema de inputs), `tools/call`
  (despacho por diccionario explícito "para reducir superficie de ataque",
  envoltura `content:[{type:text}]`, `isError`), y `ping`.
- **15 herramientas** de memoria (`memory_log_decision`, `memory_search`,
  `memory_export` a ADR, …) — las mismas que el sistema instruye a los agentes a usar.
- **Solo stdlib**, cero dependencias. Logs a **stderr** para no contaminar el stdout
  del protocolo. La superficie más robusta del plugin.

---

## 3. Integración de runtime (cómo Alfred se engancha al ciclo de vida)

### 3.1 Mapa de hooks — `hooks/hooks.json` (8 eventos)
Cobertura casi completa del ciclo de vida, todos vía `${CLAUDE_PLUGIN_ROOT}/hooks/...`:

`SessionStart` (matcher `startup|resume|clear|compact`, uno con `async:true`) ·
`UserPromptSubmit` · `UserPromptExpansion` (evento poco común: conocimiento fino del
runtime) · `Stop` · `PreCompact` · `PreToolUse` (matchers por herramienta:
`Write|Edit`, `Bash`, `Read`, …) · `PostToolUse`.

### 3.2 Los tres canales oficiales de decisión de hooks — usados los tres
Esta es la prueba de nativeidad real (un script genérico solo usaría exit codes):

1. **`exit 2` + stderr (fail-closed)** — `secret-guard.sh` (PreToolUse Write/Edit).
   Si no puede parsear/escanear, **bloquea**: "un hook de seguridad que permite cuando
   falla equivale a desactivar la protección". Delega detección en `core/secrets.py`
   (fuente única, sin duplicar patrones).
2. **JSON `hookSpecificOutput.permissionDecision: allow` por stdout** —
   `dangerous-command-guard.py` (PreToolUse Bash). Autoaprueba helpers deterministas
   de Alfred para destrabar ejecución headless sin prompt de permisos. Tokeniza con
   `shlex`, desenvuelve `sudo`/`env`/`sh -c`. Uso avanzado del protocolo de permisos.
3. **JSON `decision: block` + `reason` por stdout** — `stop-hook.py` (Stop). Si hay
   gate pendiente, **bloquea la parada** y devuelve por `reason` la fase/agentes/gate
   que falta. Convierte el evento Stop nativo en un **bucle de continuidad dirigido por
   estado** (patrón "ralph-loop"), con válvulas de escape (bypass one-shot con
   expiración, no bloquear tras prompts read-only como `/progress`).

   Más: `session-start.sh` usa **`additionalContext`** (`hookSpecificOutput`) para
   seedear el catálogo de comandos y `.claude/alfred-dev.local.md` al arrancar.

### 3.3 Diseño de dos fases para las quality gates
- `PostToolUse` (`evidence-guard.py`, `quality-gate.py`) es **fail-open** (exit 0,
  stderr informativo): **registra** evidencia de tests, no bloquea después de ejecutar.
- `Stop` (`stop-hook.py`) lee esa evidencia y **bloquea** si la gate no está superada.
- → **PostToolUse registra, Stop bloquea.** La "gate dura" la impone el Stop-hook; los
  PostToolUse son observadores. Elegante, pero conviene documentarlo para no
  confundirlo con un bloqueo inmediato.

### 3.4 Estado de sesión — ficheros `.claude/` del proyecto
Fichero-céntrico, atómico por proyecto, sin estado global oculto. Catálogo en
`core/continuity.py:50-74`: `alfred-dev-state.json` (fase activa),
`alfred-memory.db` (SQLite del MCP), `alfred-dev.local.md` (prefs → `additionalContext`),
`alfred-prefetch.json`/`-consumed.json` (helper-first), `alfred-handoff.json` (pausa),
`alfred-stop-hook-bypass.json` (bypass con expiración), etc. Los hooks son procesos
efímeros: reconstruyen continuidad leyendo disco en cada turno (única forma fiable).

### 3.5 Variables de entorno
- **`CLAUDE_PLUGIN_ROOT`**: uso ubicuo y correcto (hooks, `.mcp.json`, resolución de
  imports de `core/`). Es lo que desacopla el plugin del cwd y lo hace instalable en
  cualquier sitio. Nativeidad real.

---

## 4. Hallazgos honestos (lo que resta pureza, no bloqueante)

| # | Hallazgo | Severidad | Acción sugerida |
|---|---|---|---|
| 1 | No usa `CLAUDE_PROJECT_DIR`; deriva la raíz con `os.getcwd()`/`$PWD`/ascenso a `.claude/`. Funciona porque CC ejecuta hooks con cwd=raíz, pero es convención implícita, no contrato oficial. | Media (robustez) | `/alfred fix`: migrar a `CLAUDE_PROJECT_DIR` con `getcwd()` como fallback, test que verifique ambos caminos. |
| 2 | `displayName` en `plugin.json` no es campo del esquema base (sí del marketplace). El loader lo ignora. | Cosmético | Quitar de `plugin.json` o ignorar. |
| 3 | `agents/devops-engineer.md` parece tener `name:` duplicado. | Cosmético | Revisar frontmatter. |
| 4 | Cifras divergentes entre `plugin.json` ("10+9 agentes") y `marketplace.json` ("19 agentes, 62 skills"). | Cosmético | Unificar en el próximo release. |
| 5 | `hooks.json` triplica bloques `PostToolUse`/`Bash` (verboso, no incorrecto). | Cosmético | Consolidar opcionalmente. |
| 6 | Protocolo de control heterogéneo (unos hooks JSON, otros exit+stderr). Coherente con el rol (Pre bloquea, Post observa) pero puede leerse como inconsistencia. | Informativo | Documentar el patrón de dos fases (§3.3). |

**Condición original nº1 del architect (`Agent` vs `Task`): RESUELTA** — `Agent` es el
tool válido en la versión actual de Claude Code.

---

## 5. Conclusión

**Alfred Dev es un plugin nativo de Claude Code de manual.** Usa las siete primitivas
oficiales respetando cada contrato: rutas relativas con `./`, auto-descubrimiento por
convención, `CLAUDE_PLUGIN_ROOT` para portabilidad, `$ARGUMENTS`/`argument-hint` en
commands, `description` con triggers y `<example>` para auto-routing, flags avanzados de
skills (`disable-model-invocation`, `user-invocable`), MCP JSON-RPC 2.0 real
(`protocolVersion 2025-06-18`) y los **tres canales de decisión de hooks** según el rol
de cada uno. No inventa mecanismos paralelos donde la plataforma ya ofrece uno.

Lo que lo eleva por encima de "un plugin que funciona":
1. El **bucle de continuidad** Stop-hook ↔ estado en disco (orquestación real, no
   decorativa).
2. El **MCP server propio** con memoria persistente por proyecto.
3. La **autoaprobación de helpers** vía `permissionDecision` para flujos headless.
4. El **diseño de mínimo privilegio** por agente y el **patrón de dos fases** de gates.

**Veredicto: APROBADO CON CONDICIONES** (todas cosméticas o de robustez; ninguna
bloqueante). La única acción con valor técnico real es el hallazgo #1
(`CLAUDE_PROJECT_DIR`).

**No se requiere ADR:** el spike no toma una decisión arquitectónica nueva; describe y
valida la arquitectura existente. Si se aborda el hallazgo #1, ese cambio sí merecería
una nota breve.
