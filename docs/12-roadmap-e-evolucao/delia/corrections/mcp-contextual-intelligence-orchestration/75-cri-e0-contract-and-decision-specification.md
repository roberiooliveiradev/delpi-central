# 75 — CRI E0: contracts and architecture decisions specification

**TASK_ID:** `DELIA-CRI-E0-CONTRACT-AND-DECISION-01`
**Date:** 2026-10-21
**Mode:** `REANCHOR → TARGETED INVENTORY → REUSE GATE → PRODUCT CONTRACTS → ARCHITECTURE DECISION → FINITE IMPLEMENTATION BRIEF → DOCUMENT → COMMIT → PUSH MAIN → REPORT`
**Type:** specification and decision closure. **Runtime implementation is NOT authorized by this document.** Inputs: [73](./73-conversational-response-intelligence-personality-product-front.md), [74](./74-conversational-response-intelligence-finite-implementation-roadmap.md), [58](./58-adr-llm-semantic-decision-ownership.md), [67](./67-q03-independent-acceptance-and-closure.md), [72](./72-orchestration-structural-cleanup-execution-report.md).

## 1. Reanchor record

- Execution worktree: detached at `origin/main` → fast-forwarded to `3c0484ec28c09b9b9e07ca6e2fb13288c8138b12` at task start. Concurrent work preserved: api-delpi R03/P7 stock-inventory scope, controllership-finance plugin, integrations homologation docs — none touched.
- Canonical order revalidated: `16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02-arquitetura → 24-product-spec → personality/01–04 → ledger` (tail §6.344–§6.348).
- Working documents read in full: 73 (front + §7 central ON/OFF + §9 declarative resources), 74 (five-gate roadmap), 58 (ADR — frozen selection-only), 72 (structural cleanup evidence), plus targeted code inventory below. No third general audit performed.

## 2. Targeted inventory — proven existing contracts

### 2.1 Personality and behavior — `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=REUSE`

Canonical product specs exist and are approved:

- `docs/12-roadmap-e-evolucao/delia/personality/01-identity-and-temperament.md` — archetype, temperament.
- `…/personality/02-behavior-and-interaction.md` — full behavioral baseline: voice, answer-first structure, initiative gates (PERS-010/014/015/016/017), humor/emoji policy, disagreement/repair, situational adaptation, non-negotiables.
- `…/personality/03-decision-record.md` — `PERS-001..018` `APPROVED_PRODUCT_DIRECTION` (Product Master, 2026-10-10).
- `…/personality/04-behavioral-quality-evaluation.md` + `README.md` — eval scenarios, precedence over other docs.
- State: `PRODUCT_BEHAVIOR_BASELINE=APPROVED_PRODUCT_DIRECTION`, `RUNTIME_IMPLEMENTATION=NOT_PROVEN`. **Owner:** product/editorial docs (Product Master decision), consumed today only by `DELIA_INTERACTION_INSTRUCTION` v5 voice block (`delia-api/app/application/interaction/instruction.py`), which reaches only the non-governed conversational path — the proven structural gap (C3 doc 04, gap 8).

**Behavioral contract for E3:** personality is a *communication policy* — it tunes style/tone/initiative of presentation, never grants FACT, authorization, memory persistence, or ACT. User preferences may narrow allowed style within the approved baseline (PERS-015: temporary by default; permanence only via confirmed legitimate mechanism).

### 2.2 Central ON/OFF — `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=REUSE`

- **Mechanism:** `delia-api/app/infrastructure/config/settings.py` — env-backed `Settings` with `_env_flag(name, default=False)`, resolved once at composition in `delia-api/app/composition/root_composer.py`, injected as typed constructor/config dependencies. Precedents: `DELIA_MCP_{DAVI,TEO,VISTA}_ENABLED`, `DELIA_OPENAPI_DELPI_ENABLED`, `DELIA_MODEL_STAGE_TIMEOUT_SECONDS`. Precedents are resolved centrally at composition and passed down — not scattered reads.
- **No separate platform feature-flag service** exists in the repo inventory (`TO_INVENTORY` exhausted: no flag service, no Core toggle API in docs). Inventing one is prohibited by 73 §7.
- **Owner:** `delia-api` Settings + composition (application config boundary); Core remains AuthZ/governance authority — the flag is a behavior switch, never a permission.
- **Contract for E1:** one new setting `DELIA_RESPONSE_INTELLIGENCE_ENABLED` (default `false`, fail-closed), resolved **once** in `root_composer` into a typed `ResponseIntelligenceMode` (or equivalent single value) passed to the governed turn path. ON/OFF is resolved at process start from trusted config only — never from user input, model output, provider metadata, or frontend state.
- **OFF baseline:** bit-identical current flow — same `attempt(...)` path, same statuses, same `compose_presentation` output, same deterministic renderers. The switch chooses between the existing response-mode implementation and the new CRI one at exactly one composition boundary.
- **Rollback:** env change + service restart (same as existing flags). **No hot-toggle contract exists** — E1 must document restart-dependent disable and treat it as an acceptance gate, per 73 §7.
- **Invalid state:** unparseable/missing value → `False` (fail-closed), warning log without sensitive data — consistent with `_env_flag` + `build_openapi_source` conventions.
- **Observability:** resolved state + config provenance logged at startup (existing `_logger` conventions); per-turn `response_mode` marker in stage logs with `correlation_id` (existing stage-log format: `stage=… decision=… correlation_id=…`). No secrets, no payload, no model reasoning.

