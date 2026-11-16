# CI workflow runs

## e76018eea9 (included V024 mutation — expected red)

- Architecture Enforcement: failure (`IMMUTABLE_MIGRATION_MUTATION` on V024)
- Cursor Rules Governance: success
- api-delpi console: ran

https://github.com/roberiooliveiradev/delpi-central/actions/runs/43858905486

## 3ba6c292f6 (withdraws V024 mutation)

Tip after withdrawal; Architecture Enforcement still sees V024 M vs parent.
Follow-up tip (docs-only) is the CI-green candidate.

## Policy

Versioned migrations are immutable in git. DAVI DEV unblock remains
owner/env residual; live HTTP E2E evidence was captured while DAVI was
temporarily healthy locally.
