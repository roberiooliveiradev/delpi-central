# 74 — DÉLIA Conversational Response Intelligence: finite implementation roadmap

**Date:** 2026-10-21. **Authority:** Product Master direction to avoid infinite prompts. **Status:** ROADMAP_DEFINED; individual implementation packages NOT automatically authorized. **Inputs:** [73](./73-conversational-response-intelligence-personality-product-front.md), [58](./58-adr-llm-semantic-decision-ownership.md), [67](./67-q03-independent-acceptance-and-closure.md), [72](./72-orchestration-structural-cleanup-execution-report.md), 16 and thematic documents to inventory. GitHub main observed at `3f9259d0a597c889163076645ef863ca1f5ed87b` before authoring. Future execution MUST reanchor status/HEAD, Project Instructions/.cursor and full canonical sequence.

## Objective / non-goals
Deliver answer-first, grounded task completion and documented DÉLIA personality while isolating interference via one centrally governed ON/OFF, default OFF. No new planner, rewrite of orchestration, provider branches, lexical template engine, expansion of authority, ungoverned FACT prose, phase promotion or ACT.

## Fixed sequence: five bounded packages

| Gate | Task ID | Ownership / deliverable | Required acceptance |
|---|---|---|---|
| **E0** contract/decision | `DELIA-CRI-E0-CONTRACT-AND-DECISION-01` | Architecture/coordination: full canonical reanchor; locate personality/behavior specifications; inventory existing Evidence/Outcome/synthesis, platform/Core feature control, DÉLIA config, plugin-ui shared components; prove existing equivalent and reuse decisions, owners/consumers; contract of OFF/ON, rollout and rollback; decide if explicit ADR superseding frozen selection-only is required | Concrete contracts/authority and decisions recorded, no speculative new service; unresolved rich-factual-prose contract triggers STOP/ADR rather than implicit approval |
| **E1** central switch | `DELIA-CRI-E1-CENTRAL-ONOFF-01` | Appropriate existing platform/Core owner + DÉLIA backend adapter/composition; OFF default, central authorized control, config provenance, stage correlation, fallback and disable path; tests | OFF executes old flow; ON selects only approved future path; unavailable config fails safe; no auth/data policy change; rollout/rollback behavior demonstrated, no production ON |
| **E2** task outcome | `DELIA-CRI-E2-OUTCOME-AWARE-ANSWER-01` | DÉLIA application/Evidence/Outcome existing contracts: distinguish owner technical success from task answer; empty-match vs discovery wrapper, requested count, time order and coverage, explicit insufficiency; owner-neutral and evidence-bound | TÉO latest-process only with ordering proof, DAVI one envelope vs zero hits not mislabeled, DELPI three examples, VISTA playlist, negatives; zero invented domain facts; respects ON/OFF |
| **E3** conversational presentation | `DELIA-CRI-E3-PERSONALITY-AND-GROUNDED-PRESENTATION-01` | DÉLIA presentation + existing plugin-ui shared render components: response-first, natural PT-BR, approved personality/tone, user preference, limited contextual follow-up, expandable technical evidence | ON natural and factual within **approved** synthesis contract; OFF parity; model cannot invent FACT; real examples evaluated; accessibility/compact/docked support; no generic provider-specific templates |
| **E4** live validation and closure | `DELIA-CRI-E4-REAL-EVAL-ROLLBACK-AND-ACCEPTANCE-01` | Independent coordination: bounded OFF/ON paired evaluation against fixed owner evidence and sanctioned real model/MCP environment, safety/latency, observability and rollback; document accepted SHA/config | Gated acceptance or explicit INCONCLUSIVE/REWORK with evidence; no automatic production enablement or promotion of I04/C3 |

**Dependency:** E0 precedes implementation. E1 precedes E2/E3 deployment/testing. E2 before E3. E4 only after E1–E3 evidence. If E0 cannot resolve factual-prose authority, E1/E2 may proceed ONLY under existing selection-only contract after coordination authorization; E3's factual-prose portion is blocked pending separate ADR, not silently replaced by Python templates.

## Execution economy / anti-loop policy

