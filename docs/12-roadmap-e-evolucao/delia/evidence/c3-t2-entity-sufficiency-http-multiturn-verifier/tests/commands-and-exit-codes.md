# Commands and exit codes

```text
docker exec delpi-delia-api python -m pytest -q \
  tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py \
  tests/test_c3_t2_http_multiturn_boundary.py
→ 29 passed, exit 0

docker exec delpi-delia-api python -m pytest -q \
  tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py \
  tests/test_c3_t2_http_multiturn_boundary.py \
  tests/test_interaction_runtime.py \
  tests/test_mcp_provider_eligibility_revalidation.py
→ 119 passed, exit 0

bash delia-api/scripts/run_c3_t2_http_multiturn_live.sh
→ EVAL_COMPLETE=YES; TURN2_GROUNDED=true; PROD_CONTAINER_UNTOUCHED=YES

DELIA_EVAL_TWO_AGENT=1 DELIA_EVAL_CORPUS=INT2 \
DELIA_EVAL_SCENARIO_IDS=INT2_G2_aggregation_active_scope \
bash delia-api/scripts/run_int1_openrouter_qwen14b_instrumented_eval.sh
→ evaluation_id=or-qwen14b-aca443baae46; GROUNDED; SATISFIED; answer=109
```