### 2.3 Evidence / Outcome / grounded synthesis — `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=REUSE|EXTEND`

- `app/domain/specialist_interop/model.py` → `SpecialistOutcome` (status, provenance, `content_text`, `is_complete`, `structured`, `limitations`, `epistemic_class=OBSERVATION` pinned).
- `app/application/interaction/capability_attempt.py` → `GovernedCapabilityAttempt`/`GovernedCapabilityStatus` (`SUCCESS|NOT_APPLICABLE|SOURCE_UNAVAILABLE|AUTHZ_DENIED|CONFIRMATION_REQUIRED|WRITE_REJECTED|CLARIFICATION_REQUIRED`), `EARLY_CONVERSATIONAL_ADMISSION`.
- `app/application/interaction/contracts.py` → `InteractiveTurnResult` (`grounding_status`, `provenance`, `message_kind`, `owner_hint`, `limitations`, `epistemic_class`, `confirmation_request`); `is_fact()`/`authorizes_act()` pinned False.
- `orchestration.py` → typed `goal` proposal (`prior_evidence_sufficient`, `comparison_requested`), `SYNTHESIS_INSTRUCTION_ID` (selection-only: `items[{record_index, fields}]`), `_render_synthesis`, `_compose_answer`, `_deterministic_guidance_content`, `EMPTY_RESULT_TEXT`, `_sanitize_renderable`, count/`has_more` semantics; `paginated_result_semantics.py` (B1 — frozen, untouched).
- **Gap for E2 (proven by doc 73 evidence, not new audit):** nothing today distinguishes *owner-technical-envelope success* from *business-result answered* (DAVI case), nor validates requested count/ordering/scope against owner facts (TÉO "último" case). This is a bounded *outcome-assessment* extension over existing `SpecialistOutcome`/`limitations`/`structured` — `EXTEND`, not a new engine.
- **Gap for E3:** `compose_presentation` (`presentation.py`, contract `version: "1"`, closed block allowlist `text|notice`, `_ALLOWED_INTERACTIONS_BY_KIND`) is the sole response-shaping contract reaching the MFE; answer-first/evidence/follow-up blocks extend this versioned contract — `EXTEND`.

### 2.4 Declarative versioned resources — `EXISTING_EQUIVALENT=YES` (pattern + versioning contract), `REUSE_DECISION=EXTEND`

- **Versioning contract:** `InstructionLineage(instruction_id, version, content_hash=sha256)` (`domain/model_invocation/model.py`) — stable ID, explicit version, content hash; proven in production via `SELECTION_INSTRUCTION_VERSION="12"`, `INSTRUCTION_VERSION="5"`.
- **File-loader pattern:** `app/infrastructure/openapi/source_loader.py` → `load_declarations(path)`: versioned governed JSON reviewed in Git, strict key whitelisting (`_DECLARATION_KEYS`), bounded size (`MAX_DECLARATIONS`), fail-closed `openapi_declarations_invalid`, loaded once at composition, absence/invalid → capability absent + warning log (no sensitive data).
- **No JSON instruction/content loader exists in delia-api today.** Instruction text lives in Python constants (e.g., `DELIA_INTERACTION_INSTRUCTION`). Doc 73 §9 explicitly excludes migrating legacy strings; the new CRI resources follow the `load_declarations` shape: JSON file in repo → schema/whitelist validation → typed dataclass → injected at composition → version+sha256 recorded into lineage/log provenance → invalid/missing fails closed to the OFF/baseline path.
- **Content boundary:** resources carry presentation labels, instruction text, behavior directives and message templates — never policy, AuthZ, domain rules, secrets, or executable code. Model-facing instruction resources stay hypothesis-inputs, never authority.
- `JSON_SCHEMA_STANDARD=` strict whitelist + typed projection (the `load_declarations` convention); no external schema-lib dependency required.

