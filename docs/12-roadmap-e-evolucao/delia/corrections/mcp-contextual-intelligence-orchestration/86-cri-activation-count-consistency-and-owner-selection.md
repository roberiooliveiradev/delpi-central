# 86 — CRI activation, count consistency and semantic owner selection

**Task:** `DELIA-C3-CRI-ACTIVATION-COUNT-CONSISTENCY-AND-OWNER-SELECTION-01`
**Type:** bounded implementation + quality correction + real operational validation.
**Evaluated SHA:** worktree `e4a6da97f0` == `origin/main` at reanchor; runtime byte-equivalent (live-mounted primary checkout verified via `git diff` on all changed paths). Published SHA recorded in §8.

## 1. ETAPA A — CRI persistent activation (no new flag)

`DELIA_RESPONSE_INTELLIGENCE_ENABLED` is declared in `infra/.env`, projected through `docker-compose.dev.yml`, resolved once in `root_composer`, and injected as a typed boolean — the existing mechanism, unchanged.

Runtime evidence (two independent restarts this task):

```text
delia_response_intelligence requested=cri effective=cri
    config_source=environment runtime_sha=34a75d12a7ffcee3e4c7058969fa84fdd586e20a
cri_instruction_resource id=delia.cri.answer_requirements_instruction version=2
cri_presentation_resource id=delia.cri.presentation_vocabulary version=3
```

- Service `healthy` after `docker restart`; CRI `requested=cri effective=cri` after recreation.
- Live CRI responses observed post-restart (contract_facts, composed records answers).
- `PRODUCTION_ACTIVATION=NOT_AUTHORIZED` — no production flag or service touched.

`CRI_REQUESTED=cri`, `CRI_EFFECTIVE=cri`, `CRI_PERSISTENCE_VERIFIED=YES (restart ×2, env-sourced, rollback = env flag OFF)`.

## 2. ETAPA B — count consistency ("Encontrei 40 … de 32")

**Reproduction.** Live TÉO `record_read` "Liste os processos cadastrados" returned `Encontrei 40 registros` followed by `Exibindo 5 de 32 registros retornados` — the contradiction flagged in the independent review of doc 85.

**Root cause (one typed source per statement was violated):**

- The lead `records_found` binds `count = delivered_count` = `distinct_delivered_count(facts.records)` — exact-content dedup over the **full** owner result (40).
- The truncation notice bound `returned = len(records)` where `records` is the `prepared` projection capped at `OperationalCapabilityOrchestrator._CRI_RECORD_SCAN = 32` — an internal presentation scan bound leaking into a user-facing count claim.
- Trigger `presented < len(records)` had the same defect: two identical records (`prepared=[A,A]`, delivered=1) produced `Exibindo 1 de 2`.

**Minimal fix** (`compose_cri_response`, `conversational_response.py` — canonical presentation owner):

```text
"returned": len(records)  →  delivered_count
if presented < len(records) → if presented < delivered_count
```

`delivered_count` is the same canonical figure already consumed by the lead and by insufficiency templates (`{delivered}`), so every count statement now shares one typed source. `total_count` (owner-declared source total) remains a distinct attributed notice (`available_notice`) — never mixed with delivered/presented. `paginated_result_semantics.py` is untouched: it produces the upstream `total_count`/`coverage_complete` facts; this fix is at the consumption edge, not a second counting mechanism.

**RED→GREEN.** Three new tests in `test_cri_e3_conversational_presentation.py`:

- `test_count_scan_cap_never_leaks_into_returned_claim` — composer-level T5 reproduction (32 prepared, delivered 40).
- `test_count_duplicate_tail_never_claims_extra_returned` — duplicate collapse emits no phantom truncation.
- `test_on_scan_capped_projection_keeps_single_count_frame` — end-to-end orchestrator path with 40 owner records.

All three failed before the fix (exactly reproducing `5 de 32`), all pass after. Existing E2/E3 count tests (`5 de 7`, `5 de 8`, coverage/total notices) unchanged and green.

**Live verification (post-fix, real MCP + real model):**

```text
Encontrei 40 registros:
- …(5 record lines)…
Exibindo 5 de 40 registros retornados.
limitations: [result_truncated]   grounding_status: GROUNDED
```

## 3. ETAPA C — semantic owner selection (defect NOT reproduced)

