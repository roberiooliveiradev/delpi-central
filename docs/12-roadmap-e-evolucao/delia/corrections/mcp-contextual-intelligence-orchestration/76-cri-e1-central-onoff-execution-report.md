# 76 — CRI E1: Central ON/OFF Execution Report

**TASK_ID:** `DELIA-CRI-E1-CENTRAL-ONOFF-01`
**BASE_HEAD:** `ba68c5a3063293837a8bb237d8d828f8a0165e6a` (see final SHA in git history)
**Date:** 2026-10-21
**Gate:** E1 of roadmap 74 — implementation bounded to the centralized
activation control and its composition boundary. No E2/E3 behavior.

---

## 1. Scope executed

Implements exactly what spec 75 §4.1 decided: reuse the existing
`Settings._env_flag` + `root_composer` single-injection precedent
(`DELIA_MCP_*_ENABLED`) for one response-intelligence switch resolved
once at composition and injected into the governed-outcome → response
boundary. No new flag platform, registry, planner, runtime or service.

## 2. Mechanism

| Element | Implementation |
|---|---|
| Flag | `DELIA_RESPONSE_INTELLIGENCE_ENABLED` |
| Parser | `Settings._env_flag` vocabulary (`1/true/yes/on` → true; `0/false/no/off` → false) |
| Default / absent | `false` → baseline |
| Invalid value | `false` → baseline + safe diagnostic (`response_intelligence_config_invalid`, `reason=invalid_env_value` at composition — never the raw value) |
| Read point | `Settings.__init__` (single env read; no scattered `os.getenv`) |
| Resolution point | `_compose_turn_handler` in `root_composer` — exactly once per handler construction |
| Consumer | `HandleInteractiveConversationTurn` — typed `response_intelligence_enabled: bool` injected at the boundary before governed orchestration runs |
| Runtime SHA | `DELIA_RUNTIME_SHA` → `settings.runtime_sha`; `unknown` when absent/unreliable — never an error source |

## 3. OFF / ON behavior

- **OFF (baseline):** `self._response_mode == "baseline"`; the
  governed chain runs exactly as before — selection, arguments, MCP/Domain
  reads, grounding, provenance, statuses, limitations, selection-only
  synthesis and `compose_presentation` unchanged. No CRI resource is
  loaded (none exists yet); no extra model call.
- **ON (cri):** `self._response_mode == "cri"`; proves the boundary
  selection only. Functional output is bit-identical to baseline
  (proven by `_result_projection` equality on the serialized result —
  content, message kind, epistemic class, limitations, grounding,
  provenance). No fictional CRI answer is synthesized; E2/E3 attach at
  the same logged point (`stage=response_mode`).
- **No additional model calls** in either mode (spy-model test).

## 4. Observability

- Composition: `delia_response_intelligence mode=cri|baseline
  enabled=<bool> config_source=environment|default runtime_sha=<sha|unknown>`
  once per handler construction.
- Turn processing: `interaction stage=response_mode decision=cri|baseline
  session_id=<id> turn_id=<id>` once per processed turn inside
  `_execute_observed` — identity fields only; no input text, content,
  prompts, tokens or secrets.
- Invalid config: `delia_response_intelligence decision=fail_closed
  reason=invalid_env_value` — warning without the raw env value.
- No new correlation IDs are minted; the existing session/turn
  identifiers are reused.
- Resource version: not yet applicable — E2/E3 declarative resources
  do not exist; the contract point (composition log) is ready to
  receive a resource version field later without format change.

## 5. Files changed

- `delia-api/app/infrastructure/config/settings.py` — flag parse +
  `config_source`/`config_invalid`/`runtime_sha` (+ shared
  `_ENV_FLAG_TRUE/_ENV_FLAG_FALSE` frozensets extracted for reuse).
- `delia-api/app/composition/root_composer.py` — single resolution,
  composition log, fail-closed warning, typed injection.
- `delia-api/app/application/interaction/handle_interactive_turn.py` —
  `response_intelligence_enabled` kwarg (default False), `_response_mode`,
  per-turn mode marker.
- `delia-api/tests/test_cri_e1_response_intelligence_toggle.py` — 23 tests.

`orchestration.py` untouched; `serialize_result`, `compose_presentation`,
`InteractiveTurnResult`, HTTP routes and contracts untouched.

