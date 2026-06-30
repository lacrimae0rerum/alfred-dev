# Alfred Codex Known Gaps

## Open Gaps

| ID | Status | Area | Description | Mitigation |
| --- | --- | --- | --- | --- |
| BUG-001 | Open | Hooks | Alfred Dev hooks are not ported. Codex hook support has not been validated in this MVP. | Document as degraded guarantee; use explicit helper scripts and tests. |
| BUG-002 | Open | Orchestration | Claude `Agent` tool assumptions are removed. Codex-native subagent APIs are not required by the MVP. | Skill treats agents as role guidance and uses available Codex tools when present. |
| BUG-003 | Open | Commands | Claude slash commands are not ported. | The main Codex skill routes flows directly. |
| BUG-005 | Open | Visual style | Selina browser-based visual direction flow is represented as a conditional phase but no browser UI is ported. | Treat as manual style-direction artifact for MVP. |
| BUG-006 | Open | SonarQube | Audit flow documents security review expectations but does not automate Docker or SonarQube. | Keep audit as a role-guided flow until Codex-safe setup is implemented. |

## Resolved

| ID | Status | Area | Description | Evidence |
| --- | --- | --- | --- | --- |
| BUG-004 | Resolved | Marketplace | Standalone repo marketplace metadata with `source.path: "."` works for local installation. | `codex plugin marketplace add .`, `codex plugin add alfred-codex@alfred-codex-local`, and `codex plugin list` reported `installed, enabled`. |
