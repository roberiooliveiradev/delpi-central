# 98 — Context Panel, Evidence, Activities & LLM Usage Integration

**TASK_ID:** `DELIA-UX-CONTEXT-PANEL-EVIDENCE-ACTIVITY-AND-LLM-USAGE-INTEGRATION-01`
**Date:** 2026-10-22
**Mode:** REANCHOR → CONTRACT INVENTORY → REUSE GATE → REQUIREMENTS → IMPLEMENT → INTEGRATE → TEST → BROWSER QA → DOCUMENT → COMMIT → PUSH MAIN → REPORT
**Stage:** Prompt 5 of 6 of the integrated DÉLIA roadmap

---

## 1. Scope

Connect the existing `ConversationContextPanel` to real per-turn
interaction data: executed activities, evidence/provenance, outcome,
effective composition mode (CRI vs. deterministic vs. model), stage
latency, real model-call count, governed attempts, provider-reported
token usage, safe model metadata and honest cost state — reusing the
existing contracts, without a second observability infrastructure.

## 2. Contract inventory — what already existed

| Question | Verified answer |
|---|---|
| Does the provider return usage? | YES — adapters emit `UsageMetadata{input_units, output_units, unit_kind}` and measured `duration_ms` on `ProviderInvocationPayload` → `ModelInvocationResult` |
| Where was it lost? | The orchestrator's `_model_stage_proposal` and the handler's `_invoke` consumed the result and discarded `usage`/`duration_ms` — propagation gap, not instrumentation gap |
| Multiple model calls per turn? | YES — every semantic stage (admission, group, capability, arguments, assessment, synthesis) is a real call; governed retries re-enter the funnel |
| Activities/evidence to the wire? | YES — `ActivityEvent`/`ActivityEventSink` stream real phases over NDJSON; `provenance`/`grounding_status`/`limitations` already on `InteractiveTurnResult` |
| What reached the frontend? | A *reduced* activity view only — raw events (timestamps, sequence) were discarded after streaming; `ConversationContextPanel` rendered with zero props (always empty) |
| Effective CRI mode exposed? | NO — `response_mode` was internal to `attempt()`; a startup flag was never proof of use |
| Selection affordance? | `ConversationAssistantActions.moreActions` already exists — no new action component needed |

## 3. Reuse gate

| Responsibility | Decision |
|---|---|
| Model-call counting | REUSE `InvokeModel.execute` completions/errors at the two real call sites |
| Usage aggregation | NEW bounded request-scoped `ModelCallLedger` (ContextVar — same pattern as the activity sink and the resume checkpoint); projects only already-emitted fields |
| Activities/evidence/outcome | REUSE `ActivityEvent` stream, `provenance`, `limitations`, `grounding_status` |
| Presentation | REUSE `serialize_result` — one additive `observability` key |
| UI | REUSE `ConversationContextPanel`, `ActivityViewer`, `EvidenceDetails`, `ConversationAssistantActions.moreActions` |

No telemetry engine, token counter service, model registry, event
pipeline or interaction storage was created.

## 4. Implementation (bounded)

**Backend (`delia-api`)**

- `application/interaction/turn_observability.py` (new): request-scoped
  `ModelCallLedger` (max 24 calls), per-call observation
  `{stage, attempt, finish_status, duration_ms, input_tokens,
  output_tokens}` and `build_turn_observability()` — the only
  projection into the wire contract.
- `capability_provision/orchestration.py`: ledger recording inside the
  shared `_model_stage_proposal` funnel and on its error seam; a
  request-scoped attempt index (`ContextVar`) gives honest attempt
  numbers; replayed checkpoint proposals are data, never re-counted.
- `capability_attempt.py` / `contracts.py`: additive fields
  (`composition_mode`, `governed_attempts`, `observability`).
- `handle_interactive_turn.py`: ledger bound per request in `execute`,
  conversational `_invoke` recorded, `_with_observability` applied on
  every terminal path, `serialize_result` emits the additive block.

**Honesty rules enforced**

- `reported` only when *every* recorded call carried both directions;
  `partial` shows known directions with `total: null`; `unavailable`
  otherwise. A failed/timed-out call is counted, never zeroed.
- `cost: {status: "unavailable"}` — no provider reports billing and no
  versioned price table exists; nothing is estimated.
- Model block exposes `id`/`version`/`owner` only — provider identity
  stays out of the wire (canonical leak gate, §5).
- `finish_status` is normalized to `completed|timeout|error` — raw
  provider-level enum names never cross the boundary.

**Frontend (`plugins/delia`)**

