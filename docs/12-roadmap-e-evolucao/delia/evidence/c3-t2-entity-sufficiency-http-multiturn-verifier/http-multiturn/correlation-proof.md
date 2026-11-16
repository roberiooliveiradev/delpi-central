# Correlation proof

```yaml
HTTP_CONVERSATION_ID: http-mt-42e226d1432a
SUBJECT_FINGERPRINT: 4903c6464e2cd62d
CONTEXT_SOURCE: CANONICAL_APPLICATION_BOUNDARY
MANUALLY_INJECTED_PRIOR_TURNS: false
HTTP_REQUESTS: 2
SAME_AUTHORIZED_SUBJECT: true
TURN1_CLARIFICATION: true
TURN2_OBJECTIVE_RECOVERY: true
TURN2_OWNER_READ: true  # davi / get_product_structure / 90260921
TURN2_GROUNDING: GROUNDED
TURN2_BUSINESS_OUTCOME: CHICOTE DE LIGACAO + component 10020003 qty 175
MODEL: qwen/qwen3-14b
CONFIG_FINGERPRINT: e4a5b706a3b3156b
TWO_AGENT_EXPERIMENT: eval-only
```

Session IDs differ per request by design (no server-side session store);
continuity is the validated HTTP `context` field recovered from turn-1.
