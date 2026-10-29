# 201 — PydanticAI vs. DÉLIA baseline: structured-decision reliability A/B

**Task**: `DELIA-C3-PYDANTICAI-STRUCTURED-DECISION-AB-01`
**Scope**: experimental local harness, comparison and evidence. No production
deploy, no production model/owner calls, no production contract or dependency
changes.
**Base HEAD at reanchor**: `8a8ee4ec5080` → advanced to `92a5c1c428` by
unrelated concurrent commits; zero `delia-api` drift since.

---

## 1. Baseline implementation (inventoried, not assumed)

```text
RESPONSIBILITY=structured LLM output → typed stage proposal → semantic gates
OWNER=delia-api application layer
CANONICAL_SOURCE=app/application/capability_provision/orchestration.py
  (_propose: expected_fields presence-check + allowed_keys projection)
  + per-stage semantic validators downstream
  (e.g. interaction_class vocabulary, status coercion)
CONSUMERS=all governed stage proposals (admission, selection, assessment,
  arguments, synthesis wording, etc.)
CONTRACT=InvokeModel / ModelInvocationPort (EvalBindRequest,
  OpenAICompatibleModelInvocationAdapter in infrastructure)
IMPLEMENTATION=JSON parse → required-field presence → allowed_keys strip
  → typed proposal dict → stage-specific semantic gate
```

- `EXISTING_EQUIVALENT=YES` — baseline already validates structure and
  applies governed semantic gates; Pydantic 2.14.1 is already a production
  dependency.
- `REUSE_DECISION=EXTEND` for the harness only: an isolated evaluation
  script under `delia-api/scripts/` consuming the existing adapter for the
  baseline arm. No port expansion was needed.
- `ABSTRACTION_GATE=PASS` — SDK confined to the eval harness; zero
  `pydantic_ai` imports in `app/` (residual grep: clean).

## 2. Failure-mechanism diagnosis (observed, not estimated)

Distinguishable failure classes mapped onto the baseline flow:

| Class | Baseline behavior |
|---|---|
| Invalid JSON syntax | `invalid_structured_output` typed error → retry-eligible per budget |
| Missing required field | rejected (`expected_fields` presence-check) |
| Wrong field type | **accepted** (presence is not type-check; e.g. `"applicable": "yes"`) — semantic gate may still reject downstream |
| Invalid enum value | **accepted then coerced**: unknown `status` → `"sufficient"` downstream (fail-open coercion, now exposed by strict arm) |
| Extra unexpected properties | accepted — stripped by `allowed_keys` projection |
| Semantic-invalid selection | rejected by stage gates (unknown capability, forged candidate token, unauthorized owner) |
| Timeout / provider error | typed `ModelInvocationError.code` → governed retry budget |

Documented incident source: prior local smoke on `delia-json` showed 2
invalid attempts on `interaction_admission` under conversational context —
the reason this task targets that stage specifically.

## 3. Candidate library assessment

- `pydantic-ai-slim==2.50.0`, MIT, Python ≥3.10, published 2026-09-24
  (≥7 days; not the latest line — deliberate pin).
- Slim dep tree: anyio, genai-prices, griffelib, httpx2,
  opentelemetry-api, pydantic, pydantic-graph, typing-inspection —
  compatible with existing pydantic 2.14.1 / langgraph 1.2.16.
- Recorded in `requirements-eval.txt` (eval-only slot); **not** in
  `requirements.txt`, Dockerfile untouched.
- Mode selected: `NativeOutput` — provider-side `json_schema`
  response_format (Ollama openai-compat supports it; verified live).
  Tool-based output rejected by design (V12: no tool execution).
- Direct-request API only (`direct.model_request_sync`): zero framework
  retries, zero agent loop, no history persistence, provider-reported
  usage. PydanticAI Agent/validators/retry machinery deliberately unused —
  it would become a second planner/authority.

## 4. Experimental boundary

```text
same model (delia-json, local Ollama)
same instruction text (verbatim from orchestration_instructions.delpi.json)
same input text
arm baseline:  OpenAICompatibleModelInvocationAdapter → baseline_verdict()
arm pydanticai: direct.model_request_sync(NativeOutput, strict schema,
                allow_text_output=False, retries=0) → allow-list projection
```

`APPLICATION_CONTRACT_CHANGED=NO`, `PRODUCTION_CODE_CHANGED=NO`,
`PRODUCTION_DEPENDENCIES_CHANGED=NO`.