**Flagged case.** Doc 85's V4 question was `catálogo de operações` — a *generic* question naming no owner — routed to `mcp:davi / discover_delpi_information`. The independent review asked whether that counts as correct owner selection.

**Investigation.** Stage-1 group selection is model-driven over `_group_summaries` (bounded per-group JSON: `capability_group_id`, `owner`, `display_name`, `source_system`, capability ids/names/classes/descriptions); stage-2 picks a capability inside the chosen group. No keyword routing, no provider-specific branches. DAVI's published contract advertises DELPI-wide action discovery (`eligible_action_count: 95`) — for an owner-less "what operations are available" question it is the semantically matching surface.

**Live probe battery (unseen questions, real model + real MCPs):**

| Question | Expected | Selected |
|---|---|---|
| "Quais operações a VISTA disponibiliza?" | vista | `vista get_catalog` GROUNDED |
| "Quais operações posso usar para gerenciar playlists e blocos de tela?" | vista | `vista get_catalog` GROUNDED |
| "Quais formatos de visualização a VISTA suporta?" | vista | `vista get_catalog` GROUNDED |
| "Que modelos de dados a VISTA oferece?" | vista | `vista get_catalog` GROUNDED |
| "O que posso consultar no Transformômetro?" | teo | `teo get_catalog` GROUNDED |
| "Quais metodologias e revisões existem no Transformômetro?" | teo | `teo get_catalog` GROUNDED |
| "Quais indicadores operacionais e dados de compras…?" | davi | `davi discover_delpi_information` GROUNDED |
| "Que informações sobre estoque e produção…?" | davi | `davi discover_delpi_information` — owner correct; turn hit the ~30s budget inside the candidate chain (`interaction_admission` timeout → honest NON_GROUNDED) |
| "Mostre o catálogo de operações disponíveis" (V4 reproduction) | ambiguous | `davi discover_delpi_information` GROUNDED contract_facts |

**Verdict.** Named-owner and domain-specific questions select the right group in 8/8 probes (VISTA×4, TÉO×2, DAVI×2). The flagged V4 was a genuinely ambiguous question resolved to the group whose published capability is DELPI-wide discovery — a defensible semantic match, not a routing defect, and the response is grounded + attributed contract facts, never fabricated VISTA facts. Per the task's own rule ("se a seleção estiver correta diante do contexto real, registrar e não modificar código"): **no code change**.

`OWNER_SELECTION_DRIFT_REPRODUCED=NO`, `SEMANTIC_CONTEXT_AVAILABLE=YES`, `OWNER_SELECTION_FIX=NO_CODE_CHANGE`, `WRONG_OWNER_NEGATIVE_TESTS=PASS(0/8 wrong-owner selections)`.

## 4. Regression evidence

```text
tests/test_cri_e3_conversational_presentation.py   64 PASS (3 new)
tests/test_c3_contextual_discovery.py              16 PASS
tests/test_cri_e2_outcome_assessment.py            PASS
tests/test_cri_e1_response_intelligence_toggle.py  PASS
tests/test_stage03_discovery_guidance.py           PASS
tests/test_r4_r5_personal_ticket_count_and_pagination.py  PASS
tests/test_r45_pagination_integrity_rework.py      PASS
```

Focused + related suites: ~200 tests green in-container. Broader suite subsets previously verified on this codebase; no claim of full-backend coverage (`test_presentation_v2_proposal` has a pre-existing missing-`/docs` environment exclusion, unrelated to this diff).

## 5. OFF/ON deltas

- The count fix lives inside `compose_cri_response`, invoked only from `_compose_cri_response` when `cri_present_active` — OFF cannot reach it by construction; OFF-harness tests (orchestrator built without CRI flag) all pass.
- `ON_ENGAGEMENT=PASS` — composed counts verified live.
- `MODEL_CALL_DELTA=0`, `MCP_CALL_DELTA=0`, `LATENCY_DELTA≈0` (no new stages; same single-pass composition).

## 6. Residual search

- `agent_directives` still surfaces as bounded data rows in DAVI contract-facts digests (descriptive, never executed — known residual from doc 85).
- Environmental model timeouts (~30s turn budget) still occur on DAVI discovery + candidate chains — honest NON_GROUNDED, not a code regression.
- Proactive `filterable_fields` channel and field→event semantics remain owner/architecture dependencies (docs 83/85), unchanged.

