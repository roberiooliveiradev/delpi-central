# 268 — DÉLIA · Review independente G7 LIVE: regressão G3 de composition e gate de business outcome

**DATA:** 2026-11-05  
**TASK:** `DELIA-C3-G7-LIVE-E01-E10-OUTCOME-EVIDENCE-CLOSURE-01`  
**BASE REPORT:** `68500b78615f4c08fcdaea378c06155697516c13` (inclui alterações concorrentes entre base e commit).  
**REVIEWED CODE SHA:** `245e8cde255acd67509cff360ae0047442238c35`  
**REVIEW DECISION:** **EXECUTION_DRIFT** discovered in prior G3 cleanup / G8 “clean” assertion; bounded composition repair is **ACCEPT_WITH_RESIDUAL** in source, but **G7 business-outcome review = INCONCLUSIVE** (0/10 GROUNDED); **overall G1–G8 functional acceptance NOT_GRANTED**.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## Direct GitHub inspection

- The fix commit modifies `delia-api/app/composition/root_composer.py` by **+10 lines, no source test added**; docs 256 and execution-ledger were updated. It restores a `try/except` around `load_orchestration_instructions(_ORCHESTRATION_INSTRUCTIONS_PATH,required_names=ORCHESTRATION_INSTRUCTION_KEYS).instructions`, with `None` on error, preserving existing fail-closed policy.
- Source shows `gates = OperationalCapabilityOrchestrator(...) if providers and orchestration_instructions is not None else None`. Consequently deleting the instruction load path silently disables all governed capability orchestration, even with live MCP providers. This is a material regression introduced during CRI retirement, **not** evidence that providers are absent or broken.
- Existing source imports `load_orchestration_instructions` and has a legitimate resource path. Restoring it is `REUSE`; no new runtime or planner created.
- The G7 report claims live boot-log transition `surface=absent` → `configured`, real catalog 10 caps/3 owners, 8 tool calls, 4 collected and honest terminal `no_business_evidence`/`CAPABILITY_NOT_ENUMERABLE`; these are **executor-reported live findings, not independently replayed**. They establish the path was exercised at least in reported cases; **NOT a business-success conclusion**.
- Pre/post outcomes: **0/10 GROUNDED** both before and after. Pre-fix collected null; post-fix real tools are invoked but none meets the benchmark's factual outcome oracle. Mark every E-case based on its actual original oracle, not a bulk PASS/FAIL from HTTP200 or honest NON_GROUNDED. A fully authorized case with known available owner data may be FAIL; unavailable authoritative data or missing context may be INCONCLUSIVE. This report cannot infer which without case-by-case oracle evidence.
- The report claims runtime environment has stale `DELIA_RUNTIME_SHA=c311e75e` whereas mounted `/app` has base `68500b7861` + patch. Record **EXECUTION_DRIFT** for runtime identity. Commit `245e8cde` includes fix, but the report does not prove a clean deployed runtime image at that exact commit. Do not use stale env as a SHA assertion. Before acceptance, independently fingerprint container mounted code, config, model, import location, and effective process startup, avoiding credentials.
- One run hit `ModelHTTPError` due to context overflow `4211 tokens > 4096 ctx`; this is a reproducible incompatibility/budget insufficiency with local model profile **if repeatable**, not automatically harmless merely because the model is small. Characterize model context policy, pre-call budget and telemetry separately; no unapproved config expansion.
- No end-to-end test for `_compose_turn_handler` with enabled specialist+valid orchestration instructions and invalid/missing resource is added by this commit. Entire backend suite PASS is executor-reported; cannot replace a path-sensitive startup regression test. The previously accepted G8 residual clean judgment was insufficient; do not silently preserve it as unconditional closure.

## Required bounded closure

**TASK_ID NEXT:** `DELIA-C3-G7-COMPOSITION-SURFACE-AND-LIVE-OUTCOME-REWORK-01`

1. Reanchor fresh git HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → technical/product/thematic specs → ledger and 256/267/268. Confirm actual runtime code/config/model SHA vs build image and mounted `/app`; remediate stale SHA reporting through authorized path without storing secrets. No production deploy.
2. Add a **behavioral composition RED→GREEN test**: with at least one enabled authorized specialist provider + valid orchestration instruction resource, composing the turn handler yields non-null governed orchestration and configured surface; with missing/invalid required instruction resource, fail closed but **emit an observable explicit capability-surface/config failure**, not a misleading owner-data absence. Exercise the production composition branch, not a mere source-text check. Preserve optional resource policy per canonical authority.
3. Verify instructions resource still contains all `ORCHESTRATION_INSTRUCTION_KEYS`; ensure unrelated CRI retired resources are not restored, and actual tool catalogs remain gated live. Regression test that removing the loader fails.
4. Re-run E01–E10 on exact authenticated runtime/config/model with **per-case oracle**: question, expected source/owner and known data availability, tool/authorization, actual business result, provenance, output, latency, tokens and status. Use `doc243_e_matrix_probe.py` existing harness, do not create another evaluator.
5. Diagnose `0/10 GROUNDED` by separating owner-domain data unavailable from capability/binding/argument failure, repeated discovery without outcome, insufficient local model context, and evidence projection. Require at least a controlled **real-owner positive control** using read-only data known to exist, with authorization and explicit authoritative outcome. If no positive case exists in dev, report test environment limitation, do not mark DÉLIA functional.
6. Reproduce `4211 > 4096` token overflow using measured prompt/context plus effective Ollama `num_ctx` and actual config. Determine whether existing context-budget gate applies to investigation Agent; if not, use the legitimate existing budget/adapter boundary to guarantee fail-closed or bounded truncation without dropping required evidence, preserving provenance. No provider-specific planner branches. Test at/below context boundary and above boundary; never report unverified usage counts.
7. Maintain PREPARE/ACT and Core/Domain authorization, no writes, no production deploy. RED→GREEN defects, full backend + security/architecture regression, live positive control and E-cases, residual search for startup dependency, update doc256, ledger, per-case evidence on actual SHA; commit/push preserving others' work.
8. If no authorized positive data, STOP functional acceptance with `INCONCLUSIVE` and specific blocked prerequisites; runtime PATH restored can still be independently accepted with residuals.

## RQ status / overall gates

- The previous executor matrix count remains 21 declared IMPLEMENTED / 7 PARTIAL (arithmetic corrected by review267); these are **implementation declarations**, not proven functional acceptance.
- **RQ-09 CRI retirement** cannot count as fully reviewed behaviorally when it suppressed the non-CRI orchestration instruction loader; G7 repair restores intended separation but requires direct startup regression proof.
- **RQ-24 G7 integrated eval** remains PARTIAL, now live execution occurred but 0/10 business-grounded; no positive control.
- **RQ-28 final independent disposition** remains PARTIAL; G8 “CLEAN” cannot certify end-to-end behavior after this material blind spot.
- Correct the doc256 prior `E01–E10=TEST_NOT_RUN` in an **append-only chronological update**, do not erase historical status for earlier SHAs.

**VERDICT:** `CODE_FIX=ACCEPT_WITH_RESIDUAL`; `CURRENT_LIVE_OUTCOME=INCONCLUSIVE`; `REVIEW_DRIFT=EXECUTION_DRIFT`; `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.
