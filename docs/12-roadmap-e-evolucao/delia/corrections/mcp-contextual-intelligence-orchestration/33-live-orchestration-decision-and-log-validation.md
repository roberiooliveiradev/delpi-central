# 33 — Live orchestration decision and log validation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-LIVE-ORCHESTRATION-DECISION-AND-LOG-VALIDATION-01`  
**MODE:** diagnostic + controlled live reproduction (no speculative functional patch)  
**REFERENCE_HEAD (task brief):** `a4354d101c85bd6e1375ad2a969bf419d0fc9106` — **superseded**  
**SOURCE_SHA / DEPLOYED_SHA:** `9a8775018f31111ce59b11945efec962e0db73d4`  
**AUTHORITIES:** README track; docs 21–30; ledger §§6.269–6.271; protocol 16→50→…→ledger  
**I03_ACCEPTED:** `YES_WITH_RESIDUAL` (ledger §6.273 / doc 32 — **not** reopened by this task)  
**C3_EXECUTED:** `NO`  
**VERDICT:** `EVIDENCE_RECORDED / REMEDIATION_NOT_IMPLEMENTED`

## 0. Execution drift during this task

```text
TASK_REFERENCE_HEAD=a4354d101c85bd6e1375ad2a969bf419d0fc9106
EVAL_RUNTIME_SHA=9a8775018f31111ce59b11945efec962e0db73d4
DOCS_HEAD_AT_CLOSE=2b00c576b940c3dc13b1aeb3396a38e13fd343e5
I03_LEDGER_STATE_AT_CLOSE=YES_WITH_RESIDUAL (§6.273 / doc 32 independent acceptance)
THIS_DOC_NUMBER=33 (doc 32 already used by I03 independent acceptance)
I04_STARTED_BY_THIS_TASK=NO
FUNCTIONAL_PATCH_BY_THIS_TASK=NO
```

Live results below remain bound to **runtime SHA `9a8775018f`**. Concurrent docs advanced I03 acceptance and pointed NEXT at I04; this diagnostic does **not** implement I04 and does **not** reopen I03 acceptance.

## 1. Reanchor

```text
LOCAL_HEAD=9a8775018f31111ce59b11945efec962e0db73d4
ORIGIN_MAIN=9a8775018f31111ce59b11945efec962e0db73d4
HOST_GIT_HEAD(srv-api)=9a8775018f31111ce59b11945efec962e0db73d4
BRANCH=main
WORKING_TREE_UNRELATED=plugins/plugin-ui/docs/... (untracked; preserved)
```

Frozen decisions preserved: no I04/Q01; I03 global acceptance still blocked by coordination; helpdesk personal-count remains a related bounded defect (§6.271), not a silent replacement of the K2/K3 gate.

## 2. Runtime gate

| Field | Value |
|---|---|
| TARGET | `operador@192.168.1.237` (`srv-api`) |
| CONTAINER | `delpi-delia-api` healthy `{"service":"delia-api","status":"available"}` |
| DEPLOYED_IMAGE | `infra-delia-api` (compose rebuild ~2026-10-19T13:00Z) |
| MODEL_PROVIDER | `openai_compatible` |
| MODEL_ID | `moonshotai/kimi-k3` |
| MODEL_VERSION | not separately versioned in env |
| CONFIG_FINGERPRINT | `021ed91f68665f62` (sha256-16 of model/provider/budget/stage/teo/vista/davi flags) |
| TURN_BUDGET_SECONDS | **30** |
| MODEL_STAGE_TIMEOUT_SECONDS | **30** |
| MCP_TEO_AVAILABLE | `true` |
| MCP_VISTA_AVAILABLE | `true` |
| MCP_DAVI_AVAILABLE | `true` |
| R3-B typed capability+goal | **YES** (`_select_capability_with_goal` + instruction present) |
| Adaptive routing / I02 K2·K3 | **YES** (`_recover_prior_extraction_after_invalid_index`, `budget_skip`) |
| I03 discovery terminal | **YES** (`CAPABILITY_NOT_MATCHED` + `eligible_action_count`) |
| AUTH | password-grant Portal subject via Keycloak (credentials not recorded) |
| CORE_AUTHZ | exercised (`/interaction/turns` authenticated) |
| DOMAIN_AUTHORITY | exercised via owner MCP READ paths |
| DEPLOY_PERFORMED | **NO** (image already on SOURCE SHA) |

## 3. Live matrix (n=1 each; no opportunistic retries)

Marker prefix on inputs: `[LIVEORCH01:L0x]` for log correlation. Correlation IDs from orchestration logs / provenance.

### L01 — “Quantos chamados tem para mim?”

