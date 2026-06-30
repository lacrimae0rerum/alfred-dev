---
description: "Valida y reinstala Alfred Dev for Codex desde el worktree local"
---

# /prompts:alfred-dev-update

Actualiza la instalacion local de Alfred Dev for Codex desde el worktree actual.

## Protocolo

1. Confirma que el directorio actual contiene `.codex-plugin/plugin.json`.
2. Ejecuta:

```bash
python3 -B -m unittest discover -s tests -v
python3 -B ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

3. Si falla cualquier validacion, para y muestra el fallo.
4. Si pasa, ejecuta:

```bash
bash ./install.sh
```

5. Cierra indicando que hay que abrir una nueva sesion Codex para cargar la
   version reinstalada.

## Restricciones

- No uses la CLI de Claude para actualizar este port.
- No hagas push.
- No crees remotos.
- No cambies de rama.
- No borres memoria de proyectos del usuario.
- No declares actualizado sin evidencia real.
