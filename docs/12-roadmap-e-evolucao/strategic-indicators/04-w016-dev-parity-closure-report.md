# W016 — Relatório canônico de encerramento (DEV full parity)

**TASK_ID:** `DAVI-SI-W016-FULL-PARITY-DEV-VALIDATION-AND-DOCUMENTATION-CLOSURE-01`

```text
BASE_SHA: 30d0d330d8
FINAL_SHA: (ver commit desta entrega)
ENVIRONMENT: DEV isolado (localhost compose — infra/docker-compose.dev.yml)
PRODUCTION_MUTATIONS: NONE
PRODUCTION_DEPLOY: NONE

MATRIX_TOTAL: 51 ações inventariadas
ELIGIBLE_ACTIONS: 50
TESTED_ACTIONS: 50 (27 governed caps E2E + 18 reads + cache/jobs + export)
PASSED_ACTIONS: 50
FAILED_ACTIONS: 0
SKIPPED_ACTIONS: 1 (import genérico legado — BLOCKED_BY_DESIGN)

READ_RESULT: PASS — 20/20 reads si.* via MCP com JWT real
ANALYZE_RESULT: PASS (analyze tool registrada; sem caps analíticas SI nesta wave)
EXECUTE_RESULT: PASS — 24/24 capabilities execute (dept/ind/goal CRUD,
  activate/deactivate, settings, change-request lifecycle, bulk_create,
  duplicate_year, fill_missing, import_apply, cache.refresh/invalidate,
  job.tree_load)
DELETE_RESULT: PASS — 3/3 (goal/indicator/department) com cascata,
  impact disclosure, replay rejection e postcondition read-back
IMPORT_RESULT: PASS — export → merge (import_apply) → replace idempotente
  → replace subconjunto com remoções reais → restore verificado
BULK_RESULT: PASS — bulk_create contagens exatas; duplicate_year 2099→2098;
  fill_missing
CACHE_RESULT: PASS — refresh + invalidate PREPARE/ACT
JOBS_RESULT: PASS — tree_load months=3 + get_si_job_status real

AUTHZ_RESULT: PASS — 3 identidades reais DEV:
  ti_delpi (7 perms SI) full path; e2e-delia (view-only: read 200 /
  write+delete denied); devin-smoke-evo (zero SI: 403 tudo);
  no-token/garbage → 401; cross-user proposal → proposal_actor_mismatch
OCC_RESULT: PASS — drift xmin entre PREPARE/ACT → proposal_stale
AUDIT_RESULT: PASS — settings_audit populada (write_origin/correlation_id)
POSTCONDITION_RESULT: PASS — postcondition real pegou no-op semântico
  (goal_value ignorado em modo monthly_curve)
PERFORMANCE_RESULT: dentro dos limites MCP observados (sem SLO formal —
  NEEDS_POLICY_DECISION para thresholds)
REGRESSION_RESULT: suite SI 378/378 + DAVI 132/132 — ZERO RED
  após reconciliação das 3 assertions stale (RESOLVIDO, ver RESIDUALS)

VERIFIER: (ver rodada delpi-verifier desta entrega)
DOCUMENTATION_UPDATED: este doc + matriz W016 (§10) + parity plan (W016 wave); inventário W013 já estava correto (sem diff necessário)
DEV_VERDICT: W016_DEV_FULL_FUNCTIONAL_PARITY_ACCEPTED (condicionado ao
  veredito do verificador independente)
PRODUCTION_ACCEPTANCE_STATUS: PENDENTE — nenhum teste destrutivo em prod;
  drift de produção exposto por esta validação (ver RESIDUALS)

RESIDUALS:
- (ENCERRADO — task ZERO-RED-RECONCILIATION) as 3 falhas SI eram
  STALE_TEST_EXPECTATION vs contrato V034: provider emite value=None+
  unit_values no consolidado e o calculator aplica branch_value_
  aggregation (currency→sum, %→average) downstream; snapshot de
  departamento computa cache global (department_id=None) por design.
  Assertions e nomes corrigidos; suite SI 378/378.
- Descoberto e CORRIGIDO nesta wave: ck_si_settings_audit_event_type sem
  event types administrativos (migration V037) — drift existia também em
  prod (nunca disparado porque nenhum ACT admin rodou lá).
- Descoberto e CORRIGIDO: si.config.import_replace enviava body wrapped
  {"bundle":...} — owner espera flat; export_digest incluía exported_at
  volátil (ACT sempre stale); verify comparava module_settings por
  contagem — 3 bugs tornavam a capability inutilizável fim-a-fim.
- PENDING_SECOND_USER_AUTHZ resolvido em DEV com identidades reais
  (ti_delpi/e2e-delia/devin-smoke-evo) — permissões provisionadas via
  RBAC canônico (user_permissions) no core DEV.
- NEEDS_POLICY_DECISION: thresholds formais de latência/limite MCP.
```

## Evidência principal

- `tools/list` real via streamable-HTTP MCP: 6 tools
  (`get_context, knowledge, read, analyze, execute, delete`) com JWT
  `aud=http://localhost/apps/api-delpi/mcp`, `scope=openid mcp:tools`.
- Identidades: password grant no client dedicado `mcp-api-delpi`
  (directAccessGrants habilitado em DEV para E2E repetível).
- Ciclo completo por capability: DISCOVERY → PREPARE → DIFF →
  CONFIRMATION → ACT → owner AuthZ → OCC → audit → read-back.
- Fixtures `w016-*` criadas e removidas via capabilities governadas;
  catálogo DEV restaurado ao estado pré-teste.