| Field | Value |
|---|---|
| correlation_id | `41214722-9fc0-4cc8-9158-4799ec933d1a` |
| HTTP / ms | 200 / **14900** |
| decision_path | OPERATIONAL |
| select_group | `mcp:teo` |
| select_capability | **`helpdesk_read`** (READ) |
| goal_class | `read` typed_with_capability |
| plan | direct (no discovery envelope) |
| arguments | built; `arg_keys=action` |
| owner_read | **error** `teo.helpdesk_read` → `glpi_link_required` (409) |
| grounding | NON_GROUNDED |
| presentation | `PRECONDITION_REQUIRED` |
| content (sanitized) | source-unverified + owner message `Helpdesk BFF error: glpi_link_required.` |
| material ACT | 0 |

```text
L01_INTENT=personal_ticket_count (helpdesk-like) — PASS routing class
L01_SELECTED_OWNER=mcp:teo
L01_CAPABILITY=helpdesk_read
L01_PERSONAL_SCOPE=INCONCLUSIVE (blocked before ticket payload; arg_keys=action only)
L01_PAGINATION=NOT_REACHED
L01_AUTHORITATIVE_TOTAL=NOT_REACHED
L01_FINAL_ANSWER=honest precondition / source unverified (not page-length-as-total)
L01_OUTCOME=FAIL_TASK (no personal count) / PASS_ROUTING_VS_HISTORICAL_MISROUTE
L01_ROOT_CAUSE=SOURCE_UNAVAILABLE (owner precondition glpi_link_required)
L01_SECONDARY=PERSONAL_SCOPE_FAILURE / PAGINATION_COUNT_FAILURE = NOT_REPRODUCED_ON_THIS_SHA
```

**Historical screenshot (doc 30):** TÉO + 10 Transformômetro records as “count” — **NOT REPRODUCED** on `9a8775018f`. Current runtime selects Helpdesk capability correctly; failure is GLPI link precondition for the eval subject.

### L02 — “5 exemplos de terminal bandeira”

| Field | Value |
|---|---|
| correlation_id | `11b3bdcd-0e22-41df-93d4-1b672674a6d7` |
| HTTP / ms | **504** / **30014** |
| select_group | **`decision=none` groups=4** |
| target_selection | none |
| owner_read | NOT INVOKED |
| error | `model_timeout` (~23s after group-none until global budget) |
| ATIVIDADE_BLOQUEADA / FONTE_INDISPONIVEL | **NOT REPRODUCED** |

```text
L02_INTENT_CLASS=ambiguous (product-term examples vs conceptual)
L02_DOMAIN=DELPI product vocabulary (TERM. BANDEIRA / terminal bandeira — normative lexicon)
L02_SELECTED_OWNER=NONE
L02_SELECTED_CAPABILITY=NONE
L02_SOURCE_REQUIREMENT=unresolved (no owner consulted)
L02_ERROR_OR_BLOCK_STAGE=GROUP_SELECTION → budget burn → HTTP 504
L02_BLOCK_REASON=select_group=none then model_timeout (not explicit FONTE_INDISPONIVEL)
L02_EXPECTED_BEHAVIOR=clarification or grounded product/discovery path; not silent 504
L02_OUTCOME=FAIL
L02_ROOT_CAUSE=GROUP_ROUTING_FAILURE (+ BUDGET_EXHAUSTION secondary)
```

### L03 — TÉO methodology (K1)

| Field | Value |
|---|---|
| correlation_id | `4e061b4a-b632-4fa4-8b87-0bc4645953f3` |
| HTTP / ms | 200 / **22313** |
| specialist | `teo` / `get_methodology_guide` |
| discovery | `get_catalog` ok (80ms) |
| typed merge | YES (`typed_with_capability`; no separate cold-start `turn_goal`) |
| grounding | GROUNDED |
| limitations | `result_truncated` |
| material ACT | 0 |

**L03_RESULT:** `PASS_WITH_LIMITATION` (≤30s; methodology READ reached). Baseline ~17s (doc 24) — single sample, no statistical regression claim.

### L04 — K2 continuity (same prior evidence via `context`)

| Field | Value |
|---|---|
| correlation_id | `53ed4e86-c9f4-4f68-8178-aaa1437ff269` |
| HTTP / ms | 200 / **17341** |
| prior_sufficient | yes |
| prior_continuation | `recover_invalid_index` → `transformed` excerpts=12 |
| owner reinvoke | **NO** |
| grounding | NON_GROUNDED (`prior_turn_evidence_only`) |
| content_chars | 409 |
| framing defect | user-facing “Encontrei 7 registros:” for methodology checklist extraction |

**L04_RESULT:** `PASS_WITH_LIMITATION` (continuity wiring + recover path PROVEN). Residual: `RESPONSE_PROJECTION_FAILURE` (record-list framing).

### L05 — VISTA legibility (K3)

