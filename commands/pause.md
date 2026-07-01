---
description: "Pausa el trabajo actual y deja un handoff explícito"
---

# $alfred-dev:pause

Eres Alfred. Vas a pausar la sesión actual sin perder el hilo.

## Protocolo

Primero ejecuta el helper determinista del plugin:

```bash
python3 .codex/alfred-continuity.py pause "$PWD"
```

Si devuelve salida útil, úsala como respuesta final y termina.
No la reenvuelvas con un segundo resumen: el helper ya deja flujo, fase, gate,
handoff y siguiente acción.

Solo si el helper falla, cae al modo manual:

1. Lee `.codex/alfred-dev-state.json`.
2. Si no existe o la sesión ya está completada, dilo con claridad y NO inventes un handoff.
3. Si existe una sesión activa:
   - resume comando, descripción, fase actual y fases completadas;
   - identifica la gate pendiente;
   - identifica el siguiente paso concreto para retomar.
4. Escribe estos artefactos:
   - `.codex/alfred-handoff.json`
   - `docs/project/handoff.md`
   - actualiza `.codex/alfred-dev-state.json` añadiendo `paused_at` y `paused_via: "/alfred-dev:pause"`
5. El handoff debe incluir como mínimo:
   - flujo activo
   - descripción
   - fase actual y número
   - fases completadas
   - gate pendiente
   - artefactos registrados
   - comando de retorno `$alfred-dev:resume`
   - siguiente acción concreta al volver
6. Como `.codex/*` es sensible en Codex, NO uses `Write` ni `Edit` para esos ficheros. Si de verdad tienes que caer al modo manual, usa Bash.

## Restricciones

- NO marques la sesión como completada.
- NO borres `.codex/alfred-dev-state.json`.
- NO hagas un handoff vacío o genérico.
- Cierra con una confirmación breve indicando dónde quedó guardado el handoff.
