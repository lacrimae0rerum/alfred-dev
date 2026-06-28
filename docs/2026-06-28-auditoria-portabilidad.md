# Auditoría de portabilidad — Alfred Dev usable por otro agente

- **Fecha:** 2026-06-28
- **Tipo:** Spike / auditoría ampliada (investigación, sin código de producción)
- **Continúa:** `2026-06-28-nativeidad-claude-code.md` (qué lo hace nativo de CC)
- **Mapa base:** `../project/codebase-map-coupling.md` (qué tocar)
- **Objetivo:** diseñar la estrategia para que Alfred corra **fuera de Claude Code**,
  bajo otro harness/agente, reutilizando el máximo del activo actual.

---

## 1. Tesis y reencuadre

El spike de nativeidad demostró que Alfred es un plugin de CC "de manual". Esta
auditoría invierte la lente: **cada punto de nativeidad es un punto de acoplamiento**.
Portar = sustituir las primitivas de CC por una capa de abstracción (puertos) con
adaptadores por host.

El hallazgo central del mapeo: Alfred son **tres capas** (núcleo de código, sistema de
prompts, runtime de plataforma). El código es lo fácil (~200 LOC acoplados de ~3500). Lo
caro es el **modelo de hooks** (intercepción de cada tool-call) y el **sistema de prompts
declarativo** (19 agents + 27 commands + 62 skills en frontmatter CC). Una migración
honesta presupuesta esas dos, no los 3500 LOC.

---

## 2. Arquitectura objetivo: hexagonal (puertos y adaptadores)

Tres anillos. El núcleo no sabe en qué host corre; los adaptadores traducen.

```
┌─────────────────────────────────────────────────────────┐
│  ADAPTADORES (uno por host)                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ claude-code  │ │ agent-sdk    │ │ generic-cli /    │ │
│  │ (actual)     │ │ (Anthropic)  │ │ custom harness   │ │
│  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘ │
│         │  implementan los PUERTOS ↓         │           │
├─────────┼────────────────┼──────────────────┼───────────┤
│  PUERTOS (interfaces estables, def. una vez)             │
│  HostContext · ToolGuard · LifecycleSink ·               │
│  ContextProvider · AgentRunner · StateStore              │
├─────────────────────────────────────────────────────────┤
│  NÚCLEO PURO  (ya existe, ~3500 LOC)                     │
│  orchestrator · memory · secrets · personality ·         │
│  optional_agents · selina_*                              │
└─────────────────────────────────────────────────────────┘
```

### Los 6 puertos (interfaces a definir)

| Puerto | Reemplaza a (primitiva CC) | Responsabilidad |
|---|---|---|
| `HostContext` | `CLAUDE_PLUGIN_ROOT`, `$PWD/.claude/`, rutas | Resolver plugin_root, project_dir, state_dir, memory_db_path |
| `ToolGuard` | hooks `PreToolUse` + exit codes/JSON | Decidir `allow / deny / ask` ante una acción del agente; canal neutral |
| `LifecycleSink` | hooks `Stop`/`PreCompact`/`PostToolUse` | Recibir eventos de ciclo de vida (registrar memoria, evidencia) |
| `ContextProvider` | hook `SessionStart` + `additionalContext` | Aportar el contexto de arranque/continuidad |
| `AgentRunner` | tool `Agent`/`Task`, slash commands | Lanzar un subagente con system prompt + tools y recoger el resultado |
| `StateStore` | ficheros `.claude/*`, `memory_sync` | Persistir/leer estado de sesión y proyectar memoria |

El núcleo (`orchestrator`, `memory`, `secrets`) ya está casi listo para esto: solo
necesita recibir un `HostContext` en vez de calcular rutas con `os.getcwd()`.

---

## 3. Estrategia de desacople por superficie

### 3.1 Rutas y entorno — **fácil** (1 día)
- Introducir `HostContext` con `plugin_root`, `project_dir`, `state_dir`, `memory_db`.
- El adaptador `claude-code` lo rellena con `CLAUDE_PLUGIN_ROOT` (+ `CLAUDE_PROJECT_DIR`,
  cerrando la deuda del spike de nativeidad). Otros adaptadores lo inyectan a mano.
