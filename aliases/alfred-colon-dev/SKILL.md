---
name: alfred:dev
description: "Entrada directa de Alfred Dev for Codex como /alfred:dev. Enruta al asistente contextual Alfred y desde ahi a los flujos feature, quick, fix, spike, audit, ship y continuidad."
---

# /alfred:dev

Actua como la entrada contextual principal de Alfred Dev for Codex.

Este alias existe porque los comandos historicos de Alfred Dev se invocaban
como slash commands directos. En Codex, el plugin publica prompts y skills; este
skill personal materializa el comando directo `/alfred:dev`.

## Protocolo

0. Si el usuario pide una prueba de instalación o te pide responder
   exactamente con un token concreto, responde con ese token y no abras flujo.
1. Trata los argumentos del usuario como si hubieran entrado por
   `/prompts:alfred`.
2. Si existe `~/.codex/prompts/alfred.md`, leelo y sigue ese contrato canonico.
3. Si no existe, localiza el plugin instalado `alfred-codex` en
   `~/.codex/plugins/cache/` y usa `prompts/alfred.md` de la version activa.
4. Si tampoco puedes localizarlo, informa de que el alias esta instalado pero
   falta el plugin, y pide reinstalar con `bash ./install.sh`.
5. Mantén las reglas de Alfred: no inventar tests, gates, agentes, memoria ni
   evidencia; usar `.codex/` para estado; respetar autopilot solo donde aplique.

## Rutas operativas

Al enrutar, usa estos contratos:

- feature: `/prompts:alfred-dev-feature`
- quick: `/prompts:alfred-dev-quick`
- fix: `/prompts:alfred-dev-fix`
- spike: `/prompts:alfred-dev-spike`
- audit: `/prompts:alfred-dev-audit`
- ship: `/prompts:alfred-dev-ship`
- continuidad: `/prompts:alfred-dev-next`, `/prompts:alfred-dev-resume`,
  `/prompts:alfred-dev-progress`, `/prompts:alfred-dev-status`
