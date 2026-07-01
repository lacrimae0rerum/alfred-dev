#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Hook de SessionStart para el plugin Alfred Dev.
#
# Se ejecuta al inicio de cada sesión (startup, resume, clear, compact)
# para inyectar contexto mínimo en Codex solo cuando hay una sesión activa.
# No imprime el catálogo de comandos, la configuración completa ni memoria:
# eso vive bajo demanda en $alfred-dev:help, $alfred-dev:config y
# $alfred-dev:search.
#
# Emite JSON en stdout con hookSpecificOutput que Codex interpreta
# como contexto adicional para la conversación.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Utilidades ---

# Genera el JSON final del hook a partir del contexto recibido por stdin.
# Usar stdin en vez de sys.argv evita el limite de ARG_MAX del kernel y
# problemas de truncado con caracteres especiales en cadenas largas.
emit_hook_json() {
  python3 -c "
import json, sys
context = sys.stdin.read().strip()
if not context:
    print('{}')
    raise SystemExit(0)
output = {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context}}
# json.dumps garantiza un JSON valido independientemente del contenido
print(json.dumps(output, ensure_ascii=False))
"
}

# --- Rutas de referencia ---

PROJECT_DIR="${PWD}"
STATE_FILE="${PROJECT_DIR}/.codex/alfred-dev-state.json"
PLUGIN_ROOT=$(cd "$(dirname "$0")/.." && pwd)

# --- Construcción del contexto ---

# Silencioso por defecto. La ayuda completa vive en $alfred-dev:help y los
# contratos detallados se cargan bajo demanda por cada skill.
CONTEXT=""

# --- Estado de sesión activa ---

# Si existe un fichero de estado, se extrae información relevante
# para que Codex sepa en qué punto del flujo se encuentra el usuario.
HAS_ACTIVE_STATE="no"
if [[ -f "$STATE_FILE" ]]; then
  STATE_INFO=$(python3 -c "
import json, sys

try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        state = json.load(f)

    comando = state.get('comando', 'desconocido')
    fase = state.get('fase_actual', 'desconocida')
    descripcion = state.get('descripcion', '')
    completadas = state.get('fases_completadas', [])
    num_completadas = len(completadas)

    # Si la sesión está completada, no aporta contexto útil
    if fase == 'completado':
        sys.exit(0)

    partes = []
    partes.append(f'Flujo activo: {comando}')
    partes.append(f'Fase actual: {fase}')
    if descripcion:
        partes.append(f'Descripción: {descripcion}')
    if num_completadas > 0:
        nombres = [c['nombre'] for c in completadas]
        partes.append(f'Fases completadas: {\", \".join(nombres)}')

    print('\n'.join(partes))
except FileNotFoundError:
    sys.exit(0)
except (json.JSONDecodeError, KeyError) as e:
    print(f'[Alfred Dev] Aviso: estado de sesión corrupto o incompleto: {e}', file=sys.stderr)
    sys.exit(0)
" "$STATE_FILE") || STATE_INFO=""

  if [[ -n "$STATE_INFO" ]]; then
    HAS_ACTIVE_STATE="yes"
    CONTEXT="${CONTEXT}

### Sesión de trabajo activa

${STATE_INFO}

Puedes continuar la sesión con \$alfred-dev:status o avanzar a la siguiente fase."
  fi
fi

# --- Siguiente paso sugerido ---

NEXT_INFO=$(PYTHONPATH="${PLUGIN_ROOT}" python3 -c "
import sys
sys.path.insert(0, sys.argv[2])
from core.continuity import suggest_next_action

suggestion = suggest_next_action(sys.argv[1])
print(suggestion['command'])
print(suggestion['reason'])
" "$PROJECT_DIR" "$PLUGIN_ROOT" 2>/dev/null || true)

if [[ "$HAS_ACTIVE_STATE" == "yes" && -n "$NEXT_INFO" ]]; then
  NEXT_COMMAND=$(printf '%s\n' "$NEXT_INFO" | sed -n '1p')
  NEXT_REASON=$(printf '%s\n' "$NEXT_INFO" | tail -n +2)

  if [[ -n "$NEXT_COMMAND" && -n "$NEXT_REASON" ]]; then
    CONTEXT="${CONTEXT}

### Siguiente paso recomendado

- \$alfred-dev:${NEXT_COMMAND}
- ${NEXT_REASON}"
  fi
fi

# --- Emisión del JSON de salida ---
#
# Se pasa el contexto por stdin a Python para evitar limites de ARG_MAX
# y garantizar un JSON valido independientemente del contenido.

printf '%s' "$CONTEXT" | emit_hook_json
