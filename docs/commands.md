# Comandos operativos

Codex no carga slash commands namespaced desde plugins del mismo modo que
Alfred Dev original. En esta rama, cada contrato se publica como skill del
plugin `alfred-dev` y se invoca con `$alfred-dev:*`.

## Entrada principal

| Comando | Uso |
|---|---|
| `$alfred-dev:alfred` | Entrada contextual. Decide si toca mapear, discutir, continuar, verificar o abrir un flujo. |

## Flujos principales

| Skill | Uso |
|---|---|
| `$alfred-dev:feature <descripcion>` | Ciclo completo: producto, estilo visual condicional, arquitectura, desarrollo, calidad, documentacion y entrega. |
| `$alfred-dev:quick <descripcion>` | Cambio pequeno y acotado con menos ceremonia. |
| `$alfred-dev:fix <descripcion>` | Bugfix con diagnostico, correccion TDD y validacion. |
| `$alfred-dev:spike <tema>` | Investigacion tecnica sin compromiso de implementacion. |
| `$alfred-dev:audit` | Auditoria de calidad, seguridad, arquitectura y documentacion. |
| `$alfred-dev:ship` | Preparacion de release con gates finales. |

## Continuidad y operacion

Tambien se publican skills para continuidad y vistas operativas:

- `$alfred-dev:map-codebase`
- `$alfred-dev:discuss`
- `$alfred-dev:next`
- `$alfred-dev:status`
- `$alfred-dev:progress`
- `$alfred-dev:pause`
- `$alfred-dev:resume`
- `$alfred-dev:verify`
- `$alfred-dev:standup`
- `$alfred-dev:blocked`
- `$alfred-dev:in-progress`
- `$alfred-dev:validate`
- `$alfred-dev:search`
- `$alfred-dev:sync-github`
- `$alfred-dev:memory-ui`
- `$alfred-dev:lucius`
- `$alfred-dev:config`
- `$alfred-dev:help`
- `$alfred-dev:update`

Los ficheros `commands/*.md` se conservan como contratos fuente del port y para
compatibilidad documental con Alfred Dev, pero la superficie invocable en Codex
es `$alfred-dev:*`.
