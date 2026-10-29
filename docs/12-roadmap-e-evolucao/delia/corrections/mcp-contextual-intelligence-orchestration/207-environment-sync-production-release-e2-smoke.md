# 207 — Environment sync and production release with bounded E2 smoke

- **Task:** `DELIA-C3-ENVIRONMENT-SYNC-PRODUCTION-DEPLOY-AND-E2-SMOKE-01`
- **Reference HEAD:** `e9c405cee93fb941a2b203b506e4bfeb0d87d780`
- **Scope:** synchronize local and production runtimes to the validated release (Tasks 11–14), deploy only the drifted components, verify contracts at runtime, execute the bounded authenticated E2 smoke ("Qual o último processo do Transforma+?") plus one E1 regression turn.

## 1. Reanchor

- Local `HEAD = e9c405cee9 = origin/main`, branch `main`, uncommitted concurrent entries (stock/finance + artifacts — preserved, none staged).
- Worktrees: 30+ — none touched.
- Production repo `/home/operador/projetos/delpi-central`: was `6172f5731a` (2 commits behind — docs 42 + Task 14 `e9c405ce`), clean tree → `git pull --ff-only` to `e9c405cee9`.

## 2. Runtime inventory

### Local (WSL dev)

| Service | State | Mount/artifact | Drift |
|---|---|---|---|
| delia-api | Up (healthy) | bind-mounted `/delia-api` → v26 + `_declared_requirements_projection` live | none |
| transformometro-api | restarted | bind-mounted — server.py change post-dated container start → `docker restart` applied | resolved |
| api-delpi | Up (healthy) | no committed changes since `43650dd` (Task 13) | none |
| delia (MFE), portal, plugin-ui | Up | no committed changes `6172f57..HEAD` under `plugins/` | none |

Local contract verification (in-container): TÉO `record_read` publishes per-param descriptions (`q` = free-text over record fields; `page` documents owner implicit newest-first ordering). delia-api loader accepts v26 (fail-closed gate satisfied; service healthy).

### Production (srv-api, before deploy)

| Service | Image (before) | Code state | Drift |
|---|---|---|---|
| transformometro-api | `c2d3462af6d1` | `Annotated` count 0 — pre-Task-14 | **rebuild required** |
| delia-api | `dad53fa242f6` (Task 13) | instructions v25 | **rebuild required** |
| api-delpi | Task 13 image (healthy) | no committed drift | preserved |
| delia frontend / portal / plugin-ui | 4d / 12h / 17h | no committed drift under `plugins/` | preserved |

## 3. Deploy (official runbook, owner→consumer order)

```
SERVICE=transformometro-api
PREVIOUS_IMAGE=c2d3462af6d1
TARGET_COMMIT=e9c405cee9
DEPLOYED_IMAGE=8c470afe48dd
CONFIG_FINGERPRINT=bind-mounted repo at e9c405ce (compose unchanged)
HEALTH=Up; published inputSchema carries all param descriptions
ROLLBACK_REFERENCE=infra-transformometro-api:semantic-arg-rollback-c2d3462a

SERVICE=delia-api
PREVIOUS_IMAGE=dad53fa242f6
TARGET_COMMIT=e9c405cee9
DEPLOYED_IMAGE=c87dc40a7bb1
CONFIG_FINGERPRINT=DELIA_ORCHESTRATION_ENGINE=langgraph;
  DELIA_RESPONSE_INTELLIGENCE_ENABLED=true; instructions v26
HEALTH=Up (healthy); boot log selected=langgraph, effective=cri
ROLLBACK_REFERENCE=infra-delia-api:semantic-arg-rollback-dad53fa2
```

`up-prod-sequential.sh --build transformometro-api` then `--build delia-api`. ~90 other containers untouched; no migrations; api-delpi/delia/portal/plugin-ui preserved (no drift).

## 4. Post-deploy runtime verification

- delia-api boot: `delia_orchestration_engine selected=langgraph`, `delia_response_intelligence requested=cri effective=cri`, `cri_instruction_resource` loaded, `env=production`.
- Instructions: `version=26` inside container; fail-closed loader accepted (service healthy).
- `_declared_requirements_projection` present in deployed `orchestration.py`.
- TÉO `record_read` inputSchema (in-container): `q` = free-text over record fields; `page`/`page_size` pagination; implicit newest-first ordering documented.
- Frontend: `delpi-delia` image preserved (no plugin diff); portal `200`, `/apps/delia/` `200`, `/apps/delia-api/health` `200`; gateway healthy.
- Rollback tags for both prior images retained.