- Sustituir en `config_loader.py`, `memory_server.py`, `session_report.py`,
  `continuity.py` los paths fijos por `ctx.*`.
- Riesgo: bajo. Es find-and-inject mecánico.

### 3.2 Guards / hooks PreToolUse — **el punto duro** (mayor esfuerzo)
El problema: los guards (secret, dangerous-command, sensitive-read, prefetch) asumen que
existe un evento `PreToolUse` que CC dispara y que puede **bloquear vía exit 2**. Otro
host puede no ofrecer intercepción de tool-calls.

Estrategia en dos niveles:
1. **Lógica pura primero.** Extraer la decisión de cada guard a funciones puras
   `evaluate(action) -> Decision{allow|deny|ask, reason}` (la mayoría ya delega en
   `core/secrets.py`). Esto desacopla la *política* del *transporte*.
2. **Adaptador por host:**
   - `claude-code`: envuelve la función pura en el script de hook actual (lee stdin,
     emite exit 2 / `permissionDecision`). Sin cambio de comportamiento.
   - `agent-sdk` / `custom`: si el host tiene callbacks de tool-use (p.ej. `canUseTool`
     del Agent SDK), conecta ahí; si no, **degradación honesta**: ejecuta los guards
     como wrapper alrededor de las tools que el host sí expone, o los reduce a
     verificación post-hoc (registrar, no bloquear) y **lo declara explícitamente**.
- Riesgo: alto. Algunos hosts no permiten bloqueo pre-acción; hay que documentar qué
  garantías de seguridad se pierden. No fingir que un guard "bloquea" si el host solo
  permite observar.

### 3.3 Sistema de prompts (agents/commands/skills) — **depende del host** (alto)
Es Markdown con frontmatter CC; no ejecuta, lo conduce el modelo del host. Opciones:
- **Compilador de artefactos.** Un transformador que lee `agents/*.md`, `commands/*.md`,
  `skills/*/SKILL.md` y emite el formato del host destino (system prompts + registro de
  herramientas + definiciones de comando). El contenido (la "inteligencia" de cada
  agente) se conserva; cambia el envoltorio.
- **Mapa de tool names.** Tabla `tools:` CC → tools del host (`Bash`→`shell`, etc.) para
  reescribir los campos `tools:` y los matchers.
- Riesgo: medio-alto. El contenido es portable; el routing automático por `description`/
  `<example>` y el progressive disclosure dependen de que el host tenga ese mecanismo. Si
  no, se degrada a invocación explícita.

### 3.4 Memoria / MCP — **casi listo** (2-4 h)
- El MCP server ya habla un estándar abierto (JSON-RPC 2.0). Cualquier host con cliente
  MCP lo consume tal cual; solo inyectar `memory_db` vía `HostContext`.
- Alternativa para hosts sin MCP: exponer `memory.py` como **librería** importable
  (`from alfred_core.memory import MemoryDB`). Ya es pura.
- Riesgo: bajo.

### 3.5 Estado y continuidad — **medio** (2-3 días)
- `continuity.py` y `memory_sync.py` son los más atados (convención `~/.claude/projects/`).
- Esconder tras `StateStore`: `claude-code` mantiene la proyección a memoria nativa CC;
  otros adaptadores persisten en su propio formato o no proyectan.
- El bucle de continuidad (Stop-hook ↔ estado) solo existe si el host tiene un evento
  Stop bloqueante. Si no, la continuidad pasa a ser cooperativa (el orquestador relee
  estado al inicio de cada turno). Funciona, con menos garantía de no-parada.

---

## 4. Viabilidad por host destino

