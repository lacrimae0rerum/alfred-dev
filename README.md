# alfred-dev → Hermes port (branch: port/hermes)

Branch del port de [Alfred Dev](https://github.com/686f6c61/alfred-dev) desde
**Claude Code** hacia **Hermes Agent**. Arquitectura hexagonal: núcleo puro +
puertos neutros + adaptador Hermes.

## Estado del port

| Fase | Qué | Estado |
|---|---|---|
| 0 | Extraer núcleo a paquete `alfred_core` | ✅ |
| 1 | Puerto `HostContext` (rutas) | ✅ |
| 2 | Guards como política pura + adaptador CC | ✅ |
| 3 | Compilador de prompts → formato neutro JSON | ✅ |
| 4 | **Adaptador Hermes** (6 puertos) | ✅ **MVP completado** |
| 5 | Degradaciones declaradas por host | ✅ Documentado |

## MVP (Hermes)

El adaptador Hermes implementa 6 puertos:

- **AgentRunner** → `delegate_task()` (subagentes reales)
- **MemoryPort** → `memory()` tool
- **HooksPort** → `CoreGuard.evaluate()` directo (sin subprocess)
- **SkillsPort** → `skill_manage()` tool
- **HostContextPort** → rutas relativas a `.hermes`
- **ToolRegistry** → mapeo Bash→terminal, Agent→delegation, Edit→file

## Instalación

```bash
# Una vez, desde cualquier directorio:
bash install-hermes.sh

# Luego en cualquier sesión Hermes:
/personality alfred
```

Esto registra la personalidad Alfred + 62 skills compilados desde el plugin original.

## Verificación

```bash
uv run pytest -q        # 457 tests, 0 fallos
uv run ruff check src tests   # 0 errores
```

## Layout

```
src/alfred_core/          # núcleo portable
src/alfred_core/ports/    # 6 puertos + adaptador Hermes + test doubles
tests/                    # suite de regresión
hooks/                    # hooks originales de CC (referencia)
docs/                     # handover, PRDs, auditoría de portabilidad
install-hermes.sh         # instalador para Hermes
```

## Rama principal

El plugin original de Alfred Dev para Claude Code vive en `main` de este repo.
Este branch (`port/hermes`) contiene el port a Hermes Agent.