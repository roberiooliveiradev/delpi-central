# 205 — Goal-to-owner causal remediation and production deploy

- **Task:** `DELIA-C3-GOAL-TO-OWNER-CAUSAL-REMEDIATION-AND-PRODUCTION-DEPLOY-01`
- **Base / implementation SHA:** `ab5048df0c` → `43650dd20e21b601a9405eaed0c574bd8049ca15` (`fix(delia,davi): close goal-to-owner evidence gaps (C3 Task 13)`), pushed and verified on `origin/main`.
- **Scope:** two causally-proven minimal corrections — one owner-side (`api-delpi`), one consumer-side (`delia-api`) — deployed to the real production host via the established SSH runbook. LangGraph B1 preserved; Engine A unchanged; no new port/planner/registry/framework; no prompt or budget changes.

## 1. Causal gate (§10)

```
INCIDENT=E1 ("Me dê dois exemplos de terminal bala")
FIRST_PROVEN_DIVERGENCE=owner contract projection — the DELPI OpenAPI
  declares per-parameter `description` semantics ("Termos contidos na
  descrição" etc.) but `build_argument_json_schema`/`_param_schema`
  stripped them: the published DAVI candidate `argument_schema`
  carried types only. The governed argument model had
  `business_subject` + an instruction to bind it into descriptive
  fields, but the owner's field-level semantics were unavailable.
LEGITIMATE_OWNER=api-delpi dynamic-information argument schema
EVIDENCE=real OpenAPI baseline params carry `description`;
  _param_schema copied type/enum/pattern/format/bounds/default only
CAUSE_STATUS=PROVEN
FIX_LOCATION=argument_validator._param_schema (bounded description
  propagation)
CONTRACT_CHANGE_REQUIRED=NO

INCIDENT=E2 ("Qual o último processo do Transforma+?")
FIRST_PROVEN_DIVERGENCE=bounded page walk gated to COUNT-intent only
  + early-return when an authoritative `total` exists. TÉO `process`
  returns `ORDER BY updated_at DESC` pages with `total` on every
  response; a declared `ordering` requirement therefore produced
  `coverage_unproven`/`insufficient` after page 1 forever — the
  owner-supported path was unreachable.
LEGITIMATE_OWNER=delia-api existing pagination orchestration
EVIDENCE=_maybe_aggregate_paginated_count gates: count-goal-only +
  `if envelope.total_count: return`; TÉO envelope {total,items}
  recognized by _TOTAL_KEYS
CAUSE_STATUS=PROVEN
FIX_LOCATION=orchestration._maybe_aggregate_paginated_count —
  extended the SAME walk to declared answer_requirements coverage
  gaps (ordering/complete_coverage/min_items), schema-derived page
  cursor, unchanged bounds
CONTRACT_CHANGE_REQUIRED=NO
```

## 2. Fixes (minimal diffs)

**A — api-delpi** (`external_capabilities/dynamic_information/argument_validator.py`, +12 lines): `_param_schema` now propagates a bounded owner-provided `description` (stripped, capped at 300 chars) into the published JSON schema. Schema stays untrusted metadata-as-data; no instruction semantics. No parallel schema path.

**B — delia-api** (`capability_provision/orchestration.py`, ~+160 lines): `_maybe_aggregate_paginated_count` — COUNT trigger preserved verbatim; new second trigger `_requirements_need_more_pages(goal, envelope, facts)` fires only when declared `answer_requirements` (ordering / complete_coverage / min_items) cannot be proven from the gathered evidence AND the owner publishes a completable envelope. `_page_cursor` resolves the page argument **contractually** from the bound capability schema (parameter named `page` / `*page*` type int) — never invented. All existing integrity guards kept: first-page start, contiguity, stable IDs, dedup, owner-total consistency, max-pages, deadline headroom, no material replay. For the requirements path `complete` is asserted only when `gathered >= owner_total` (COUNT still trusts the authoritative total itself).

Engines: the walk lives in `_governed_owner_path`, shared by LangGraph B1 and Engine A — both inherit the correction; parity holds by construction.

## 3. RED → GREEN

