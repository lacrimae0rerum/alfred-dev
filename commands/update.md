---
description: "Valida y reinstala Alfred Dev for Codex desde el worktree local"
---

# $alfred-dev:update

Este contrato se conserva por compatibilidad con Alfred Dev. En Codex se invoca
como `$alfred-dev:update`.

## Objetivo

Actualizar la instalacion local del port Codex sin tocar ramas remotas ni el
fork original.

## Protocolo

1. Verifica que estas dentro del repo del plugin o localiza el repo instalado.
2. Ejecuta validacion antes de reinstalar:

```bash
python3 -B -m unittest discover -s tests -v
python3 -B ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

3. Si la validacion falla, no reinstales. Muestra el fallo y la correccion
   minima recomendada.
4. Si la validacion pasa, reinstala desde el worktree local:

```bash
bash ./install.sh
```

5. Pide abrir una sesion nueva de Codex para cargar skills, subagents, hooks y
   MCP actualizados.

## Restricciones

- No uses la CLI de Claude para actualizar este port.
- No hagas push.
- No crees remotos.
- No cambies de rama.
- No borres memoria de proyectos del usuario.
- No declares actualizado sin salida real de validacion e instalacion.