## 7. Files changed

```text
delia-api/app/application/capability_provision/conversational_response.py  (2-line fix + comment)
delia-api/tests/test_cri_e3_conversational_presentation.py                (3 new tests)
docs/.../86-cri-activation-count-consistency-and-owner-selection.md       (this report)
docs/.../mcp-contextual-intelligence-orchestration/README.md              (index entry)
docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md             (entry)
```

## 8. Outcome

```text
TASK_ID=DELIA-C3-CRI-ACTIVATION-COUNT-CONSISTENCY-AND-OWNER-SELECTION-01
CRI_PERSISTENCE=VERIFIED(env-sourced, restart-surviving, no new flag)
COUNT_FIX=CANONICAL_FRAME(delivered_count single source)
OWNER_SELECTION=VERIFIED_HEALTHY(8/8 correct, generic→DELPI-wide discovery defensible)
NEW_MODEL_STAGES=0  NEW_REGISTRIES=0  PROVIDER_BRANCHES=0
UNIT_TESTS=PASS(64 E3 + focused suites)
REAL_EVAL=PASS(T5 counts live, 9 selection probes)
OFF_PARITY=PASS(by construction, composition is CRI-gated)
PRODUCTION_ACTIVATION=NOT_AUTHORIZED
I04_ACCEPTED=NO
C3_EXECUTED=YES
NEXT=COORDINATION_REVIEW
```

## 9. Independent coordination review — 2026-10-22

**Verdict: ACCEPT_WITH_RESIDUAL.** Inspected published implementation `a45b376327` and report 86 using connected GitHub; main was already at `ba8005d6032d0f8442fffec6813bd42907c3b29f` when review began, with other concurrent work. Independent runtime re-execution: `TEST_NOT_RUN`; the 2 restart checks, RED/GREEN tests, real TEO response and selection probes remain executor-reported evidence.

**Count correction accepted:** composer `params[returned]` now binds to `delivered_count` and truncation is emitted only when `presented < delivered_count`. This removes the `_CRI_RECORD_SCAN=32` display-cap leakage identified in T5, without altering the owner-provided `total_count` or upstream pagination contracts. The reported RED tests and live `5 de 40` response support the intended business presentation outcome. Note that `delivered_count` means distinct delivered records, not necessarily raw API rows; maintain that distinction in future vocabulary/contract tests.

**Owner selection:** no mandatory code correction is justified for the originally flagged generic `catalogo de operacoes` query. Its lack of specific owner permits a DELPI-wide DAVI discovery interpretation. The executor's 8 domain-specific probes indicate correct group selection; one DAVI probe did not complete within budget, so `OWNER_SELECTION=EXECUTOR_VERIFIED` but `BUSINESS_TASK_OUTCOME=PARTIAL`, not universal success. Preserve LLM-led selection and existing group context; no keyword routing or provider-specific branch.

**CRI activation:** executor reports ON requested/effective after two dev restarts, config in existing env/compose and resources instructions v2/presentation v3. This review cannot independently verify local `.env` or the running container: `CRI_DEV_PERSISTENCE=EXECUTOR_VERIFIED`; `INDEPENDENT_RUNTIME_CHECK=TEST_NOT_RUN`. The log's historical runtime_sha value must not substitute for byte-equivalence verification of changed mounted files; executor reports this separately. Production activation remains unauthorized.

**Remaining separate dependencies:** DAVI candidate-chain model-timeout under 30s budget (actual task completion residual); bounded agent_directives presentation as metadata; owner contract for field-to-event meaning and global sorting/coverage; proactive filter admissibility if evidence later warrants it. None justify reopening this count fix or implementing a new planner/registry.

`REVIEW=ACCEPT_WITH_RESIDUAL`; `COUNT_FIX=STATIC_VERIFIED_PLUS_EXECUTOR_LIVE_PASS`; `OWNER_SELECTION_DRIFT=NOT_REPRODUCED_IN_REPORTED_CASES`; `CRI_DEV_ON=EXECUTOR_VERIFIED`; `INDEPENDENT_RUNTIME_TEST=TEST_NOT_RUN`; `I04_ACCEPTED=NO`; `C3_EXECUTED=YES_EXECUTOR_REPORTED`; `PRODUCTION_ACTIVATION=NOT_AUTHORIZED`.
