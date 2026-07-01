#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"
PROMPTS_DIR="${CODEX_HOME}/prompts"
AGENTS_DIR="${CODEX_HOME}/agents"

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI not found in PATH" >&2
  exit 1
fi

mkdir -p "${PROMPTS_DIR}" "${AGENTS_DIR}"

echo "[Alfred Codex] Installing custom prompts..."
cp "${REPO_ROOT}"/prompts/*.md "${PROMPTS_DIR}/"

echo "[Alfred Codex] Installing custom agents..."
cp "${REPO_ROOT}"/.codex/agents/*.toml "${AGENTS_DIR}/"

echo "[Alfred Codex] Removing obsolete personal aliases..."
rm -rf "${CODEX_HOME}/skills/alfred:dev" "${CODEX_HOME}/skills/alfred-dev"

echo "[Alfred Codex] Removing obsolete plugin namespace..."
codex plugin remove alfred-codex@alfred-codex-local >/dev/null 2>&1 || true
codex plugin marketplace remove alfred-codex-local >/dev/null 2>&1 || true

echo "[Alfred Codex] Registering local marketplace..."
codex plugin marketplace add "${REPO_ROOT}" >/dev/null || true

echo "[Alfred Codex] Installing plugin..."
codex plugin add alfred-dev@alfred-dev-local >/dev/null

echo "[Alfred Codex] Installed."
echo
echo "Start a new Codex session, then use:"
echo "  \$alfred-dev:alfred"
echo "  \$alfred-dev:feature <description>"
echo "  \$alfred-dev:quick <description>"
echo "  \$alfred-dev:fix <description>"
echo
echo "Use \$alfred-dev:* as the Codex-native Alfred command surface."