| Field | Value |
|---|---|
| correlation_id | `44d68700-2d71-4c19-9599-033f9988f18c` |
| HTTP / ms | 200 / **23308** |
| specialist | `vista` / `get_product_guide` |
| index_probe | ok identifiers=11 |
| index_select | `reject_weak_relevance` topic=`block_types` (not forced `display_formats`) |
| nested guidance | NOT_REACHED |
| clarification | YES (legibility / visualization theme) |
| material ACT | 0 |

**L05_RESULT:** `PASS` safe no-match clarification. Class: `OWNER_CATALOG_GAP` consistent with docs 24–26 — **not** `ORCHESTRATOR_SELECTION_FAILURE`. Budget residual from prior I03 sample (**30013ms**) **not** reproduced on this SHA/sample.

### L06 — DAVI discovery (K4)

| Field | Value |
|---|---|
| correlation_id | `ac7663c8-24ad-4dc3-b425-6e1a46ed7d84` |
| HTTP / ms | **504** / **30011** |
| select_capability | **`decision=none` group=`mcp:davi`** |
| target_selection | none |
| owner_read | NOT INVOKED |
| error | `model_timeout` |

**L06_RESULT:** `FAIL` (regression vs doc 28 live K4 PASS on earlier SHA). Direct owner still healthy (below).

## 4. Direct MCP / owner comparison (READ-only)

Subject = same Portal user as live turns. Delegated exchange audiences: `mcp-transformometro` / `mcp-tv-dashboard` / `mcp-api-delpi`. No tokens/`authorize_url` persisted.

| Surface | OWNER_DIRECT_RESULT | DELIA_ORCHESTRATED_RESULT | Notes |
|---|---|---|---|
| Helpdesk HTTP `/tickets` | 409 `glpi_link_required` | — | confirms precondition |
| TEO `helpdesk_read(session)` | success; session schema present | L01 selected same tool | linked semantics in payload; tickets still blocked |
| TEO `helpdesk_read(capabilities\|tickets)` | `glpi_link_required` | L01 same error projected | **parity** with orchestrated failure |
| VISTA `get_product_guide{}` | index success (~2.7k chars) | L05 INDEX→weak reject→clarify | owner catalog available |
| DAVI `discover_delpi_information` | `candidate_count=0`, `eligible_action_count=95` | L06 never reached READ | owner OK; orchestrator failed capability selection |

```text
OWNER_DIRECT ≠ DELIA_USER_FACING automatically:
- AuthZ/delegation, argument projection, budgets, and synthesis differ.
- L06 proves owner can answer while orchestrator times out pre-READ.
```

## 5. Decision-path reconstruction (first divergence)

| Case | Path | First divergence |
|---|---|---|
| L01 | INTENT→GROUP teo→CAP helpdesk_read→ARGS→READ error | READ / provider precondition (`glpi_link_required`) |
| L02 | INTENT→**GROUP none**→(budget)→504 | GROUP_SELECTION |
| L03 | …→teo methodology→DISCOVERY→READ→synth | none material |
| L04 | turn_goal prior_sufficient→recover_invalid_index→transform | projection framing (“registros”) |
| L05 | vista guide→INDEX→reject_weak→clarify | none (honest no-match) |
| L06 | GROUP davi→**CAP none**→504 | CAPABILITY_SELECTION |

## 6. Evaluation matrix

| Critério | L01 | L02 | L03 | L04 | L05 | L06 |
|---|---|---|---|---|---|---|
| Intenção correta | PASS | FAIL | PASS | PASS | PASS | INCONCLUSIVE |
| Fonte adequada | PASS (selected) | FAIL | PASS | N/A prior | PASS | FAIL (not reached) |
| Capability adequada | PASS | FAIL | PASS | N/A | PASS | FAIL |
| Parâmetros corretos | INCONCLUSIVE | N/A | PASS | N/A | PASS | N/A |
| Evidência suficiente | FAIL | FAIL | PASS | PASS_WITH_LIMITATION | PASS (clarify) | FAIL |
| Grounding | PASS (honest nongrounded) | FAIL | PASS | PASS_WITH_LIMITATION | PASS | FAIL |
| Resposta ao pedido | FAIL | FAIL | PASS_WITH_LIMITATION | PASS_WITH_LIMITATION | PASS | FAIL |
| Orçamento 30s | PASS | FAIL | PASS | PASS | PASS | FAIL |
| Segurança | PASS | PASS | PASS | PASS | PASS | PASS |
| Outcome final | FAIL_TASK | FAIL | PASS_WITH_LIMITATION | PASS_WITH_LIMITATION | PASS | FAIL |

`MATERIAL_ACT_COUNT=0` across all cases.

## 7. Proven / discarded / inconclusive causes

### PROVEN

