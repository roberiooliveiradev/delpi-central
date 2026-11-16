# Testes e regressão — final gates

**EVALUATED_BASE_SHA (pre-commit):** `5c4977f0e081ac3c8795f3afac4584f037379516`
**WORKDIR:** `delpi-delia-api` container (bind-mount `/app` → `delia-api/`)
**ENVIRONMENT:** DEV isolado

## Comandos

```yaml
COMMAND: python -m pytest tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py tests/test_int2_delivery_completeness_contract.py tests/test_r6_invented_identifier_rejection.py tests/test_rc5_anchor_correctness_remediation.py tests/test_c3_t2_evidence_closure_negatives.py tests/test_r45_pagination_integrity_rework.py tests/test_int1_investigative_progress_rework.py -q
EXIT_CODE: 0
RESULT: all PASS

COMMAND: python -m pytest tests/test_two_agent_experiment.py tests/test_pydantic_ai_semantic_rework.py -q
EXIT_CODE: 0
RESULT: all PASS

COMMAND: python -m pytest tests/ -q
EXIT_CODE: 0
RESULT: full delia-api regression PASS (warnings only: event loop deprecation)

COMMAND: python3 scripts/audit_cursor_rules.py
EXIT_CODE: 0

COMMAND: python3 scripts/audit_documentation_structure.py
EXIT_CODE: 0

COMMAND: bash delia-api/scripts/run_int1_openrouter_qwen14b_instrumented_eval.sh
ENV:
  DELIA_EVAL_CORPUS: INT2
  DELIA_EVAL_TWO_AGENT: true
  DELIA_EVAL_LIVE_MULTITURN_CHAIN: 1
  DELIA_EVAL_SCENARIO_IDS: INT2_G2_aggregation_active_scope,INT2_R5_multipage_full_enumeration,INT2_R6_clarification_needed,INT2_R6_multiturn_structure_recovery
EXIT_CODE: 0
EVALUATION_ID: or-qwen14b-00bb3f24aebb
MODEL_ID: qwen/qwen3-14b
CONFIG_FINGERPRINT: e4a5b706a3b3156b
PROD_CONTAINER_UNTOUCHED: YES
```

## Live outcomes

| Scenario | Classification |
|---|---|
| INT2_G2_aggregation_active_scope | LIVE_PASS (GROUNDED + SATISFIED, 109) |
| INT2_R5_multipage_full_enumeration | LIVE_PASS (GROUNDED + SATISFIED, 3 pages) |
| INT2_R6_clarification_needed | LIVE_PASS (clarification, 0 MCP) |
| INT2_R6_same_conversation_recovery | LIVE_PASS (live prior chain, GROUNDED + SATISFIED) |
