# 265 — DÉLIA · Review independente G6 e handoff G7

**DATA:** 2026-11-05  
**TASK:** `DELIA-C3-G6-HTTP-DEADLINE-AND-INCREMENTAL-STT-BOUNDED-TRANSPORT-01`  
**BASE_SHA:** `7fa80a4ee1b2d345bc8d2b1c8c0c75ddf6ab825a`  
**REVIEWED_SHA:** `f8ff2b6e56e468202066a9f5fc5c3c95c5626349`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for bounded G6 change; integration/protocol proof pending G7.  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED; **E01–E10:** TEST_NOT_RUN.

## Verified from GitHub

- One DÉLIA commit: `infrastructure/model_invocation/openai_compatible_transcription_adapter.py` +73/-49; `tests/test_dictation_transcription.py` +74; `tests/test_incremental_streaming_protocol.py` +17/-13; doc256 +18.
- `stream_transcribe` now calls `self._http_post` defaulting to `deadline_http_post`, with the entire POST + `response.iter_lines()` inside `deadline_scope(deadline)`. It has a monotonic deadline check after every yielded line and catches `BoundedHttpTimeout` / requests Timeout as `DictationError(PROVIDER_TIMEOUT)`; transport errors map `PROVIDER_UNAVAILABLE`.
- `deadline_transport.py` existing socket wrapper and DNS resolver claim absolute deadline for connect/TLS/status/body in controlled direct-only sessions; no second transport invented. `deadline_http_post` uses `with _deadline_session() as session: return session.post(...stream=...)`, which **closes the Session before subsequent iter_lines consumption**. Whether an already-open streamed response remains readable requires an instrumented real streaming test; no unsupported assertion of defect. If broken or timing resource issues proven, fix within existing adapter/transport without creating a new HTTP stack.
- Streaming uses byte-line UTF-8 decoding, preserving multilingual characters, maps observed SSE deltas cumulatively, closes response in finally.
- The new tests use injected fake post and fake timeout to prove wiring and exception mapping; 4 SSE tests migrated to injected interface. Executor reports 53/53 STT PASS and backend suite exit 0; reviewer did not execute tests independently.
- No evidence from reviewed tests of a **real** trickle/stall over network, TLS handshake stall, DNS, disconnect during SSE or max incremental buffered bytes. Real owner STT business outcome remains G7.
- No production deployment authorized for this cleanup.

## Residuals: bounded G7 checks (not G6 scope redesign)

1. Real local HTTP SSE server: slow trickle bytes at intervals less than read inactivity timeout, stall mid-line, split UTF-8, status delay, timeout during POST vs SSE, client cancellation/close, ensure absolute duration bound and no detached request.
2. Verify `deadline_http_post` session lifecycle: response returned after session exit. Confirm stream works for repeated long SSE via local server and socket closes after cancel/timeout. If bug proven, smallest change to ensure response/session resource lifecycle matches stream while maintaining trust_env=False, proxy policy and deadline.
3. Verify SSE cumulative buffer and audio/request and response size bounds, no raw payload/security secret in log or NDJSON. Existing tests may cover parts; reuse before designing.
4. Integrate model/owner E01–E10 (user questions, not only HTTP 200): native PydanticAI tool loop, grounded SourceRefs and outcome, retries/usage after rework, real delegated MCP, snapshot A/B, OpenAPI foundation C3-T5, auth/prompt-injection/partial failures. Exact SHA, model/hash/config/owner evidence, token usage labels, latency and fail-closed negatives.
5. Preserve G1–G6 regressions, full backend/architecture/UX where applicable, no ACT/production deploy. Report `PASS|FAIL|INCONCLUSIVE|TEST_NOT_RUN` per check; no phase progression merely because docs updated.

## G7 authorized execution handoff

**TASK_ID:** `DELIA-C3-G7-INTEGRATED-REAL-MODEL-SECURITY-AND-OUTCOME-VERIFICATION-01`

- First reanchor actual main HEAD/status, canonical sources 16→50→17→49→51→52→21→20→25, tech/product/specs, ledger, docs 256/259–265. Preserve unrelated work.
- Freeze evaluation matrix and oracle before running; use existing E01–E10 and model/owner evaluation harness where available, no new verifier engine, no green status from mocks.
- Execute independent repeatable tests: (A) G6 SSE deadline real local server + cancellation and lifecycle, (B) G4 whole PydanticAiInvestigationEngine with recorded physical provider requests/usage/deadline and governed tools, (C) E01–E10 with real local authorized LLM and actual owner paths, (D) security negative tests (MCP metadata prompt injection, discovery!=approval, Keycloak/Core/Domain/AuthZ, read/write, partial evidence, provenance, C3-T5 and snapshot equivalence). Distinguish TEST_NOT_RUN if environment unauthorized.
- If a genuine defect discovered, perform bounded RED→GREEN fix in the legitimate boundary only; do not reflexively implement another engine, reintroduce CRI or change frozen contract. For authority conflicts STOP affected branch as `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED`.
- Outcome-based report by E-case: question, expected authoritative business outcome, actual owner SourceRefs, content status/grounding, retries/physical calls, latency, measured tokens vs estimates, pass/fail/inconclusive reasons, exact SHA/config/model. Full regressions and residual scan, docs/ledger after facts, commit/push. No production deploy.

**STATUS:** Review is code/doc analysis only; runtime tests not independently executed by reviewer.