### 2.5 Frontend shared components — `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=REUSE`

- `plugins/delia/src/api/presentation.ts` — parse-only adapter for the backend `presentation` contract (v1 emitted; v2 `markdown_safe` reader-ready, producer not implemented). Unknown kinds/versions degrade to neutral. The single legitimate channel for E3 output.
- `plugins/plugin-ui/src/components/conversation/` — `EvidenceDetails.tsx` (spec doc 80), `ConversationAssistantActions.tsx` (spec doc 92 — follow-up offers), `ConversationStatus`, `ConversationError` (doc 78), `MessageActionBar`.
- `plugins/plugin-ui/src/components/markdown/` — `ConversationMarkdown`/`MarkdownDocument` (docs 83–91 contract); `data/DataRecordCard.tsx`; styles for evidence/data-cards already exist.
- **Rule:** backend emits governed blocks; MFE/plugin-ui render-only; frontend never becomes authority over ON/OFF, authorization, or policy. No new component family — extend only if an existing component's contract proves insufficient (`TO_INVENTORY` during E3 diff).

## 3. Contract matrix (required §9 delivery)

| Capability | Existing equivalent | Reuse decision | Owner | Contract | Destination |
|---|---|---|---|---|---|
| Central ON/OFF | YES — `Settings._env_flag` + `root_composer` injection (`DELIA_*_ENABLED` precedent) | REUSE | delia-api Settings/composition | env `DELIA_RESPONSE_INTELLIGENCE_ENABLED` default OFF → one typed mode resolved at composition | E1 |
| Outcome-aware answer | YES→EXTEND — `SpecialistOutcome`, `GovernedCapabilityAttempt`, statuses, `limitations`, `structured`, `is_complete`, count/`has_more` semantics | EXTEND | delia-api application (orchestration) | outcome-assessment over existing outcome/projection contracts; new `limitations`/status vocab additions only where typed | E2 |
| Grounded synthesis | YES — `SYNTHESIS_INSTRUCTION_ID` selection-only + deterministic projections | REUSE (frozen ADR 58) | orchestration + deterministic renderers | unchanged selection contract; presentation enriched below it | E2/E3 |
| Versioned instructions/text | PARTIAL→YES — `InstructionLineage` + `load_declarations` loader pattern | EXTEND | delia-api infrastructure loader + application consumers | JSON resource contract §4 below | E2/E3 (+E1 OFF fallback) |
| Personality | YES — `personality/01–04`, PERS-001..018 | REUSE | product docs → declarative resource projection | behavioral directives as versioned resource content; never authority | E1/E3 |
| Presentation channel | YES — `compose_presentation` v1 + parse-only MFE adapter | EXTEND | delia-api `presentation.py` + plugins/delia adapter | new bounded block kinds under closed allowlist; version bump only if shape changes | E3 |
| Frontend components | YES — `EvidenceDetails`, `ConversationAssistantActions`, `ConversationMarkdown`, `DataRecordCard`, `ConversationStatus/Error` | REUSE | plugin-ui + plugins/delia | existing component props/contracts | E3 |
| Observability | YES — structured `_logger` stage lines, `correlation_id`, `turn_budget` timings | REUSE | delia-api observability convention | `response_mode`, resource version+hash, path markers in stage logs | E1/E4 |

## 4. New contract specifications

### 4.1 `DELIA_RESPONSE_INTELLIGENCE_ENABLED` (E1)

- **Owner/consumer:** `Settings` (infrastructure config) → `root_composer` (composition) → single injection point in the governed turn path. Consumers never read env directly.
- **Type/values:** boolean via existing `_env_flag`; default `False`. Any non-allowlisted value → `False`.
- **Semantics:** `OFF` = today's flow byte-for-byte (same orchestrator instance behavior, same `compose_presentation` output). `ON` = CRI response path engaged at the governed outcome→response boundary; orchestration selection, owner invocation, AuthZ, budgets, PREPARE/ACT unchanged.
- **Errors/fallback:** absent/invalid → OFF + warning log. Missing CRI resources under ON → fail closed to OFF-equivalent deterministic rendering (never a bare exception to the user).
- **Observability:** `response_mode=cri|baseline` + resolved config version in turn/stage logs; startup log of resolved state.
- **Tests required (E1):** OFF parity on fixed corpus (identical attempt content/limitations/statuses); ON engages new path only; invalid env fails closed; no AuthZ/evidence/ACT difference OFF↔ON; rollback = env flip + restart documented.
- **Compatibility:** additive constructor/config param; no public DTO/route change.

