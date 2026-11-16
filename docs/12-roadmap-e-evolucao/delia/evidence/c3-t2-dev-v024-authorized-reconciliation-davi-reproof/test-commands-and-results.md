# Test commands and results — 2026-11-16, SHA c176dac339a

## Regression (delia-api, container)

```text
docker exec delpi-delia-api sh -c "cd /app && python -m pytest \
  -o addopts='' -q \
  tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py \
  tests/test_c3_t2_http_multiturn_boundary.py \
  tests/test_interaction_runtime.py \
  tests/test_mcp_provider_eligibility_revalidation.py"
→ 119 passed in 2.72s — exit 0
```

## HTTP multiturn live (two real POSTs, canonical context)

```text
DELIA_EVAL_TWO_AGENT=1 bash delia-api/scripts/run_c3_t2_http_multiturn_live.sh
→ EVAL_COMPLETE=YES; PROD_CONTAINER_UNTOUCHED=YES — exit 0
→ correlation http-mt-351936f0111f
→ turn1 "Quero ver a estrutura de um produto" → CLARIFICATION_REQUIRED
   (NON_GROUNDED, agent_requested_clarification, no premature consult)
→ turn2 "90260921" (context = canonical [USER_INPUT, DELIA_RESULT]
   from turn-1 response; MANUALLY_INJECTED_PRIOR_TURNS=false;
   SAME_AUTHORIZED_SUBJECT=true)
   → davi.read arguments.code=90260921 → SUCCESS → GROUNDED
   → product 21010421 CHICOTE DE LIGACAO (PA), components listed
→ INVARIANTS all true: HTTP_REQUESTS=2, CONTEXT_SOURCE=CANONICAL,
   TURN1_CLARIFICATION, TURN2_HTTP_OK, TURN2_GROUNDED
```

## Live INT2 instrumented eval (two-agent, OpenRouter qwen3-14b)

```text
DELIA_EVAL_TWO_AGENT=1 DELIA_EVAL_CORPUS=INT2 \
DELIA_EVAL_SCENARIO_IDS=G2,R5,C2,D,R6_clarification \
bash run_int1_openrouter_qwen14b_instrumented_eval.sh
→ EVAL_COMPLETE=YES — exit 0
```

| Scenario | Result |
|---|---|
| G2 aggregation_active_scope | NON_GROUNDED honest — model chose MCP:analyze path, claimed "200" unsubstantiated; sufficiency engine overrode declared `complete` (obligation UNSATISFIED) — fail-closed prevented a wrong grounded answer |
| R5 multipage_full_enumeration | GROUNDED, SATISFIED — 3 paginated reads, full 109-item list, complete |
| C2 record_detail_product | GROUNDED, SATISFIED — davi.read → real structure 90260921 |
| D insufficient_product | GROUNDED, `insufficient` — 99999999 exists, no BOM; honest limits |
| R6 clarification_needed | NON_GROUNDED + agent_requested_clarification — no premature consult (mcp:[]) |

G2 second sample: see live_int2_g2_retry.log (added to artifacts).