- `App.tsx` retains the real `activityEvents` per turn and tracks the
  selected context turn.
- `DeliaAssistantMessage` exposes "Contexto" via `moreActions`;
  `ConversationTimeline`/`DeliaConversationPage` pass selection through.
- `api/interactionClient.ts` parses `observability` through a bounded
  allowlist — unknown keys never land.
- `ui/contextPanel.tsx` (new, render-only): Details (state, specialist,
  capability, composition, model, owner, latency, calls, attempts,
  tokens, cost), per-call rows, `EvidenceDetails`, `ActivityViewer`
  annotated with real event timestamps.

## 5. Security decision — provider identity

Requirement RQ-P5-* asks for provider/model "when exposable with
safety". The canonical leak gate
(`test_response_does_not_leak_provider_or_authority_internals`)
forbids the `provider` substring anywhere in the response — provider
identity is therefore **not exposable** in this contract. The
projection carries `model.id`, `model.version` and `model.owner`
(`DELPI`) instead, and the usage vocabulary is
`reported|partial|unavailable`. This is the honest reading of "safe":
the existing gate is the authority, not the requirement's phrasing.

## 6. Evidence

**Live wire (real chain, Ollama `qwen2.5:3b`, authenticated MCPs)**
`scripts/p5_observability_live_eval.py` — two full `handler.execute`
turns serialized exactly as NDJSON emits them:

- `model_calls: 4`, `governed_attempts: 2` — admission + select_group
  per attempt, each with real `duration_ms` (6.0s–15.9s) and correct
  attempt numbering; no duplicated counting.
- All calls timed out under CPU-bound Ollama → `finish_status:
  "timeout"`, token fields absent, aggregate `status: "unavailable"`,
  `total: null`. Nothing fabricated.
- `composition_mode: "deterministic"` vs `response_mode: "cri"` —
  effective vs. configured, distinct by construction.
- `model: {id: "qwen2.5:3b", version: "configured", owner: "DELPI"}`;
  `cost: {status: "unavailable"}`.
- Real-wire forbidden scan: `provider`, `instruction`,
  `system_prompt`, `chain_of_thought`, `Bearer`, `api_key` — all
  absent.

**Tests**

- Backend `test_turn_observability.py`: 21 tests — ledger bounds,
  aggregation statuses, partial/one-direction semantics, bounded
  projection, handler integration, CRI/deterministic/model modes,
  timeout counted without usage, serialization compatibility.
- Contract-gate tests updated additively (`presentation`, `runtime`
  key-set pins register `observability`; OFF/ON parity excludes the
  diagnostic block; architecture module list registers the new file
  with its justification).
- Frontend `contextPanel.test.tsx`: 12 tests — empty state, real usage
  rendering, unavailable markers, selection wiring, NDJSON parse,
  allowlist drop of unknown keys, legacy payloads.

**Regression**: full `delia-api` suite green (all pass, 3 pre-existing
skips); full `plugins/delia` suite 28 files / 334 tests green; `tsc`
clean; `vite build` + federation patch check OK.

**BROWSER_QA=TEST_NOT_RUN** — the dev portal serves the pre-change MFE
build (`delpi-delia` has no source mount) and `delpi-delia-api` mounts
the main worktree; exercising the new contract end-to-end in a browser
would require redeploying unmerged code. The live-wire probe above
covers the real serialized payload; unit/integration suites cover the
UI.

## 7. Requirements disposition

| RQ | Status | Evidence |
|---|---|---|
| P5-01 message selection | IMPLEMENTED | `moreActions` → selected turn; test |
| P5-02 details | IMPLEMENTED | Detail rows; live wire |
| P5-03 evidence | IMPLEMENTED | `EvidenceDetails` on real provenance |
| P5-04 activities | IMPLEMENTED | `ActivityViewer` + real timestamps |
| P5-05 effective CRI mode | IMPLEMENTED | `composition_mode` vs `response_mode` |
| P5-06 token consumption | IMPLEMENTED | provider-reported only; partial honest |
| P5-07 latency | IMPLEMENTED | per-call + total `duration_ms` |
| P5-08 model calls | IMPLEMENTED | stage+attempt per call, no dupes |
| P5-09 cost | IMPLEMENTED | `unavailable` — never invented |
| P5-10 security/privacy | IMPLEMENTED | leak gate holds on the real wire |
| P5-11 compatibility | IMPLEMENTED | additive key; legacy parses null |
| P5-12 visual integration | PARTIAL | plugin-ui reuse + a11y markup; BROWSER_QA not run |