### 4.2 `delia_response_intelligence` declarative resources (E2/E3)

- **Shape (JSON, reviewed in Git):** `{"resource_id": str, "version": str, "owner": "delia-api", "kind": "instruction|labels|directives|templates", "entries": [...]}` — strict key whitelist, bounded sizes, fail-closed errors (`response_resource_invalid`).
- **Loader:** bounded module in `app/infrastructure/` mirroring `load_declarations` (read → parse → whitelist → typed dataclass → tuple). Loaded once at composition; consumers receive immutable typed objects.
- **Lineage:** resource `resource_id`+`version`+`sha256(content)` recorded into `InstructionLineage`-compatible provenance and stage logs; model-facing instruction content hashed exactly as today.
- **Kinds:** `instruction` (model-facing, e.g., response-assessment instruction for E2 — still hypothesis input), `labels`/`templates` (presentation vocabulary, PT-BR), `directives` (personality-to-presentation mapping, e.g., boolean→label renderings, answer-first ordering rules — presentation metadata, not logic).
- **Trust boundary:** resource content is build-time-reviewed data; it cannot carry AuthZ, domain rules, secrets, or free-form factual prose authority. Missing/invalid under ON → fail-closed to baseline render.
- **Compatibility/versioning:** `version` field + sha256 observability; adding keys = whitelist extension + tests; consumers reject unknown kinds/versions.

### 4.3 Presentation contract extension (E3)

- Extend `compose_presentation` under its existing versioning discipline: new candidate block kinds (e.g., `evidence` — provenance fields projection; `suggestions` — bounded next-step offers) are **emit-only, closed-allowlist, typed**, and v2-reader compatible. MFE adapter already drops unknown kinds — safe additive evolution; bump `PRESENTATION_CONTRACT_VERSION` if any existing field shape changes.
- Answer-first ordering (lead content block → optional detail/evidence → optional suggestion) is a *projection ordering*, built solely from `InteractiveTurnResult`/`GovernedCapabilityAttempt` fields already governed.

## 5. Architecture decision — factual prose vs frozen `selection-only`

**Decision: `RICH_FACTUAL_PROSE_ADR_REQUIRED=NO` for the E1–E4 scope.**

Rationale: every product case in doc 73 is satisfiable inside the frozen contract:

| Case | Required behavior | Achieved by (no new authority) |
|---|---|---|
| TÉO "último processo" | Lead with the found record; claim "latest" **only** when owner order/universe is proven | E2 outcome-assessment (ordering/count vs owner metadata) + E3 answer-first projection of selected evidence fields |
| DAVI "3 exemplos" → envelope | Distinguish 1 technical record from 0 business results | E2 envelope-vs-result typing on `SpecialistOutcome.structured`/status |
| API DELPI "3 exemplos grupo 1008" | Natural presentation of real items | E3 presentation labels/templates over selected fields |
| VISTA playlists | Organized summary, no raw booleans | E3 declarative label mapping + expandable technical detail (`EvidenceDetails`) |

The frozen boundary that remains: the model **never authors enterprise factual assertions**. Model output stays a *hypothesis* (selection/organization/assessment proposals) revalidated against owner evidence; phrasing of facts comes from deterministic projections + versioned templates/labels — presentation of owner data, not model-authored fact. This is the same epistemic line ADR 58 drew; nothing in E2/E3 crosses it.

**Escalation clause:** if E4 paired OFF/ON evidence proves the acceptance criteria cannot be met without model-authored factual prose, the work **stops** at `ARCHITECTURE_DECISION_REQUIRED` and a dedicated ADR is prepared — it is never silently replaced by keyword/Python templates (73 §4).

`SELECTION_ONLY_PRESERVED=YES` — ADR 58 untouched.

## 6. E1–E4 implementation briefs

### E1 — `DELIA-CRI-E1-CENTRAL-ONOFF-01`
- **Files (planned):** `settings.py` (1 flag), `root_composer.py` (single resolution/injection), governed turn path constructor (typed mode param), tests.
- **Contract:** §4.1. Default OFF; OFF parity proven on the fixed corpus; ON selects only the approved CRI path; fail-closed; `response_mode` + config version in logs; rollback = env + restart (documented, not instant).
- **Tests:** parity OFF; engagement ON; invalid-state fail-closed; auth/evidence/budgets unchanged.