1. **L01 routing class fixed vs doc 30 screenshot** on SHA `9a8775018f`: selects `helpdesk_read`, not Transformômetro list-as-count.  
2. **L01 task failure** = owner `glpi_link_required` for eval subject (direct MCP + Helpdesk HTTP + DELIA agree).  
3. **L02** = `select_group=none` then global `model_timeout` (not FONTE_INDISPONIVEL message path).  
4. **L04** = I03 K2 recover path live-exercised (`recover_invalid_index`).  
5. **L05** = weak topic reject + clarification under 30s on this sample.  
6. **L06** = capability selection none on DAVI group despite healthy owner discovery contract (`eligible=95`).

### DISCARDED (this SHA/sample)

- L01 Transformômetro misroute as current cause of “10 chamados”.  
- L02 `ATIVIDADE_BLOQUEADA/FONTE_INDISPONIVEL` as current block signature.  
- L05 forced `display_formats` nested READ.  
- Unauthorized ACT / AuthZ bypass.

### INCONCLUSIVE

- Authoritative personal ticket total / assigned-vs-requester semantics (blocked by GLPI link).  
- Whether PAGE_SIZE was ever projected as TOTAL on this SHA (not reached).  
- Statistical latency vs ~17s K1 baseline (n=1).  
- Exact model payload that yielded `select_group=none` / `select_capability=none` (not instrumented beyond stage logs).

## 8. Recommended minimal diffs (coordination gate — not applied)

| ID | Proof | Minimal safe change | Forbidden |
|---|---|---|---|
| R1 | L02/L06 | After `select_group`/`select_capability` none: deterministic clarification / fail-closed with remaining budget — do not burn to bare 504 | new planner; specialist hardcode |
| R2 | L06 vs direct DAVI | Investigate typed capability proposal miss for discovery intents; keep provider-neutral | DAVI-only branch |
| R3 | L04 framing | Prior-extraction projection must not use “registros” envelope for guidance/checklist | invent facts |
| R4 | L01 | Keep honest `glpi_link_required` UX; separate task for personal count **only** with linked subject + pagination/total contract | fabricate totals; JWT identity guessing |
| R5 | L01 related (§6.271) | Bounded RED: page_len ≠ total; unknown total honest | raise global 30s |

**ARCHITECTURE_DECISION_REQUIRED:** only if R2 needs contract change beyond existing typed selection / discovery terminal.

## 9. Backend tests executed

Inside `delpi-delia-api` image matching SOURCE SHA:

```text
test_i01_contextual_knowledge_continuity.py
test_i02_k2_k3_output_quality.py
test_i02r3b_typed_capability_goal_selection.py
test_adaptive_capability_routing_completion.py
test_i03_k2_k3_nonregression.py
test_i03_semantic_capability_discovery.py
test_specialist_interop_security.py
→ PASS (full listed modules)
FULL_SUITE=TEST_NOT_RUN (bounded modules only)
```

## 10. Security / residuals

```text
MESSAGE_ONLY=YES
MATERIAL_UNAUTHORIZED_ACT=0
NO secrets/JWT/PII in this document
NO authorize_url persisted
NO deploy / production mutation beyond read-only probes and authenticated MESSAGE turns
```

Residuals: GLPI link for eval user; L02/L06 timeout-on-none-selection; L04 projection wording; I03 global acceptance still NO; I04/Q01 not opened.

## 11. Answers to coordination questions

1. **Why Transformômetro for chamados?** On this SHA: **it did not**. Historical screenshot remains `TO_INVENTORY` for older runtime; current selects `helpdesk_read`.  
2. **Why “10” as count?** **NOT REPRODUCED**. Blocked by `glpi_link_required` before any page payload. Doc 30 pagination caveat still stands for when tickets become reachable.  
3. **Why block terminal bandeira?** Group selection returned none → budget exhausted → HTTP 504. Not the prior FONTE_INDISPONIVEL signature.  
4. **Wrong stages?** L01 READ precondition; L02 group; L04 projection; L06 capability.  
5. **Did sources have the data?** Helpdesk tickets: unavailable without GLPI link. VISTA index: yes. DAVI discovery envelope: yes (`eligible=95`). Methodology: yes.  
6. **Model vs orchestrator vs contract vs provider?** L01 provider precondition; L02/L06 model selection + orchestrator lack of fail-closed short-circuit; L04 projection; L05 catalog gap (known).  
7. **Smallest safe corrections?** R1–R5 above — coordination review before functional merge.

```text
I03_ACCEPTED=YES_WITH_RESIDUAL
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT_MAIN=I04_PROVIDER_NEUTRAL_GENERALIZATION
NEXT_RELATED=COORDINATION_ROOT_CAUSE_AND_REMEDIATION_REVIEW_DOC33
```