## 5. Bounded authenticated E2 smoke

- Identity: `user` (portal password grant, client `delpi-central`, scope `openid profile email`) — same sanctioned identity as doc 205.
- Budget: exactly 1 E2 turn + 1 E1 turn, single attempt each, no retries, no budget changes, no new instrumentation.

### E2 — "Qual o último processo do Transforma+?" — **ANSWERED (GROUNDED)**

```
CORRELATION_ID=task15-e2-483166f3 (orchestration 62e036bf-4458-4ec5-9cd2-2d45ce264155)
RUNTIME_SHA=e9c405cee9  ACTIVE_ENGINE=langgraph  INSTRUCTION_VERSION=26
GOAL_CLASS=read  ADMISSION=owner_surface (operational)
OWNER_SELECTED=mcp:teo  CAPABILITY_SELECTED=record_read
ARGUMENT_KEYS=action,entity,page_size   Q_FILTER_PRESENT=NO
PAGINATION_USED=page_size arg; owner implicit newest-first ordering
OWNER_TOTAL=76  EVIDENCE_PRESENTED=1 (presented=1 delivered=1)
RELEVANCE=corresponds  CRI=composed  OUTCOME_ASSESSMENT=answered
GROUNDING=GROUNDED  EPISTEMIC=OBSERVATION  LIMITATIONS=none
RESPONSE=PROC-0073 "Acompanhamento de Produtos Novos na Produção"
  (+ description, gestor field, provenance "76 registros no total")
MODEL_CALLS=6 (admission, select_group, select_capability+goal,
  native_assessment, arguments, evidence_relevance)
STAGE_TIMINGS_MS=3408/4813/4222/3996/127(owner)/10122
TOTAL_LATENCY≈29.3s   MODEL_TOKENS=not reported by endpoint
```

**Business outcome:** the E2 defect class is closed end-to-end under the production model — no invented `q`, unfiltered listing with declared intent, owner ordering evidence, real latest record presented with provenance. Compare doc 205 smoke: `arg_keys=...,q` → `total=0` → truthful empty. Same goal, same owner, opposite argument formulation — consistent with the Task 14 deterministic surfaces taking effect under a compliant model.

### E1 regression — "Me dê dois exemplos de terminal bala" — **truthful empty (divergence)**

```
CORRELATION_ID=task15-e1-7170c804 (orchestration abe4fee7-3695-42d2-961e-3c27a89ef9c6)
ADMISSION=owner_surface (ambiguous)  OWNER=mcp:davi
PATH=discover_delpi_information(query) → select_candidate →
  execute_delpi_information(arguments,candidate_token)
SELECTED_CANDIDATE=governed knowledge read (topic=product_master_sb1)
OWNER_RESULT=excerpts=0  EVIDENCE_PRESENTED=0
OUTCOME_ASSESSMENT=empty_result  GROUNDING=GROUNDED
RESPONSE="A fonte respondeu com uma coleção vazia…"  TOTAL_LATENCY≈33.3s
```

**Honest classification:** `E1_REGRESSION=CANDIDATE_SELECTION_DIVERGENCE`. The governed chain executed correctly and failed closed — no fabrication, truthful empty. But business outcome regressed vs doc 205 smoke (2 real TERM. BALA records): the model-selected candidate was the governed knowledge topic instead of the product-search candidate. api-delpi was not redeployed (no drift); the divergence is model-owned candidate choice under v26 semantics, possibly interacting with the new listing-vs-content-search distinction applied to DAVI discovery candidates. Logged as residual — per task §12/§13 no lexical heuristic patch and no extra production calls were made.

## 6. Verdict

`PRODUCTION_DEPLOY_EXECUTED_AND_VERIFIED` — both drifted services rebuilt via official runbook, contracts verified at runtime (v26, langgraph, CRI, TÉO param descriptions), rollback tags retained, ~90 unrelated services untouched.

`E2_CLOSED_UNDER_PRODUCTION_MODEL` — ordering/listing intent now produces unfiltered listing + owner-ordered evidence + supported latest record (GROUNDED, answered).

`E1_RESIDUAL` — truthful empty via model-owned candidate-selection divergence; not a code failure; next bounded step: observe whether the divergence recurs and, if so, address at the instruction/candidate-surface level in a separate task — never by lexical branches.