## 5. RED → GREEN

`tests/test_pydanticai_structured_output_eval.py` — 20 tests mapping V1–V18
(parity, rejection, forbidden-coercion, fail-closed enum, retry-ceiling,
no-tool-execution, token accounting, architecture isolation).
True RED: module absent → all RED → harness GREEN **20/20**.

## 6. Deterministic corpus (same raw response, all arms)

12 cases × {baseline, strict-pydantic, forbid-projection}:

```
valid_selection               base T  strict T  forbid T
malformed_json                F       F         F
missing_required_field        F       F         F
wrong_field_type              T       F         F   ← delta
invalid_enum                  T       F         F   ← delta
extra_unexpected_properties   T       T         F
non_object_output             F       F         F
applicable_false_passthrough  T       T         T
semantically_invalid          T       T         T   (downstream gate's job)
forged_candidate_token        T       T         T   (downstream gate's job)
empty_content                 F       F         F
plus provider/timeout/cancellation coverage in tests
```

10/12 agreement. The 2 deltas are the earlier-rejection finding: strict
schemas reject wrong types and invalid enums **before** the baseline's
downstream semantics — including exposing the fail-open
unknown-status→`sufficient` coercion.

## 7. Live real-model results (delia-json, local Ollama, 78 calls)

- `select_group` + `native_assessment`: 30 calls — **0 invalid outputs,
  both arms**.
- `interaction_admission` (the stage that previously produced invalid
  outputs): 48 calls — **0 invalid outputs, both arms**.
- Input tokens: **identical** (27140 vs 27140) — schema rides in
  `response_format`, not the prompt.
- Output tokens: PydanticAI arm marginally higher (strict schema always
  emits `limitations: []`); no savings.
- Latency: comparable (within per-run variance on a 3.1B local model).
- Semantic quality: equivalent — including equivalent weaknesses
  (e.g. `hypothetical` misclassifications, `applicable:false` +
  `capability_group_id` noise) — a schema cannot fix semantics; the
  downstream gates own that.

`TOKEN_SOURCE=PROVIDER_REPORTED` for both arms.

## 8. Contract / security comparison

- Retry budget: preserved — PydanticAI retries=0, `provider_requests==1`
  per call, counted identically.
- PREPARE/ACT: preserved — harness never touches execution; V17 covered.
- Provenance/observability: unchanged (harness-only).
- No hidden tool calls (function tools absent); no provider-specific code
  in Application; SDK import surface confined to `scripts/`.

## 9. Verdict

**EXTEND_BASELINE.**

PydanticAI's native schema mode works correctly against the provider, is
cleanly bounded, and adds no governance risk — but on the fine-tuned
`delia-json` model it demonstrated **zero** measurable reliability or
efficiency gain (0/78 invalid in both arms, identical input tokens). The
only genuine delta found lives one layer down: **earlier rejection of
wrong types and invalid enum values** — and that does not require the
framework at all. Plain Pydantic (already a production dependency) or a
focused contract hardening of the baseline `expected_fields` semantics
delivers the same effect for zero added dependency surface.

The one material finding worth a separate bounded decision: the baseline
coerces unknown `native_assessment.status` values to `"sufficient"`
(fail-open). Strict-schema validation exposes it; whether to make the
baseline reject it earlier is a contract decision for coordination, not
something this task changes.

## 10. Files / dependencies

- `delia-api/scripts/pydanticai_structured_output_eval.py` (new, harness)
- `delia-api/tests/test_pydanticai_structured_output_eval.py` (new, V1–V18)
- `delia-api/requirements-eval.txt` (pinned eval-only dep + rationale)
- No app code, no production deps, no prompts, no graph changes.

## 11. Regression evidence

- Harness suite: 20/20 GREEN
- Focused: model_invocation + interaction_runtime + capability +
  engine_selection + engine_b suites — 231 GREEN
- `audit_architecture_phase3.py`: OK, no new regressions
- `audit_backend_boundaries.py`: 0 findings
- Residual search: no `pydantic_ai` in `app/` or `requirements.txt`

## 12. Unresolved / next bounded step

- Live reliability delta on the **production model** is unknowable from a
  3.1B local model — production eval is not authorized and was not run.
- The fail-open status coercion is documented here for a future bounded
  contract decision.
- If `delia-json` regresses in real traffic, native schema mode is now a
  proven drop-in arm behind the same contract.