- `delia-api/tests/test_c3_goal_to_owner_execution.py` (11 tests, TÉO/DAVI-real envelope shapes): **5 RED** before the fix — ordering requirement unreachable on multi-page owner (`coverage_unproven` after 1 call), min_items coverage gap, `page` cursor derived from bound schema, no fabricated totals/ordering. **11/11 GREEN** after — including locks: COUNT-only goals unchanged, no-cursor capability stops truthfully, budget/deadline respected, duplicate/stable-ID guards intact.
- `api-delpi/tests/test_davi_dynamic_read.py` (+5 tests): **5 RED** — real baseline params lose descriptions. **5/5 GREEN** — `description`/`page`/`page_size` texts propagated bounded; absent/oversized/blank descriptions excluded.

## 4. Regression / gates

- delia-api suite: ~2700 collected, **2 pre-existing environmental failures** (`/docs` + `/plugins` mounts absent in the test container — same class documented in Task 12; unrelated to the diff); everything else GREEN. Focused E1/E2/pagination/CRI/evidence surface: 199+11 GREEN.
- api-delpi DAVI suite: **418 GREEN**.
- `audit_architecture_phase3.py` + `audit_backend_boundaries.py`: 0 new findings.
- Residual search: no hardcoded `terminal bala`/`Transforma+` paths, no direct DELPI provider bypass, no new retries/budgets/authorization changes, no PREPARE/ACT surface touched.
- Unrelated concurrent stock-inventory worktree changes preserved untouched; only 4 task-owned files staged.

## 5. Production deploy (srv-api, SSH runbook)

- Host `operador@192.168.1.237`; repo `/home/operador/projetos/delpi-central` fast-forwarded `49eee133 → 43650dd20`.
- Rollback tags created before rebuild: `infra-api-delpi:goal-owner-rollback-d94e443e`, `infra-delia-api:goal-owner-rollback-def538a0` (prior healthy images retained).
- Sequential build per runbook: **api-delpi** (`42ad9defd8cb`, healthy) then **delia-api** (`dad53fa242f6`, healthy). ~90 other containers untouched.
- Boot log: `delia_orchestration_engine selected=langgraph`, `cri` effective, `env=production`, Kimi/OpenRouter config preserved.
- Deployed-code verification inside running containers: `_requirements_need_more_pages` + `_page_cursor` present in delia-api; `description` propagation present in api-delpi `_param_schema`.

## 6. Bounded authenticated smoke (2 turns, identity `user`, scope `openid profile email`)

| # | Turn | Latency | Capability | Outcome |
|---|---|---|---|---|
| S1 | "Me dê dois exemplos de terminal bala." | ~77.8s | `davi.execute_delpi_information` (discover→select→arguments→execute→relevance `corresponds`) | **GROUNDED / OBSERVATION, verdict `answered`, presented=2 delivered=2** — `10080092 TERM. BALA 0,50-2,27MM2 ESTANHADO…` + `TERM. BALA 1,00-2,50MM2 NIQUELADO FITADO DIAM 4,80MM PLUGUE`; honest owner total ("a fonte informa 6 registros"); limitations [] |
| S2 | "Qual o último processo do Transforma+?" | ~26.9s | `teo.record_read` | **GROUNDED / OBSERVATION, verdict `empty_result`**, truthful "coleção vazia" — model sent `arg_keys=action,entity,page_size,q`; owner legitimately returned `total=0`; no fabrication, no invented latest |

Model calls: S1 ≈ 7 (vs historical ~14–15 FAIL); S2 = 4 (vs historical 5 FAIL). Tokens: provider usage not emitted at INFO log level — **not claimed**.

**E2 honest characterization:** the deployed walk fix closes the proven coverage/ordering divergence (regression-locked), but production exercised a different branch — the model again formulated a text-filter `q`, the owner authoritatively returned `total=0`, and no partial envelope existed to walk. The response is a truthful empty result (satisfies "never invent a latest process"), not a supported latest-process answer. The residual is model-owned argument formulation against the owner's actual `q` semantics — correctable only by instruction/semantic means, not by deterministic code without lexical heuristics (out of scope).

## 7. Verdict

`PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED` — E1 causally fixed end-to-end (owner description propagation → correct argument binding → two distinct authoritative records, `answered`). E2's proven contract divergence (requirements-gated page walk) is fixed, tested, and deployed; its production exercise produced a truthful limitation-grade outcome rather than the target answer, because the model-owned argument path still filtered instead of listing. Reported as such — no acceptance fabricated.

Residuals: E2 ordering intent via unfiltered listing + walk (reachable only when the model selects it); `answer_requirements` declaration completeness is model-owned; 2 pre-existing environmental test-mount failures.
