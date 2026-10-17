# 44 — Specialist knowledge utilization eval (DAVI / TÉO / VISTA)

**DATA:** 2026-10-17  
**TASK_ID:** `DELIA-C3-MCP-SPECIALIST-KNOWLEDGE-UTILIZATION-EVAL-01`  
**MODE:** evidence-only; `SOURCE_CODE_CHANGE=NO`; `DEPLOY=NO`  
**REFERENCE_HEAD:** `558421fd729ed7e35592804b9b99748f5588aad5`  
**DEPLOYED_SHA:** `e9b2f46287389f9376ee75502baa1e2369948c40` (behind reference; docs-only commits on origin after deploy — no pull/restart performed)  
**MODEL:** `moonshotai/kimi-k3`

## Capability status (runtime-proven this eval)

| Capability | Owner | Status |
|---|---|---|
| `get_methodology_guide` | teo | PROVEN (K1/K2 invoke) |
| `get_catalog` | teo | PROVEN (discovery step K1/K2) |
| `get_product_guide` | vista | PROVEN (K3 index+topic) |
| `discover_delpi_information` | davi | PROVEN (K4 invoke) |
| `get_product_guide` / `get_catalog` (teo product) | teo | TO_INVENTORY (not exercised) |
| `suggest_change` / `get_playlist_context` | vista | TO_INVENTORY (not in this matrix) |
| `execute_delpi_information` | davi | TO_INVENTORY (not required for K4) |

## Per-turn evidence

### K1 — TÉO methodology

```text
CORRELATION_ID=4129869c-e0a5-4dcf-9dfd-4f3de88caf00
SELECTED=mcp:teo / get_methodology_guide (+ get_catalog DISCOVERY)
OWNER_KNOWLEDGE_CALLED=YES
KNOWLEDGE_USED_IN_RESPONSE=YES (owner payload projected; authority GUIDANCE_NOT_SOURCE_OF_TRUTH)
GROUNDING=GROUNDED
LATENCY_MS=28910
MATERIAL_ACT_COUNT=0
VERDICT=PASS_WITH_LIMITATION
```

**Limitation:** `synthesis decision=skip_budget remaining_ms=1103` — user-facing text is largely structured guide dump, not a pedagogic rewrite. Methods/invariants from the methodology owner are present (suggested cause ≠ proven cause, evidence states).

### K2 — TÉO contextual follow-up

```text
CORRELATION_ID=110e17fa-97f7-4b94-8bd4-6731f36531f7
SELECTED=mcp:teo / get_methodology_guide (again)
GOAL prior_sufficient=no
LITERAL_REPLAY_OF_K1=YES
LATENCY_MS=30014 (GLOBAL_BUDGET_EXCEEDED)
SYNTHESIS=timeout → budget_fallback
VERDICT=FAIL
FAILURE_STAGE=INTENT_UNDERSTANDING (prior_sufficient) + SYNTHESIS/TURN_BUDGET
```

Did not treat K1 methodology OBSERVATION as sufficient to answer “quais informações levantar”; re-ran catalog+guide; returned identical content; exceeded 30s.

### K3 — VISTA product guidance

```text
CORRELATION_ID=f7de981a-4475-46b4-b380-ff369657b56d
SELECTED=mcp:vista / get_product_guide
INDEX_PROBE=ok → index_select bound topic → READ with topic
CONTENT=block_types / visualization families (truncated)
LIMITATIONS=result_truncated
SYNTHESIS=skip_budget remaining_ms=5900
NO playlist inspection; NO PREPARE/ACT
VERDICT=PASS_WITH_LIMITATION
```

### K4 — DAVI discovery

```text
CORRELATION_ID=1b926504-8afe-4af4-9846-ffeae0d3da19
SELECTED=mcp:davi / discover_delpi_information (not OpenAPI force)
INVOKE=ok arg_keys=query,top_k
RESPONSE=honest empty match (“nenhuma ação correspondente…”)
NO invented tables/fields; NO writes
VERDICT=PASS_WITH_LIMITATION
```

Discovery path selected correctly; utilization incomplete for listing product-query possibilities (empty match for the formulated query).

## Scorecard

| Dimension | Result |
|---|---|
| SPECIALIST_KNOWLEDGE_DISCOVERY | PASS (correct owners/capabilities chosen when needed) |
| SPECIALIST_KNOWLEDGE_UTILIZATION | PARTIAL (K1/K3 knowledge present but synthesis starved; K2 unused prior; K4 empty match) |
| KNOWLEDGE_TO_NEXT_STEP | FAIL on K2 continuity |
| PROVIDER_NEUTRALITY | PASS (OpenAPI not forced; DAVI selected when meta-discovery fit) |

```text
TESTS_EXECUTED=4
PASS=0
PASS_WITH_LIMITATION=3
FAIL=1
INCONCLUSIVE=0
TEST_NOT_RUN=0
MAX_OBSERVED_LATENCY_MS=30014
MATERIAL_ACT_COUNT=0
```

## Proven gaps (no implementation in this task)

1. **K2 continuity / goal:** `prior_evidence_sufficient=false` on a follow-up that only needs transforming prior methodology → unnecessary re-invoke + literal replay.  
   `EXISTING_EQUIVALENT=YES` (prior_continuation + GOAL instruction) · `REUSE_DECISION=EXTEND` candidate (tighten when prior OBSERVATION is methodology/product guide and ask is “inputs/steps from that guide”).

2. **Synthesis budget on knowledge READ:** K1/K3 `skip_budget` and K2 synthesis timeout leave raw/truncated owner dumps.  
   Candidate: preserve headroom after discovery/index for selection-only synthesis — **without** raising global 30s.

3. **K4 discovery query framing:** empty action match for “possibilities about products” — may need better argument projection or presenting discovery catalog honestly when top_k is empty.  
   `EXISTING_EQUIVALENT=TO_INVENTORY` (owner discovery contract shape).

## Security invariants observed

```text
GUIDANCE != DOMAIN_FACT (teo/vista authority markers present)
DISCOVERY != AUTHORIZATION
READ only; PREPARE/ACT=0
MODEL_AUTHORED_FACTUAL_PROSE avoided via owner projection / skip_budget
```

```text
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=INDEPENDENT_KNOWLEDGE_UTILIZATION_REVIEW
```
