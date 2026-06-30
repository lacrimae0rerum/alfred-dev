# Alfred Dev para Hermes Agent

> Branch: `port/hermes` — Port del plugin [Alfred Dev](https://github.com/686f6c61/alfred-dev) desde Claude Code hacia [Hermes Agent](https://hermes-agent.nousresearch.com/).

Alfred Dev es un equipo de **19 agentes de IA especializados** (product-owner, architect, senior-dev, security-officer, qa-engineer, devops-engineer, tech-writer, y 9 opcionales) que orquestan el ciclo completo de desarrollo de software: desde el PRD hasta el despliegue, con quality gates verificables entre cada fase.

Este branch porta ese ecosistema desde **Claude Code** hacia **Hermes Agent**, conservando el núcleo lógico (~3500 LOC) y reemplazando solo el transporte (hooks, subagentes, skills, memoria).

---

## ⚡ Instalación

```bash
# 1. Clonar este branch
git clone -b port/hermes https://github.com/lacrimae0rerum/alfred-dev.git

# 2. Ejecutar el instalador (una vez)
bash alfred-dev/install-hermes.sh

# 3. En cualquier sesión de Hermes, activar Alfred
/personality alfred
```

El instalador:
- Registra la personalidad `alfred` en Hermes (`hermes config set`)
- Compila e instala los **62 skills** originales de Alfred Dev en `~/.hermes/skills/`
- No requiere sudo, claves API, ni modificar el repositorio

### Requisitos

- [Hermes Agent](https://hermes-agent.nousresearch.com/) instalado y configurado
- [Alfred Dev](https://github.com/686f6c61/alfred-dev) clonado en `~/Projects/alfred-dev` (o variable `ALFRED_DEV_ROOT`)
- Python 3.10+ (para adaptación de frontmatter de skills)

---

## 🧠 Qué incluye

### 19 agentes especializados

| Agente | Rol | Responsabilidad |
|---|---|---|
| **Alfred** | Orquestador | Coordina flujos, activa agentes, evalúa gates |
| **SonIA** | Project Manager | Descompone PRD en tareas, kanban, trazabilidad |
| **El buscador de problemas** | Product Owner | PRDs, historias de usuario, criterios de aceptación |
| **Selina** | Directora de estilo | Dirección visual (solo proyectos con UI) |
| **El dibujante de cajas** | Arquitecto | Diseño de sistemas, ADRs, diagramas |
| **El artesano** | Senior Dev | Implementación TDD, refactoring, commits |
| **El paranoico** | Security Officer | OWASP, threat modeling, compliance |
| **El rompe-cosas** | QA Engineer | Test plans, code review, testing E2E |
| **El fontanero** | DevOps Engineer | Docker, CI/CD, deploy, monitoring |
| **El traductor** | Tech Writer | Documentación técnica y de usuario |
| *+ 9 opcionales* | | Data Engineer, UX Reviewer, Performance, GitHub Manager, SEO, Copywriter, Librarian, i18n, Lucius |

### 62 skills en 15 dominios

```
producto/     arquitectura/   desarrollo/    seguridad/     calidad/
devops/       documentación/  datos/         ux/            rendimiento/
github/       seo/            marketing/     estilo/        alfred/
```

### 6 flujos de trabajo

| Flujo | Fases | Para qué |
|---|---|---|
| `feature` | 7 (producto → estilo → arquitectura → desarrollo → calidad → docs → entrega) | Funcionalidades completas |
| `quick` | 3 (diseño → desarrollo → validación) | Cambios pequeños |
| `fix` | 3 (diagnóstico → corrección TDD → validación) | Bugs |
| `spike` | 1 (investigación) | Prototipos, benchmarks |
| `ship` | 4 (auditoría → changelog → versionado → deploy) | Releases |
| `audit` | 1 (4 agentes en paralelo) | Auditoría completa |

### Guards de seguridad (sin subprocess)

Los guards se ejecutan **in-process** vía `CoreGuard.evaluate()`, sin depender de scripts externos ni subprocesos:

| Guard | Bloquea |
|---|---|
| `evaluate_write` | Secretos (API keys, tokens, passwords) en archivos |
| `evaluate_command` | Comandos destructivos (`rm -rf /`, `DROP DATABASE`, `git push --force`) |
| `evaluate_read` | Lectura de archivos sensibles (`.env`, claves privadas, credenciales) |

### Persistencia

- **Memoria SQLite** con FTS5 para búsqueda de decisiones, commits y eventos
- **Exportación/importación** a Markdown (formato ADR)
- **Sanitización** automática de secretos

---

## 📦 Estructura del proyecto

```
src/alfred_core/              # Núcleo portable (~3500 LOC)
├── orchestrator.py           # Máquina de estados de flujos + gates
├── memory.py                 # Persistencia SQLite (WAL + FTS5)
├── guards/                   # Política pura de seguridad
├── compiler/                 # Compilador de prompts CC → JSON neutro
├── host.py                   # Resolución de rutas (HostContext)
├── ports/                    # 6 interfaces + adaptador Hermes
│   ├── __init__.py           # ABCs: AgentRunner, Memory, Hooks, Skills, HostContext, ToolRegistry
│   ├── hermes.py             # Adaptador Hermes (implementación real)
│   └── noop.py               # Test doubles para tests unitarios
├── personality.py            # Catálogo de agentes y voces
├── config_loader.py          # Configuración de proyecto + detección de stack
├── optional_agents.py        # Registro de agentes opcionales
├── secrets.py                # Patrones de detección de secretos
└── memory_config.py          # Configuración de memoria
tests/                        # 457 tests, suite de regresión
hooks/                        # Hooks originales de Claude Code (referencia)
docs/                         # Documentación del port
├── host-degradations-hermes.md  # Diferencias CC vs Hermes
├── 2026-06-28-auditoria-portabilidad.md  # Auditoría de portabilidad
├── codebase-map-coupling.md  # Mapa de acoplamiento
└── prd/                      # PRDs del proyecto
install-hermes.sh             # Instalador para Hermes
```

---

## 🧪 Tests y calidad

```bash
cd alfred-dev
uv run pytest -q                  # 457 tests, 0 fallos esperados
uv run ruff check src tests       # 0 errores esperados
```

El core de `alfred_core` tiene **dependencia cero** — solo pytest y ruff para desarrollo.

---

## ⚠️ Diferencias con Claude Code

| Funcionalidad | Claude Code | Hermes |
|---|---|---|
| Slash commands (`/alfred-dev:feature`) | ✅ Nativo | ❌ Se reemplaza con prompt conversacional |
| Plugin system (`plugin.json`) | ✅ Marketplace | ❌ Se reemplaza con personalidad + skills |
| Modelo por agente (opus vs sonnet) | ✅ Configurable | ❌ Hermes decide el modelo |
| Routing automático por description | ✅ Nativo | ❌ Alfred orquestador decide |
| Guards de seguridad | ✅ Via hooks subprocess | ✅ Via CoreGuard in-process (más fiable) |
| Subagentes | ✅ Tool `Agent`/`Task` | ✅ `delegate_task()` |
| Skills | ✅ SKILL.md en plugin | ✅ SKILL.md en `~/.hermes/skills/` |
| Calidad y gates | ✅ Mismo núcleo | ✅ Mismo núcleo |

Detalle completo en [`docs/host-degradations-hermes.md`](docs/host-degradations-hermes.md).

---

## 📖 Licencia

MIT. Proyecto independiente, no afiliado a Anthropic ni al equipo de Claude Code.