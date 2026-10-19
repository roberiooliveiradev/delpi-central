# 31 — I03 · K2/K3 Bounded Non-Regression Validation and Remediation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I03-K2-K3-BOUNDED-NONREGRESSION-REMEDIATION-01`  
**BASE_HEAD:** `f3b113a869e00b072eb52c828f6a5293b0f0248f` (ancestor; working base after rebase includes §6.270)  
**AUTHORITIES:** [24](./24-i02-k2-k3-output-quality-remediation-implementation.md)–[29](./29-i03-independent-davi-crosscheck-review.md), ledger §§6.269–6.270  
**EXISTING_EQUIVALENT:** `YES` — `_prior_continuation_attempt` / `_propose_index_identifier`  
**REUSE_DECISION:** `EXTEND`  
**I03_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` (live section filled after deploy)

## 1. Reprodução

### K2 — `invalid_record_index`

**REPRODUCED:** `YES` (synthetic RED)

Cadeia:

```text
prior_evidence_sufficient=true
→ _prior_continuation_attempt
→ model proposes record_index fora de range
→ _render_synthesis → invalid_record_index
→ (antes) insufficient_evidence imediato
```

**ROOT_CAUSE:** `INVALID_MODEL_PROPOSAL` era tratado como `INSUFFICIENT_PRIOR_EVIDENCE`, apagando excerpts legítimos. O helper `_extraction_list_from_prior_excerpts` já existia, mas só rodava após render bem-sucedido.

### K3 — `budget_exceeded` / `delpi_source_unverified`

**REPRODUCED:** `YES` (synthetic RED — `model_timeout` e `turn_budget_exhausted` em `index_select`)

Cadeia:

```text
INDEX READ ok
→ _propose_index_identifier / _propose
→ residual < MIN_VIABLE ou model_timeout
→ _StageDeadlineExceeded propaga ao topo
→ SOURCE_UNAVAILABLE → delpi_source_unverified
```

**ROOT_CAUSE:** estágio opcional de `index_select` após INDEX bem-sucedido colapsava o turno em source-unavailable, embora `_clarification_question` já tivesse fallback determinístico para o mesmo tipo de deadline.

Não atribuído causalmente ao DISCOVERY terminal I03 (K4 path separado).

## 2. Correção mínima

| Área | Mudança |
|---|---|
| K2 | `_recover_prior_extraction_after_invalid_index` + ramo `recover_invalid_index` em `_prior_continuation_attempt` |
| K3 | `_propose_index_identifier` captura `_StageDeadlineExceeded` → `budget_skip` / `None` → clarificação |

Preservado: GLOBAL 30s; stage-cap 10 OFF; args-headroom OFF; K4 discovery classes; MESSAGE≠ACT; sem branch por especialista; sem inventar índices/registros.

## 3. Testes

`tests/test_i03_k2_k3_nonregression.py` + regressões I01/I02/I03/R2/R3/ACR + full `delia-api` pytest **PASS**.

## 4. Live (preencher pós-deploy)

| Field | Value |
|---|---|
| SOURCE_SHA | _(pending)_ |
| DEPLOYED_SHA | _(pending)_ |
| MODEL | _(pending)_ |
| BUDGET/STAGE | 30 / runtime env |

| Case | Result | Notes |
|---|---|---|
| K1 | _(pending)_ | |
| K2 | _(pending)_ | |
| K3 | _(pending)_ | |
| K4 | _(pending)_ | holdout discovery |

## 5. Rollback

```text
git revert <IMPLEMENTATION_SHA>
```

## 6. State

```text
K2_CODE_CHANGE=YES
K3_CODE_CHANGE=YES
K4_HOLD OUT=PRESERVED
I03_ACCEPTED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
