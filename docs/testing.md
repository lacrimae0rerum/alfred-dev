# Tests

Alfred Dev for Codex usa pruebas por capas. La suite Python cubre la lógica local del port, los contratos de manifiesto validan la superficie que Codex carga, y los smokes manuales deben ejecutarse solo en un entorno Codex aislado porque instalar este plugin en la sesión de desarrollo puede contaminar el propio agente.

Esta página es la guía operativa para desarrollar sin romper la release. Si solo estas tocando una función pequeña, empieza por `python3 -B -m unittest discover -s tests -v`. Si estas preparando publicación, usa los gates de contrato descritos más abajo.

La suite actual se ejecuta con `unittest` y no requiere instalar el plugin. Cada fichero de test cubre un modulo o contrato concreto y se puede ejecutar de forma aislada o en conjunto.

---

## Comandos rápidos

Para ejecutar toda la suite local:

```bash
python3 -B -m unittest discover -s tests -v
```

Para validar la superficie publicable del plugin:

```bash
python3 -B ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 -B ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/alfred
```

---

## Gates de contrato Codex

El port Codex no depende de un único comando mágico. Cada gate cubre una frontera distinta y evita que una mejora local rompa el manifiesto, los wrappers `$alfred-dev:*`, el MCP de memoria o la documentación pública.

| Gate | Comando | Qué valida |
|------|---------|------------|
| Suite local | `python3 -B -m unittest discover -s tests -v` | Core Python reducido, manifiestos, MCP, rutas `.codex/`, docs públicas y wrappers de comando. |
| Plugin shape | `python3 -B ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .` | Manifiesto `.codex-plugin/plugin.json`, marketplace local, skills y MCP declarados. |
| Skill shape | `python3 -B ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/alfred` | Frontmatter y estructura mínima del skill principal. |
| Smoke manual aislado | instalación en otro `CODEX_HOME` o en una VM/sesión limpia | Verifica que `$alfred-dev:alfred`, `$alfred-dev:feature`, hooks y MCP cargan en Codex real sin contaminar esta sesión. |

No ejecutes `install.sh` dentro de esta sesión de Codex de desarrollo. Para pruebas reales, usa un `CODEX_HOME` temporal o una sesión separada.

---

## Cobertura principal

La suite de `tests/` cubre las superficies mínimas que Codex consume:

- **Core y memoria**: orquestador, configuración, continuidad, memoria SQLite, compactación, sincronización, UI local y sanitización de secretos.
- **MCP**: servidor `alfred-memory`, forma JSON-RPC, herramientas publicadas y fallback cuando la memoria no esta disponible.
- **Hooks**: captura de actividad, guardas de comandos peligrosos, evidencias, secretos, lecturas sensibles, quality gates, prefetch, session start, stop hook y compactación.
- **Instaladores**: `install.sh` y `uninstall.sh`, sin ejecutar instalación real durante la suite local.
- **Comandos y agentes**: 19 agentes Markdown, 19 subagents TOML, 26 contratos en `commands/` y 25 wrappers `$alfred-dev:*` en `skills/`.
- **Skills**: inventario de 62 skills de dominio heredados más 25 wrappers de comandos Codex.
- **Publicación**: coherencia de versión y ausencia de rutas locales o claims Claude en docs públicas.
- **Selina y visual**: catálogo de estilos, dirección visual, variantes, helper visual y servidor local de apoyo.

Los tests siguen usando `unittest` como estilo interno y `pytest` como runner. Cada fichero se puede ejecutar de forma aislada cuando quieres iterar rápido:

```bash
python3 -B -m unittest tests.test_manifest -v
python3 -B -m unittest tests.test_public_docs -v
python3 -B -m unittest tests.test_memory_mcp -v
```

---

## Patrones de testing usados

Los tests que necesitan disco usan `tempfile.NamedTemporaryFile` o `tempfile.TemporaryDirectory` y limpian en `tearDown()` o `try/finally`. Ningun test debe escribir estado permanente en el repositorio, en `~/.codex/` ni en una base de datos real salvo que el propio test lo aísle en un directorio temporal.

Los modulos del core se importan añadiendo la raiz del proyecto a `sys.path`:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

