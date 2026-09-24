# E0 Baseline — TV-DASHBOARD-PRESENTATION-001

| Campo | Valor |
|---|---|
| EXECUTION_HEAD | `1ceedd48079516b401fad34495aee7abdbcc66cb` |
| PLAN_BASE_HEAD | `0afe0cac1caaa8f194b81e24631af97e10184d04` (ancestry) |
| BRANCH | `main` |
| READY_TO_EXECUTE | YES |

## WORKING_TREE isolation (CONFIRMADO)

**Não tocar (paralelo dirty):**

- `.cursor/plans/davi_herda_teo_vista.plan.md`
- `minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md`
- `plugins/tv-dashboard/tsconfig.tsbuildinfo` (artifact)

**Escopo TV-only:** `tv-dashboard-api/**`, `plugins/tv-dashboard/**` (authority bridge), evidence + ADR.

## Gate

WORKING_TREE isolation documentada — PASS.