## 6. Test evidence

| Area | Tests | Result |
|---|---|---|
| A. Config parsing | absent→OFF/default; true vocab; false vocab; invalid→OFF+invalid flag; runtime_sha env/unknown | PASS |
| Composition | mode injection cri/baseline; config_source/runtime_sha in log; invalid→baseline+warning | PASS |
| B. OFF parity / C. ON selection | identical serialized governed result OFF vs ON; `decision=cri` logged; identical orchestration call shape | PASS |
| Model calls | ON adds zero model invocations | PASS |
| D. Security | flag never reaches `attempt()` kwargs; WRITE_REJECTED path identical OFF/ON | PASS |
| E. Rollback | env flip + rebuild: OFF→cri→baseline, absent→baseline | PASS |
| Full suite | `1713 passed, 3 skipped` (baseline 1690+3 before E1) | PASS |
| Syntax | `py_compile` on all touched files | SYNTAX_OK |

Security-negative coverage: invalid env cannot activate; mode cannot
alter orchestration inputs; write-rejection lifecycle identical under
ON; suite's redaction/provenance/never-ACT-by-text tests all pass.

## 7. Rollback

Mechanism = env change + process restart (settings read once at
composition). Proven: `off → on → off` and `on → absent` cycles via
fresh `Settings()` + `_compose_turn_handler` rebuild restore
`baseline`. No hot toggle claimed.

## 8. Residuals / non-goals honored

- ON changes **no content** — E2 (`OUTCOME-AWARE-ANSWER`) and E3
  (`PERSONALITY-AND-GROUNDED-PRESENTATION`) attach at the logged
  boundary; nothing of them is pre-built here.
- No declarative resources, no JSON loaders (none required by E1 —
  spec 75 §10 explicitly defers them).
- `REAL_MODEL_TEST=NOT_RUN` — E4 scope.
- `PUBLIC_CONTRACT_CHANGE=NO`, `AUTHORITY_BOUNDARIES_PRESERVED=YES`,
  `SELECTION_ONLY_PRESERVED=YES`, `B1_UNCHANGED=YES`,
  `MATERIAL_ACT=0`, `PRODUCTION_DEPLOY=NO`.
- `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` — unchanged.

```text
CRI_E1=EXECUTED
FLAG=DELIA_RESPONSE_INTELLIGENCE_ENABLED
DEFAULT_STATE=OFF
FAIL_CLOSED=INVALID_ABSENT_TO_BASELINE
COMPOSITION_POINT=_compose_turn_handler
CONSUMER=HandleInteractiveConversationTurn
TESTS=1713_PASSED_3_SKIPPED
I04_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=COORDINATION_REVIEW_THEN_E2
```


## 9. Independent coordination review — 2026-10-21

**VERDICT: `ACCEPT_WITH_RESIDUAL` for bounded E1.** Reviewed published implementation at `d65d5035a8a30cd2f8f23773780ab4d095f21f64` against E0 doc 75 and E1 gates: `Settings` uses the existing `_env_flag` convention and invalid-value diagnostics; `root_composer` resolves once and injects mode into `HandleInteractiveConversationTurn`; handler records per-turn `response_mode` without changing attempt/synthesis/presentation content. `orchestration.py` unchanged. Executor-reported full suite: `1713 passed / 3 skipped`; **independent suite re-execution `TEST_NOT_RUN`**, source inspected statically. Compare from baseline includes unrelated concurrent controllership commits, not part of E1.

**Accepted within E1:** OFF baseline preserved by design and executor tests, ON observability-only path, no model-call additions, no new flag engine, no resource loader or speculative CRI behavior. **Residual:** mode switch still requires environment modification and restart, not hot toggle; effective model/resource real-runtime quality awaits E2–E4. Do not represent E1 as a fully functional answer-intelligence feature or assert production activation. E2 must actually consume the centrally injected decision and prove OFF parity, outcome correctness, and fail-closed semantics; no independent production run authorized here.

`E1_VERDICT=ACCEPT_WITH_RESIDUAL`; `E1_CLOSED=YES`; `E2_AUTHORIZABLE=YES_SEPARATE_BOUNDED_TASK`; `E2_IMPLEMENTED=NO`; `PRODUCTION_DEPLOY=NO`; `I04_ACCEPTED=NO`; `C3_EXECUTED=NO`.
