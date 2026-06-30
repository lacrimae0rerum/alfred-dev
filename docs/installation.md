# Instalacion en Codex

Alfred Dev for Codex se instala como plugin local standalone. La rama Codex no
usa instaladores ni comandos de Claude; usa la CLI `codex plugin` y copia dos
superficies que Codex carga fuera del manifest de plugin: prompts y subagents.

## Requisitos

- Codex CLI instalado.
- Python 3.10 o superior.
- Este repositorio clonado en la rama `port/codex`.

## Instalacion local soportada

Desde la raiz del repositorio:

```bash
bash ./install.sh
```

El instalador hace cuatro cosas:

1. copia `prompts/*.md` a `~/.codex/prompts/`;
2. copia `.codex/agents/*.toml` a `~/.codex/agents/`;
3. registra este directorio como marketplace local con `codex plugin marketplace add`;
4. instala `alfred-codex@alfred-codex-local` con `codex plugin add`.

Despues abre una sesion nueva de Codex en el proyecto objetivo. Los prompts
quedan disponibles como:

```text
/prompts:alfred
/prompts:alfred-dev-feature
/prompts:alfred-dev-quick
/prompts:alfred-dev-fix
/prompts:alfred-dev-spike
/prompts:alfred-dev-audit
/prompts:alfred-dev-ship
```

Codex no expone comandos slash arbitrarios de plugin como `/alfred-dev:feature`.
En este port esos contratos viven en `prompts/` y se invocan con
`/prompts:<nombre>`.

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
codex plugin remove alfred-codex
```

`uninstall.sh` elimina los prompts y subagents copiados a `~/.codex`. El comando
`codex plugin remove` elimina la instalacion del plugin en Codex.

## Diferencias con Alfred Dev original

- El estado de proyecto vive en `.codex/`, no en `.claude/`.
- Los prompts Codex sustituyen a los slash commands namespaced.
- Los subagents Codex se materializan como TOML en `.codex/agents/`.
- El servidor MCP y los hooks se empaquetan en el plugin, pero deben validarse
  en una sesion Codex real porque dependen del host.
