---
name: alfred
description: "Entrada contextual de Alfred Dev for Codex: enruta solicitudes de software engineering hacia flujos con agentes especializados, memoria MCP y quality gates verificables."
---

# Alfred Dev for Codex

Usa este skill cuando el usuario pida trabajar con Alfred, arrancar un flujo
Alfred, continuar una sesión Alfred, auditar, implementar, arreglar, investigar
o entregar software con el equipo especializado del plugin.

## Superficie Codex

Codex no publica comandos slash arbitrarios desde plugins con la misma forma que
Alfred Dev original. En este port la invocación operativa usa menciones de
skills del plugin con el mismo namespace funcional:

- `$alfred-dev:alfred`
- `$alfred-dev:feature`
- `$alfred-dev:quick`
- `$alfred-dev:fix`
- `$alfred-dev:spike`
- `$alfred-dev:audit`
- `$alfred-dev:ship`

Cuando el usuario escriba una intención de Alfred sin skill explícito, aplica
el mismo contrato de `commands/alfred.md` si está disponible en el plugin.

## Protocolo

1. Identifica si la intención corresponde a continuidad, discovery, feature,
   quick, fix, spike, audit, ship, config, progreso, pausa o validación.
2. Lee primero el estado operativo del proyecto si existe:
   - `.codex/alfred-dev-state.json`
   - `.codex/alfred-handoff.json`
   - `.codex/alfred-uat.json`
   - `.codex/alfred-dev.local.md`
3. Usa el servidor MCP `alfred-memory` para memoria persistente cuando esté
   disponible; si falla, continúa sin inventar memoria y reporta el fallo.
4. Invoca o simula explícitamente los subagents de Codex equivalentes al equipo
   Alfred cuando el flujo lo requiera: product-owner, architect, senior-dev,
   security-officer, qa-engineer, devops-engineer, tech-writer, project-manager,
   selina y agentes opcionales habilitados.
5. Respeta las quality gates del flujo. Autopilot puede resolver solo gates de
   usuario configuradas; nunca salta tests, seguridad, evidencia ni aprobación
   humana de producción.
6. No declares avances, tests, auditorías, aprobaciones ni memoria sin evidencia
   real de herramienta, fichero, salida de comando o confirmación explícita.

## Restricciones

- No presentes `/alfred-dev:*` como slash command nativo de Codex. La forma
  invocable soportada por Codex es `$alfred-dev:*`.
- No uses rutas `.claude/` ni variables del runtime Claude para estado Codex.
- No escribas secretos, credenciales ni datos sensibles en memoria.
- No amplíes el flujo más allá del objetivo del usuario.
- Si una gate falla, detén el avance, registra la causa y propone la corrección
  mínima verificable.
