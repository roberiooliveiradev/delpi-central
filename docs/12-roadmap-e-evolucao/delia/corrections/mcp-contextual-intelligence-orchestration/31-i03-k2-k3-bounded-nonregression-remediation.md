# 31 — I03 · K2/K3 Bounded Non-Regression Validation and Remediation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I03-K2-K3-BOUNDED-NONREGRESSION-REMEDIATION-01`  
**BASE_HEAD:** `f3b113a869e00b072eb52c828f6a5293b0f0248f`  
**IMPLEMENTATION_SHA / DEPLOYED_SHA:** `9a8775018f31111ce59b11945efec962e0db73d4`  
**AUTHORITIES:** [24](./24-i02-k2-k3-output-quality-remediation-implementation.md)–[29](./29-i03-independent-davi-crosscheck-review.md), ledger §§6.269–6.271  
**EXISTING_EQUIVALENT:** `YES` — `_prior_continuation_attempt` / `_propose_index_identifier`  
**REUSE_DECISION:** `EXTEND`  
**I03_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Reprodução

### K2 — `invalid_record_index`

**REPRODUCED:** `YES` (synthetic RED)

```text
prior_evidence_sufficient=true
→ model proposes record_index fora de range
→ _render_synthesis → invalid_record_index
→ (antes) insufficient_evidence imediato
```

**ROOT_CAUSE:** `INVALID_MODEL_PROPOSAL` tratado como `INSUFFICIENT_PRIOR_EVIDENCE`, apagando excerpts legítimos. `_extraction_list_from_prior_excerpts` já existia, mas só após render bem-sucedido.

### K3 — `budget_exceeded` / `delpi_source_unverified`

**REPRODUCED:** `YES` (synthetic RED — `model_timeout` e `turn_budget_exhausted` em `index_select`)

```text
INDEX READ ok
→ _propose_index_identifier
→ residual < MIN_VIABLE ou model_timeout
→ _StageDeadlineExceeded → SOURCE_UNAVAILABLE
```

**ROOT_CAUSE:** estágio de `index_select` após INDEX bem-sucedido colapsava o turno, embora `_clarification_question` já tivesse fallback determinístico.

Não atribuído ao DISCOVERY terminal I03 (caminho K4 separado).

## 2. Correção mínima

| Área | Mudança |
|---|---|
| K2 | `_recover_prior_extraction_after_invalid_index` + `recover_invalid_index` |
| K3 | `_propose_index_identifier` captura `_StageDeadlineExceeded` → `budget_skip` → clarificação |

Preservado: GLOBAL 30s; stage-cap 10 OFF; args-headroom OFF; classes K4 discovery; MESSAGE≠ACT; sem branch por especialista.

## 3. Testes

`tests/test_i03_k2_k3_nonregression.py` + I01/I02/I03/R2/R3/ACR + full `delia-api` pytest **PASS**.

## 4. Live evaluation (MESSAGE-only, n=1, sem retries)

| Field | Value |
|---|---|
| TARGET | `srv-api` `delpi-delia-api` |
| MARKERS | `recover_invalid_index` + `budget_skip` in image |
| MODEL | `moonshotai/kimi-k3` / `openai_compatible` |
| BUDGET / STAGE | **30** / **30** |

### K1 — TÉO (sha256-8 `2a8147e1`)

**Correlation:** `94574096-4daa-4032-bce4-c21ce58b681f` (batch) / smoke `d9c0c29b-…`

```text
HTTP=200 TOTAL_MS=16943 SPECIALIST=teo CAPABILITY=get_methodology_guide
TYPED_WITH_CAPABILITY=YES GROUNDING=GROUNDED CONTENT_CHARS=1132 MATERIAL_ACT=0
```

**K1_RESULT:** `PASS`

### K2 — continuidade

**Correlation:** `3b2c3a41-bc75-46e0-a600-3503f35ca926`

```text
prior_continuation=transformed excerpts=12
LIMITATIONS=prior_turn_evidence_only
HTTP=200 TOTAL_MS=12313 GROUNDING=NON_GROUNDED (continuity)
CONTENT_CHARS=324 BULLET_LINES=6
OWNER_REINVOCATION=NO (no provider invoke on K2 turn)
MATERIAL_ACT=0
insufficient_evidence=NO invalid_record_index=NO
```

**K2_RESULT:** `PASS`

### K3 — VISTA

**Correlation:** `fecbe804-c110-47fc-8cac-f30d816a6a7c`

```text
SPECIALIST=vista CAPABILITY=get_product_guide
INDEX_SELECT=no_match (index_select timing_ms=5387)
NESTED_GUIDANCE=NOT_REACHED
CLARIFICATION=YES TOTAL_MS=21784 GROUNDING=NON_GROUNDED
MATERIAL_ACT=0 turn_budget_exhausted=NO
```

**K3_RESULT:** `PASS` (clarificação segura dentro do orçamento; alinhado ao aceite I02 doc26)

### K4 — DAVI holdout

**Correlation:** `8a83dbfc-6b50-47f6-b3e3-7e805ee2b926`

```text
discover_delpi_information discovery_terminal=CAPABILITY_NOT_MATCHED eligible=95
TOTAL_MS=17335 GROUNDING=GROUNDED CONTENT_CHARS=799 MATERIAL_ACT=0
```

**K4_RESULT:** `PASS` (sem regressão I03)

## 5. Rollback

```text
git revert 9a8775018f31111ce59b11945efec962e0db73d4
```

## 6. State

```text
K2_FAILURE_REPRODUCED=YES
K2_CODE_CHANGE=YES
K2_LIVE=PASS
K3_TIMEOUT_REPRODUCED=YES (synthetic stage)
K3_CODE_CHANGE=YES
K3_LIVE=PASS
K1_REGRESSION=PASS
K4_DAVI_REGRESSION=PASS
I03_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
