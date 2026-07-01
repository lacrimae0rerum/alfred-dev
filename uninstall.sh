#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-${HOME}/.codex}"

rm -f "${CODEX_HOME}"/prompts/alfred.md
rm -f "${CODEX_HOME}"/prompts/alfred-dev-*.md
rm -rf "${CODEX_HOME}/skills/alfred:dev" "${CODEX_HOME}/skills/alfred-dev"

for agent in \
  alfred architect copywriter data-engineer devops-engineer github-manager \
  i18n-specialist librarian lucius performance-engineer product-owner \
  project-manager qa-engineer security-officer selina senior-dev seo-specialist \
  tech-writer ux-reviewer
do
  rm -f "${CODEX_HOME}/agents/${agent}.toml"
done

echo "[Alfred Codex] Removed prompts, custom agents, and obsolete Alfred aliases."
codex plugin remove alfred-dev@alfred-dev-local >/dev/null 2>&1 || true
codex plugin marketplace remove alfred-dev-local >/dev/null 2>&1 || true
echo "[Alfred Codex] Disabled local alfred-dev plugin namespace when present."
