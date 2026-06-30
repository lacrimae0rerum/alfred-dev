#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"

rm -f "${CODEX_HOME}"/prompts/alfred.md
rm -f "${CODEX_HOME}"/prompts/alfred-dev-*.md

for agent in \
  alfred architect copywriter data-engineer devops-engineer github-manager \
  i18n-specialist librarian lucius performance-engineer product-owner \
  project-manager qa-engineer security-officer selina senior-dev seo-specialist \
  tech-writer ux-reviewer
do
  rm -f "${CODEX_HOME}/agents/${agent}.toml"
done

echo "[Alfred Codex] Removed prompts and custom agents."
echo "Disable or uninstall alfred-codex from Codex Plugins if desired."