| Host destino | Encaje | Esfuerzo | Qué se conserva / qué se pierde |
|---|---|---|---|
| **Claude Agent SDK** (Anthropic) | **Alto** | Bajo-medio | Mismos conceptos: subagentes, tools, hooks (`PreToolUse`/`canUseTool`), MCP. Se conserva casi todo. Mejor primer objetivo de port. |
| **Harness/CLI propio** | Medio | Medio-alto | Núcleo + memoria + prompts portables; hay que implementar los 6 puertos y el bucle de tools. Control total. |
| **Otro IDE-agent (Cursor, etc.)** | Medio-bajo | Alto | Depende de si expone subagentes/hooks. Probable degradación de guards a observación. |
| **Otro proveedor LLM (no Claude)** | Bajo | Muy alto | Hay que traducir prompts y reimplementar runtime entero; los `model: opus/sonnet` y el tono se reescriben. |

**Recomendación de objetivo:** portar primero al **Claude Agent SDK**. Es el host con
mayor isomorfismo conceptual; valida la arquitectura de puertos con el mínimo de
fricción y deja `claude-code` como segundo adaptador (no como única implementación).

---

## 5. Plan por fases (incremental, sin big-bang)

1. **Fase 0 — Extraer el núcleo a paquete** (`alfred_core`): mover `orchestrator`,
   `memory`, `memory_config`, `secrets`, `personality`, `optional_agents` a un paquete
   instalable con `pyproject.toml`, sin tocar comportamiento. Tests de regresión del
   orquestador y la memoria como red. **Inequívoco, valor inmediato.**
2. **Fase 1 — `HostContext`**: inyectar rutas; cerrar la deuda `CLAUDE_PROJECT_DIR`.
   Adaptador `claude-code` rellena desde env. Verde en CC = sin regresión.
3. **Fase 2 — Puertos de política**: extraer la lógica pura de los guards a
   `evaluate()`; el hook actual pasa a ser un adaptador fino. La seguridad no cambia en CC.
4. **Fase 3 — Compilador de prompts**: transformador agents/commands/skills → formato
   neutro + mapa de tool names. Empezar por 1 agente y 1 command de prueba.
5. **Fase 4 — Adaptador Agent SDK**: implementar los 6 puertos contra el SDK; correr un
   flujo `/spike` mínimo de extremo a extremo fuera de CC.
6. **Fase 5 — Degradaciones declaradas**: documentar por host qué garantías (bloqueo
   pre-acción, continuidad no-parada, auto-routing) se conservan o degradan.

---

## 6. Riesgos y honestidad operativa

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Host sin intercepción pre-tool → guards no bloquean | Pérdida de garantía de seguridad | Degradación declarada; no fingir bloqueo; wrapper de tools donde se pueda |
| Auto-routing por `description` no existe en el host | Agentes no se eligen solos | Fallback a invocación explícita; conservar el contenido |
| Bucle de continuidad depende de Stop bloqueante | Menos garantía de no-parada | Continuidad cooperativa (relectura de estado por turno) |
| Deriva entre adaptadores (CC vs SDK) | Doble mantenimiento | El núcleo y los puertos son la fuente única; los adaptadores son finos |
| Reescribir prompts a otro proveedor | Coste alto, riesgo de perder matiz | No es objetivo inmediato; centrarse en hosts Claude |

**Nota de honestidad:** este documento es análisis y diseño, **no se ha ejecutado
ninguna migración ni se ha escrito código**. Las estimaciones de esfuerzo son órdenes de
magnitud, no compromisos. La viabilidad real del adaptador Agent SDK debe validarse con
un prototipo de Fase 4 antes de comprometer el plan completo.

---

## 7. Conclusión

Portar Alfred fuera de Claude Code es **viable y de coste moderado** si se ataca por
capas y se elige bien el primer host. El núcleo de código ya es casi una librería; el
trabajo de valor está en (1) formalizar 6 puertos, (2) convertir los guards en política
pura + adaptador, y (3) compilar el sistema de prompts a otro formato. El primer objetivo
natural es el **Claude Agent SDK** por isomorfismo conceptual, dejando `claude-code` como
un adaptador más en lugar de la única implementación.

**Siguiente paso recomendado:** ejecutar la **Fase 0** (extraer `alfred_core` a paquete
con tests de regresión). Es inequívoca, no rompe nada en CC y desbloquea todo lo demás.
Se puede abrir como `/alfred-dev:feature` o `/alfred-dev:quick` según el tamaño que
quieras darle.
