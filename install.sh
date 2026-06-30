#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"
PROMPTS_DIR="${CODEX_HOME}/prompts"
AGENTS_DIR="${CODEX_HOME}/agents"
SKILLS_DIR="${CODEX_HOME}/skills"

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI not found in PATH" >&2
  exit 1
fi

mkdir -p "${PROMPTS_DIR}" "${AGENTS_DIR}" "${SKILLS_DIR}/alfred:dev"

echo "[Alfred Codex] Installing custom prompts..."
cp "${REPO_ROOT}"/prompts/*.md "${PROMPTS_DIR}/"

echo "[Alfred Codex] Installing custom agents..."
cp "${REPO_ROOT}"/.codex/agents/*.toml "${AGENTS_DIR}/"

echo "[Alfred Codex] Installing /alfred:dev alias..."
cp "${REPO_ROOT}/aliases/alfred-colon-dev/SKILL.md" "${SKILLS_DIR}/alfred:dev/SKILL.md"

echo "[Alfred Codex] Registering local marketplace..."
codex plugin marketplace add "${REPO_ROOT}" >/dev/null || true

echo "[Alfred Codex] Installing plugin..."
codex plugin add alfred-codex@alfred-codex-local >/dev/null

echo "[Alfred Codex] Installed."
echo
echo "Start a new Codex session, then use:"
echo "  /alfred:dev"
echo "  /prompts:alfred"
echo "  /prompts:alfred-dev-feature <description>"
echo "  /prompts:alfred-dev-quick <description>"
echo
echo "Use /alfred:dev as the main Alfred entrypoint; detailed flows remain available as /prompts:alfred-dev-*."