## 8. Material residuals

- CPU-bound Ollama ≤3B latency inside the 60s budget still yields
  honest `PROCESSING_TIMEOUT`/timeout calls (doc 93) — the panel now
  *shows* this honestly instead of hiding it.
- Per-stage user-facing latency labels beyond raw timestamps remain a
  product decision (viewer annotates observed times only).
- Browser QA on the real portal pending a merge+deploy — UI verified
  via jsdom suites and live wire payload only.
- Provider identity stays off the wire by gate; if product later wants
  it, the canonical gate must be revisited explicitly.
- Pre-existing residuals unchanged: delegated-credential reuse mid-turn
  (doc 94), `Ori` fragment, production invoke-class evidence.

## 9. Report

```text
TASK_ID=DELIA-UX-CONTEXT-PANEL-EVIDENCE-ACTIVITY-AND-LLM-USAGE-INTEGRATION-01
PANEL_CURRENT_STATE=was render-only shell, zero props — now bound to
    real per-turn data via existing selection affordance
REUSE_DECISION=REUSE+EXTEND — no second telemetry/observability
    infrastructure
USAGE_LOSS_ROOT_CAUSE=usage/duration_ms produced at the invocation
    boundary and discarded downstream — propagation fixed, not
    instrumentation
PROVIDER_ON_WIRE=NO — canonical leak gate forbids; owner attribution
    exposed instead
TOKEN_ACCOUNTING=provider-reported verbatim; reported|partial|
    unavailable; failed calls counted, never zeroed
RETRY_ACCOUNTING=per-attempt index; replayed checkpoints never
    re-counted; live: 4 calls / 2 attempts verified
COST=unavailable — never estimated, no price table exists
PRIVACY=real-wire forbidden scan clean; bounded allowlist parse
MODEL_PROVIDER_FOR_TESTS=OLLAMA EXTERNAL_LLM_TEST_CALLS=0
BACKEND_REGRESSION=full suite green FRONTEND_REGRESSION=334/334
TYPECHECK=clean BUILD=ok FEDERATION=patch-verified
BROWSER_QA=TEST_NOT_RUN(portal serves pre-change build)
EVALUATED_SHA=b0d967614d17afd64f13a4f1ce08f535f6a99853
EVALUATED_CONFIG=dev; Ollama qwen2.5:3b; TEST_ONLY adapters in unit
    suites; budgets/recovery unchanged; PRODUCTION untouched
EXECUTOR_VERDICT=implementation+evidence returned for independent
    review; no acceptance claimed
```


## Revisão de coordenação — 2026-10-22

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (IMPLEMENTAÇÃO)**. O relatório 98 e os contratos/documentação publicados foram inspecionados; os testes de runtime são relatados pelo executor, não reexecutados independentemente neste parecer (`INDEPENDENT_RUNTIME_REEXECUTION=TEST_NOT_RUN`). Está demonstrada a implementação da ligação entre seleção da mensagem, ActivityEvent/provenance/outcome, ledger bounded de chamadas e observability no contrato aditivo de `turn_result`. Reuso de componentes do plugin-ui e do mecanismo de Model Invocation; nenhuma segunda infraestrutura de telemetry criada. Custos não inferidos e tokens apenas quando reportados; a superfície pública não inclui identidade de provider por gate canônico de vazamento.

**GATE AINDA ABERTO:** `BROWSER_QA=TEST_NOT_RUN` — sem deploy do frontend/backend integrado no host do Portal, a experiência real de seleção, troca de mensagens, streaming, acessibilidade visual e visualização dos estados de Contexto não foi provada. `PANEL_IMPLEMENTATION=ACCEPT_WITH_RESIDUAL`; `PANEL_USER_EXPERIENCE_END_TO_END=PENDING`. Registrar o QA como requisito explícito da etapa 6, com SHA/config de frontend/backend, usuário autorizado e evidência sanitizada. Não declarar integração produtiva só porque o payload passou nos testes.

**Próxima subetapa:** 5.1 aceleração GPU do Ollama local (`97-ollama-gpu-acceleration-substep-5-1-plan.md`) pode seguir agora, independentemente do browser QA, por possuir owner e escopo de infraestrutura dev separados. Não alterar produção ou budgets; medir CPU/GPU no hardware real. Posteriormente, etapa 6 homologação integrada: browser QA, CRI por turno, sequência DAVI, timeout, `Ori` como residual, e gate de revogação do token delegado antes de habilitar retry em produção. `I04_ACCEPTED=NO` sem decisão canônica posterior.
