#!/usr/bin/env bash
# install-hermes.sh — Instala Alfred Dev como personalidad y skills en Hermes
#
# Uso:  bash install-hermes.sh
#
# Este script:
#   1. Registra la personalidad "alfred" en Hermes (vía hermes config set)
#   2. Compila e instala los 62 skills de Alfred Dev en ~/.hermes/skills/
#
# Requisitos:
#   - Hermes Agent instalado (hermes CLI en PATH)
#   - Alfred Dev source en ~/Projects/alfred-dev (o ALFRED_DEV_ROOT)
#   - Python 3.10+ (para adaptación de frontmatter)
#
# NO requiere: permisos sudo, claves API, ni modificar el repositorio.

set -euo pipefail

ALFRED_DEV_ROOT="${ALFRED_DEV_ROOT:-$HOME/Projects/alfred-dev}"
HERMES_SKILLS="$HOME/.hermes/skills"

echo "=== Alfred Dev → Hermes Installer ==="
echo "  Alfred source: $ALFRED_DEV_ROOT"
echo "  Hermes skills: $HERMES_SKILLS"
echo ""

# Step 1: Validate prerequisites
if ! command -v hermes &>/dev/null; then
    echo "ERROR: 'hermes' CLI not found. Install Hermes Agent first."
    echo "  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"
    exit 1
fi

if [ ! -d "$ALFRED_DEV_ROOT/skills" ]; then
    echo "ERROR: Alfred Dev source not found at $ALFRED_DEV_ROOT"
    echo "  Set ALFRED_DEV_ROOT or clone the repo:"
    echo "  git clone https://github.com/686f6c61/alfred-dev.git \$HOME/Projects/alfred-dev"
    exit 1
fi

SKILL_COUNT=$(find "$ALFRED_DEV_ROOT/skills" -name "SKILL.md" | wc -l)
echo "  Found $SKILL_COUNT skills in $ALFRED_DEV_ROOT/skills/"
echo ""

# Verify we found all 62 skills (from Alfred Dev catalog)
if [ "$SKILL_COUNT" -lt 62 ]; then
    echo "  ⚠ Warning: expected 62+ skills, found $SKILL_COUNT"
fi
echo ""

# Step 2: Register Alfred personality
echo "=== Step 1/2: Registering Alfred personality ==="

hermes config set agent.personalities.alfred 'Eres Alfred, un orquestador de desarrollo de software.
Diriges un equipo de 19 agentes especializados (product-owner, architect, senior-dev,
security-officer, qa-engineer, devops-engineer, tech-writer, y 9 agentes opcionales).
Tienes acceso a 62 skills en 15 dominios (producto, arquitectura, desarrollo, seguridad,
calidad, devops, documentación, datos, ux, rendimiento, github, seo, marketing, estilo).

No ejecutas las tareas tú mismo: delegas en el agente adecuado según la fase del flujo.
Cuando recibes una petición, identificas qué agente necesita intervenir, compilas su prompt
desde los artefactos de Alfred, y lanzas un subagente via delegate_task().

Reglas:
- product-owner decide QUÉ problema se resuelve y POR QUÉ.
- architect decide CÓMO se implementa técnicamente.
- Tú (alfred) decides CUÁNDO interviene cada uno, en qué orden y con qué gate.
- Nunca redefines alcance ni diseño por tu cuenta.
- Los guards de seguridad bloquean secretos (API keys, tokens) y comandos destructivos.
- Usa CoreGuard y ToolRegistry para cada operación de tool.' && echo "  ✓ Personalidad 'alfred' registrada"

# Step 3: Install skills
echo "=== Step 2/2: Installing $SKILL_COUNT skills ==="

INSTALLED=0
FAILED=0

for skill_path in "$ALFRED_DEV_ROOT/skills"/*/*/SKILL.md; do
    # Extract category and skill name from path
    rel_path="${skill_path#$ALFRED_DEV_ROOT/skills/}"
    category="$(echo "$rel_path" | cut -d/ -f1)"
    skill_name="$(echo "$rel_path" | cut -d/ -f2)"
    dest_dir="$HERMES_SKILLS/$category/$skill_name"

    mkdir -p "$dest_dir"

    # Adapt frontmatter: ensure Hermes-required fields exist
    python3 -c "
import re, yaml, pathlib

src_path = '$skill_path'
src = pathlib.Path(src_path).read_text()

# Parse frontmatter
m = re.search(r'\\n---\\s*\\n', src[3:])
if not m:
    # No frontmatter — wrap entire content in minimal Hermes SKILL.md
    body = src.strip()
    pathlib.Path('$dest_dir/SKILL.md').write_text(
        '---\\nname: $skill_name\\ndescription: Alfred Dev skill from $category\\n'
        'version: 1.0.0\\nauthor: Alfred Dev\\nlicense: MIT\\n'
        'metadata:\\n  hermes:\\n    tags: [$category]\\n---\\n\\n' + body
    )
else:
    fm = yaml.safe_load(src[3:m.start()+3])
    body = src[m.start()+6:]

    # Ensure Hermes-required fields
    if not isinstance(fm, dict):
        fm = {'name': '$skill_name'}
    fm.setdefault('name', '$skill_name')
    fm.setdefault('description', f'Alfred Dev skill from $category')
    fm.setdefault('version', '1.0.0')
    fm.setdefault('author', 'Alfred Dev')
    fm.setdefault('license', 'MIT')
    fm.setdefault('metadata', {}).setdefault('hermes', {}).setdefault('tags', ['$category'])

    new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False).strip()
    pathlib.Path('$dest_dir/SKILL.md').write_text('---\\n' + new_fm + '\\n---\\n\\n' + body.lstrip())
" && INSTALLED=$((INSTALLED + 1)) || FAILED=$((FAILED + 1))

    # Progress indicator
    if [ $((INSTALLED % 10)) -eq 0 ]; then
        echo -n "  [$INSTALLED/$SKILL_COUNT]..."
    fi
done

echo ""
echo "  ✓ $INSTALLED skills installed"
if [ $FAILED -gt 0 ]; then
    echo "  ⚠ $FAILED skills failed (check path names with special chars)"
fi

echo ""
echo "=== Done ==="
echo ""
echo "Alfred Dev está listo para usar en Hermes."
echo ""
echo "Para activarlo en tu sesión actual:"
echo "  /personality alfred"
echo ""
echo "Para usarlo siempre por defecto:"
echo "  hermes config set display.personality alfred"
echo ""
echo "O directamente desde la CLI:"
echo "  hermes --personality alfred"
echo ""