Los ficheros con guion, como `hooks/spelling-guard.py`, se cargan con `importlib.util.spec_from_file_location` porque no se pueden importar con sintaxis Python normal.

Los tests de memoria verifican a dos niveles: usan la API pública de `MemoryDB` y, cuando hace falta, abren SQLite directamente para comprobar tablas, índices, permisos, WAL y relaciones persistidas.

Los tests de sanitización construyen patrones sensibles en runtime para no dejar secretos falsos completos en el código fuente:

```python
fake_key = "AKIA" + "TESTMEMORYDB1234"
fake_sk = "sk-" + "a" * 25
```

---

## Integraciones externas

Los checks que necesiten red, Docker, GitHub CLI, navegador o instalación real de Codex deben vivir fuera de la suite local y ejecutarse con autorización explícita. Su función es probar contratos externos de forma explícita: GitHub, Codex CLI, SonarQube/Docker y otras integraciones que pueden tener side effects o depender de autenticación.

---

## Límites honestos de cobertura

### Calidad generativa

Los prompts de comandos, agentes y skills se pueden auditar por estructura, herramientas, referencias y coherencia, pero no se puede garantizar con un test determinista que Codex produzca siempre una respuesta excelente. La validación conversacional final requiere revisión manual en una sesión Codex limpia.

### Sesiones reales de Codex

La suite simula hooks, MCP y discovery hasta donde es razonable, pero la carga final depende de Codex, su caché de plugins, el estado de autenticación y el selector interactivo. La evidencia de release debe incluir smokes en worktree o instalación aislada, especialmente para `$alfred-dev:alfred`, `$alfred-dev:*` y MCP.

Aunque la cobertura automatizada ya es amplia, todavía hay zonas donde la validación manual dentro de Codex sigue siendo importante: la experiencia completa de los skill mentions en conversación real, la ergonomía de los agentes como prompts largos, el encadenado completo de hooks con eventos reales del runtime y, en la rama `Alfred-Astro`, la UX final del companion visual de Selina.

### Servicios con side effects

GitHub, SonarQube, Docker y cualquier herramienta externa con credenciales se prueban con preflights y contratos. Los tests no deben crear issues, releases, contenedores persistentes ni cambios remotos sin una bandera explícita y documentación de evidencia.

Los commands son prompts, no código imperativo, pero eso no significa que queden fuera de la suite. El repo incluye tests de contratos para continuidad, PM ops, ayuda, auditoría y superficie pública (`test_progress_contract.py`, `test_pm_contract.py`, `test_discuss_contract.py`, `test_audit_prompt_contract.py`, `test_public_surface_contract.py`, entre otros). Lo que no se puede automatizar por completo es la calidad conversacional final del comando dentro de Codex.

### Plataformas no presentes

El port actual incluye instaladores Bash. Si se añade PowerShell en el futuro, debe tener tests de contrato y evidencia en Windows real o PowerShell disponible.

Los agentes siguen la misma lógica que los commands: son ficheros Markdown que definen la personalidad y las instrucciones de cada agente especializado. El motor de personalidad (`core/personality.py`) y parte de la composición del equipo sí están cubiertos por tests, pero la calidad final del prompt de cada agente sigue requiriendo validación empírica.

---

## Como añadir un nuevo test

1. Crea un fichero `tests/test_<modulo>.py` con clases `unittest.TestCase` y nombres de test descriptivos.
2. Usa directorios temporales para cualquier escritura.
3. Evita depender de una instalación real en `~/.codex/` salvo que el test cree un `HOME` temporal.
4. Si el cambio afecta comandos, agentes, skills, hooks, MCP o instaladores, añade también un contrato en una suite existente.
5. Ejecuta el test nuevo y la suite relacionada antes de cerrar el cambio.

Ejemplo mínimo:

```python
#!/usr/bin/env python3
"""Tests para mi_modulo."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.mi_modulo import funcion_a_testear


class TestMiModulo(unittest.TestCase):
    def test_comportamiento_esperado(self):
        self.assertEqual(funcion_a_testear("entrada"), "salida")


if __name__ == "__main__":
    unittest.main()
```
