# Prompts operativos

Codex no carga slash commands namespaced desde plugins del mismo modo que
Alfred Dev original. En esta rama, la entrada principal se instala como skill
personal directo `/alfred:dev`; cada contrato especializado se publica tambien
como custom prompt en `~/.codex/prompts/`.

## Entrada principal

| Comando | Uso |
|---|---|
| `/alfred:dev` | Entrada directa principal. Enruta al flujo o vista correcta sin obligar al usuario a elegir a mano. |
| `/prompts:alfred` | Entrada contextual. Decide si toca mapear, discutir, continuar, verificar o abrir un flujo. |

## Flujos principales

| Prompt | Uso |
|---|---|
| `/prompts:alfred-dev-feature <descripcion>` | Ciclo completo: producto, estilo visual condicional, arquitectura, desarrollo, calidad, documentacion y entrega. |
| `/prompts:alfred-dev-quick <descripcion>` | Cambio pequeno y acotado con menos ceremonia. |
| `/prompts:alfred-dev-fix <descripcion>` | Bugfix con diagnostico, correccion TDD y validacion. |
| `/prompts:alfred-dev-spike <tema>` | Investigacion tecnica sin compromiso de implementacion. |
| `/prompts:alfred-dev-audit` | Auditoria de calidad, seguridad, arquitectura y documentacion. |
| `/prompts:alfred-dev-ship` | Preparacion de release con gates finales. |

## Continuidad y operacion

Tambien se instalan prompts para continuidad y vistas operativas:

- `/prompts:alfred-dev-map-codebase`
- `/prompts:alfred-dev-discuss`
- `/prompts:alfred-dev-next`
- `/prompts:alfred-dev-status`
- `/prompts:alfred-dev-progress`
- `/prompts:alfred-dev-pause`
- `/prompts:alfred-dev-resume`
- `/prompts:alfred-dev-verify`
- `/prompts:alfred-dev-standup`
- `/prompts:alfred-dev-blocked`
- `/prompts:alfred-dev-in-progress`
- `/prompts:alfred-dev-validate`
- `/prompts:alfred-dev-search`
- `/prompts:alfred-dev-sync-github`
- `/prompts:alfred-dev-memory-ui`
- `/prompts:alfred-dev-lucius`
- `/prompts:alfred-dev-config`
- `/prompts:alfred-dev-help`
- `/prompts:alfred-dev-update`

Los ficheros `commands/*.md` se conservan como contratos fuente del port y para
compatibilidad documental con Alfred Dev, pero la superficie invocable en Codex
es `prompts/*.md`.