- Maximum **5 primary prompts**, one per gate; one independent review at each gate, **at most 1 bounded rework** per gate. No infinite microtasks, blanket audits or new packages without Product Master decision.
- For every gate: reanchor; owner/contract/consumer; `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` and `REUSE_DECISION=REUSE|EXTEND|NEW`; smallest diff; tests/evals; residual search; ledger documentation; commits/push main if authorized; independent verdict `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.
- Distinguish test outcomes `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`. Production readiness and task outcome cannot be inferred from HTTP 200 / green unit suite.
- Known screenshot baselines: TÉO most-recent process raw fields, DAVI 1 technical record + "Nenhum resultado", DELPI 3 terminals, VISTA playlist raw booleans. Use these as representative cases, not hardcoded language intent rules; evaluate generalization/negative controls.
- Protect global 30s, post-orchestration 12s, owner authorization, source provenance, security/secret policy, READ/PREPARE/ACT boundary. ON/OFF state may not be an AuthZ source.
- No redeploy or production activation implied. E4 authorizes no material writes.

```text
CRI_ROADMAP=DEFINED
CRI_E0=NEXT_SPECIFICATION
CRI_E1_E4=PLANNED_NOT_AUTHORIZED
PRIMARY_PACKAGES=5
MAX_BOUNDED_REWORK_PER_PACKAGE=1
CENTRAL_FEATURE_CONTROL=REQUIRED
DEFAULT_STATE=OFF
EXISTING_FEATURE_CONTROL=TO_INVENTORY
PERSONALITY_SPECS=TO_INVENTORY
SELECTION_ONLY=FROZEN
RICH_FACTUAL_PROSE=ARCHITECTURE_DECISION_REQUIRED
I04_ACCEPTED=NO
C3_EXECUTED=NO
```


## E0 outcome (2026-10-21)

`DELIA-CRI-E0-CONTRACT-AND-DECISION-01` executed → [75 — contracts and decisions specification](./75-cri-e0-contract-and-decision-specification.md). Resolved: central control = REUSE `Settings._env_flag` + `root_composer` single injection (`DELIA_RESPONSE_INTELLIGENCE_ENABLED`, default OFF, fail-closed, restart-dependent rollback documented); declarative resources = EXTEND the `load_declarations` JSON/whitelist/fail-closed pattern + `InstructionLineage` versioning; personality = REUSE `personality/01–04` (PERS-001..018); presentation = EXTEND `compose_presentation`; **rich-factual-prose ADR = NOT required** for E1–E4 scope (all four cases satisfiable inside frozen `selection-only`; explicit escalation clause if E4 disproves). `E0_CONTRACT_READY=YES`; implementation still requires distinct coordination authorization per gate.

## E1 outcome (2026-10-21)

`DELIA-CRI-E1-CENTRAL-ONOFF-01` executed → [76 — central ON/OFF execution report](./76-cri-e1-central-onoff-execution-report.md). Delivered exactly the E0 contract: `DELIA_RESPONSE_INTELLIGENCE_ENABLED` parsed in `Settings` (`_env_flag` vocabulary; absent/invalid → baseline + safe diagnostic), resolved once in `_compose_turn_handler` (`root_composer`), injected as typed bool into `HandleInteractiveConversationTurn` (`_response_mode` baseline|cri). ON proves boundary selection only — serialized governed results are bit-identical OFF vs ON, zero additional model calls, no E2/E3 stages, no declarative resources loaded. Observability: composition log `delia_response_intelligence mode=… config_source=… runtime_sha=…` + per-turn `stage=response_mode decision=…` (identity fields only). Rollback = env change + restart (proven off→on→off). `1713 passed, 3 skipped`; no public contract, authority, selection or presentation change. `REAL_MODEL_TEST=NOT_RUN` (E4 scope). `CRI_E1=EXECUTED`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` — awaits coordination review before E2 authorization.

## E2 outcome (2026-10-21)

`DELIA-CRI-E2-OUTCOME-AWARE-ANSWER-01` executed → [77 — outcome-aware answer execution report](./77-cri-e2-outcome-aware-answer-execution-report.md). Technical success is no longer auto-equated with task outcome: with the E1 switch ON, the governed-outcome → response binding edge runs a deterministic sufficiency assessment — new leaf module `outcome_assessment.py` (verdict vocabulary `answered|empty_result|envelope_only|insufficient`, `EvidenceFacts` from existing `extract_pagination_envelope`/`_synthesis_records`/`is_complete`, `AnswerRequirements` fail-closed parse). The SAME goal stage may now propose typed `answer_requirements` (`min_items`, `ordering`, `complete_coverage`) — hypothesis verified against owner evidence, `ADDITIONAL_MODEL_CALLS=0`. Sufficiency is marked through the existing `insufficient_evidence` limitation folded onto `outcome.limitations` (SUCCESS never rewritten; every render path carries it); verdicts logged as `stage=outcome_assessment decision=… reasons=…`. Cases A–D proven: single-record "latest" → `ordering_unproven`; envelope without business records → `envelope_only`; authoritative `total=2` vs 3 requested → `fewer_than_requested`; complete plain read → `answered`. OFF = byte-identical baseline (no stage, no requirement consumption, baseline prompts). No new flag system, planner, registry or public DTO; the requirements clause extends the existing Python-resident instruction family (versioned via `InstructionLineage` content hash — migrating that family to JSON was already out of roadmap scope). `1756 passed, 3 skipped` (+43). `REAL_MODEL_EVALUATION=NOT_RUN` (E4). `CRI_E2=EXECUTED`, `I04_ACCEPTED=NO`, `C3_EXECUTED=NO` — awaits coordination review before E3 authorization.

## Foundational implementation convention — versioned text/instruction resources

Product Master requires new CRI code from E0 to separate behavioral instructions, long prompt text and user-facing prose resources from Python flow implementation. See [73 §9](./73-conversational-response-intelligence-personality-product-front.md). **E0 acceptance adds an inventory** of existing instruction ID/lineage, declarative resource format/loader, JSON/schema conventions, personality specs, copy/localization and governance. Prefer versioned JSON resources **where existing legitimate contracts support them**; reuse existing canonical formats, do not create competing registries. E1 must preserve centralized ON/OFF and record effective resource version; E2/E3 consume approved resources without embedding long instruction prose inside Python/TypeScript; E4 checks versioned configuration, OFF parity, invalid-resource fail-closed and provenance/security tests. Existing orchestration.py textual migration is outside this roadmap; no code authorized by this documentary decision.