### E2 — `DELIA-CRI-E2-OUTCOME-AWARE-ANSWER-01`
- **Contracts reused:** `SpecialistOutcome`, `GovernedCapabilityAttempt`, statuses/limitations, `structured`, count/`has_more`, `goal` typed proposals.
- **Scope:** bounded outcome-assessment (existing stage mechanics via `_model_stage_proposal` + new instruction resource §4.2) that classifies: `answered | empty_result | envelope_only | insufficient | unavailable`; validates requested count/ordering/scope against owner metadata (`is_complete`, totals, ordering declarations) — never asserting "latest/top/all" without proof; emits typed insufficiency instead of misleading dumps.
- **Tests:** TÉO ordering case (claim only with proof), DAVI envelope-vs-result, DELPI 3-example, VISTA list, negatives (fabricated data resistance, owner failure, conflicting counts), OFF parity.

### E3 — `DELIA-CRI-E3-PERSONALITY-AND-GROUNDED-PRESENTATION-01`
- **Contracts reused:** `compose_presentation` (EXTEND, §4.3), `DeliaAssistantMessage`/plugin-ui components (REUSE), personality docs 01–04 → declarative `directives`/`labels`/`templates` resources (§4.2).
- **Scope:** answer-first block ordering; descriptive labels for field names; booleans→domain vocabulary via resource mapping; raw identifiers/JSON into expandable evidence (existing `EvidenceDetails`); bounded single follow-up offer via `ConversationAssistantActions` vocabulary; PERS-010/014/016 initiative gates = presentation policy only.
- **Tests:** factual fidelity (every asserted fact traced to owner field), OFF parity, unknown-kind drop, no model-authored fact, accessibility/responsive, injection/fake-evidence negatives.

### E4 — `DELIA-CRI-E4-REAL-EVAL-ROLLBACK-AND-ACCEPTANCE-01`
- **Scope:** paired OFF/ON runs on the four doc-73 cases + generalization/negatives, fixed SHA/config/model; metrics = task outcome, grounding fidelity, latency (30s/12s preserved), safety negatives, `response_mode` provenance in logs; rollback demonstration (env flip + restart).
- **Acceptance:** independent verdict `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`; HTTP 200 / owner counts ≠ PASS; `REAL_MODEL_EVAL=TEST_NOT_RUN` without authorized credentials.

## 7. Frozen state and boundaries — verified unchanged

`Q01_Q03=CLOSED_WITH_RESIDUAL`, `B1=UNRESOLVED_FORMALLY_DEFERRED` (untouched), `I04_ACCEPTED=NO`, `C3_EXECUTED=NO`, `SELECTION_ONLY_FACTUAL_SYNTHESIS=FROZEN`, budgets 30s/12s, `MATERIAL_ACT=NOT_AUTHORIZED`, `PRODUCTION_DEPLOY=NOT_AUTHORIZED`. No public DTO, port, route, or `InteractiveTurnResult`/`compose_presentation` field changed in this task (docs only). No provider-specific branches, no new planner/engine/registry, no second feature-flag system, no legacy-string migration.

## 8. Residuals and blockers

- **BLOCKERS:** none for E1 start; E3 factual-prose escalation clause recorded (§5).
- **NON_BLOCKING_RESIDUALS:** (a) rollback is restart-dependent — accepted gate, documented; (b) real-model evidence pending authorized environment (`TEST_NOT_RUN`); (c) `TO_INVENTORY` item: whether any plugin-ui component gap surfaces during E3 diff (evaluated at implementation, not spec).
- **ARCHITECTURE_DECISION_REQUIRED:** none open — the prose question is decided for scope (§5) with an explicit future escalation path.

```text
E0_CONTRACT_READY=YES
FEATURE_CONTROL=REUSE_SETTINGS_COMPOSITION
DECLARATIVE_RESOURCES=EXTEND_LOAD_DECLARATIONS_PATTERN
PERSONALITY_SPECS=personality/01-04_APPROVED
RICH_FACTUAL_PROSE_ADR=NOT_REQUIRED_CURRENT_SCOPE
SELECTION_ONLY=PRESERVED
RUNTIME_CODE_CHANGED=NO
NEXT=COORDINATION_ACCEPTANCE_THEN_E1
```
