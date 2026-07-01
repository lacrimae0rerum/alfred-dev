# Instalacion en Codex

Alfred Dev for Codex se instala como plugin local standalone. La rama Codex no
usa instaladores ni comandos de Claude; usa la CLI `codex plugin` y copia los
subagents que Codex carga fuera del manifest de plugin.

## Requisitos

- Codex CLI instalado.
- Python 3.10 o superior.
- Este repositorio clonado en la rama `port/codex`.

## Instalacion local soportada

Desde la raiz del repositorio:

```bash
bash ./install.sh
```

El instalador hace estas cosas:

1. copia `prompts/*.md` a `~/.codex/prompts/`;
2. copia `.codex/agents/*.toml` a `~/.codex/agents/`;
3. elimina aliases personales obsoletos de pruebas anteriores;
4. registra este directorio como marketplace local con `codex plugin marketplace add`;
5. instala `alfred-dev@alfred-dev-local` con `codex plugin add`.

Despues abre una sesion nueva de Codex en el proyecto objetivo. Los comandos
quedan disponibles como skills del plugin:

```text
$alfred-dev:alfred
$alfred-dev:feature
$alfred-dev:quick
$alfred-dev:fix
$alfred-dev:spike
$alfred-dev:audit
$alfred-dev:ship
```

La entrada principal es `$alfred-dev:alfred`. Los contratos especializados
viven en `commands/` y se invocan con `$alfred-dev:<nombre>`.

## Verificacion

```bash
python3 -B -m unittest discover -s tests -v
python3 -B ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 -B ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/alfred
codex plugin list
```

Para verificar el MCP, instala el plugin y arranca Codex desde un proyecto. El
servidor publicado se llama `alfred-memory` y guarda datos en:

```text
<project>/.codex/alfred-memory.db
```

## Desinstalacion local

```bash
bash ./uninstall.sh
codex plugin remove alfred-dev
```

`uninstall.sh` elimina los prompts, subagents y aliases obsoletos copiados a `~/.codex`. El comando
`codex plugin remove` elimina la instalacion del plugin en Codex.

## Diferencias con Alfred Dev original

- El estado de proyecto vive en `.codex/`, no en `.claude/`.
- Los skill mentions `$alfred-dev:*` sustituyen a los slash commands namespaced.
- Los subagents Codex se materializan como TOML en `.codex/agents/`.
- El servidor MCP y los hooks se empaquetan en el plugin, pero deben validarse
  en una sesion Codex real porque dependen del host.
