# 229 — DÉLIA · Systemic intelligence-flow architecture audit

**TASK_ID:** `DELIA-C3-INTELLIGENCE-FLOW-SYSTEMIC-ARCHITECTURE-AUDIT-01`  
**Date:** 2026-11-04  
**Audit HEAD (reanchor):** `7d5b3667fd` (task OBSERVED_HEAD `0d18a76bbf` is ancestor)  
**PRODUCT_CODE_CHANGED:** NO  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**STATUS:** AUDIT_COMPLETE — recommendations for coordination only

---

## 1. Executive findings

1. **PROVEN:** Interactive turns always enter governed capability orchestration first (`HandleInteractiveConversationTurn` → `OperationalCapabilityOrchestrator.attempt`); CRI is a response-mode marker, not a separate planner.
2. **PROVEN:** There are **≥20** distinct governed LLM instruction purposes in `orchestration_instructions.delpi.json`, invoked via a shared `_propose` / Pydantic AI port with env-bounded retries (`DELIA_LLM_CALL_MAX_ATTEMPTS`, observed 3 in homologation).
3. **PARTIALLY_PROVEN:** Semantic fragmentation (admission → turn_goal → subobjectives → **per-sub** turn_goal classify → select_group → select_capability → arguments → …) multiplies model calls before the first successful owner READ. Live E4-R6 compares routinely spent **~175–300s** with `material_satisfied=0`.
4. **PROVEN (doc 226 conflict with runtime):** Frozen decision “use semantic decisions once; execute validated tasks deterministically” is only **partially realized**. Compare paths still re-call `turn_goal` per subobjective inside `_acquisition_subobjectives` and re-run full owner selection per sub.
5. **PROVEN:** RC-A acquisition-time obligation preservation (§20) works live (`preserve_material_dependency`); it does **not** fix owner selection (RC-B) or discovery-first (RC-C).
6. **PROVEN:** Simple conceptual ask (“O que é SIPOC?”) can still burn a large slice of the turn budget (client timeout ~90s observed) even when admission later marks `conversational/explanation` — proportional FAST path is **not reliably short** under current model latency.
7. **PROVEN:** Unavailable/misbound owner paths fail closed to `NON_GROUNDED` / `delpi_source_unverified` (E06 probe) — security posture intact; functional compare oracle still NOT_REACHED.
8. **CAUSAL HYPOTHESIS** (“fragmentation of semantic decisions drives errors/retries/latency”): **PARTIALLY_PROVEN** — strong for latency and reclassification volume; owner-selection errors (TÉO vs DAVI) and discovery dead-ends remain **independent** first-failure points (RC-B/C).

---

## 2. Documentation reanchor

| Item | Value |
|---|---|
| DOCUMENTATION_REANCHOR | docs 16, 50, 49/ADR58, 219–228, ledger; code HEAD `7d5b3667fd` |
| AUTHORITIES_READ | 16 execution master; 50 standalone; ADR 58 LLM ownership; 221–226 typed-goal / reuse once; 228 §§12–20 RC-A |
| DECISIONS_REVALIDATED | LLM=semantic proposal; Domain/Core=authority; no Chat runtime dependency; §6.145 no model factual prose; RC-A evidence_needed preservation |
| EXECUTION_DRIFT | Doc 226 “semantic once / deterministic READ obligations” vs runtime still decomposing+reclassifying every compare sub (**DRIFT_PARTIAL**) |
| CP_RQ | E4-R6 intelligence flow; RC-A IMPLEMENTED; RC-B/C/REF05 OPEN |

```text
EXISTING_EQUIVALENT=YES (orchestrator, SubObjectiveTracker, Pydantic AI port, VerifiedCompositeEvidence)
REUSE_DECISION=EXTEND (recommendation only — no product change this task)
ABSTRACTION_GATE=PASS (no new planner proposed as mandatory)
PHASE_ALLOWED=AUDIT_ONLY
```

---

## 3. Architecture baseline (runtime)

```text
HTTP POST /interaction/turns
  → auth (JWT + Core /me)
  → HandleInteractiveConversationTurn.execute
       response_mode = cri|baseline
  → OperationalCapabilityOrchestrator.attempt
       → _admit_conversational_turn          [LLM: interaction_admission]
       → branch: surface_inquiry | conversational NOT_APPLICABLE | _governed_owner_path
  → _governed_owner_path
       → live groups/surface
       → optional _understand_goal           [LLM: turn_goal] (when prior_turns)
       → optional prior_continuation
       → depth==0: _decomposed_investigation [LLM: subobjectives]
            → _acquisition_subobjectives     [LLM: turn_goal × N subs]
            → per sub: _governed_owner_path(depth>0)
                 select_group / select_capability / arguments / invoke / assess …
            → evidence_composition gate + optional composition [LLM]
  → interaction grounding / deterministic terminals / conversational fallback [LLM]
  → JSON or NDJSON turn_result
```

Engine note: homologation logs show **both** `app.infrastructure.orchestration.langgraph_engine` and `capability_provision.orchestration` emitting `interaction_admission` — dual sequencing surfaces sharing the same admission contract (**TO_INVENTORY** ownership clarity; not changed here).

**PROVEN (call-graph audit):** `select_decision_path` / labels FAST·OPERATIONAL·REASONING are **post-plan telemetry only** — they do **not** skip selection or LLM stages. Real control branches are admission class, `path_mode` (native/corroborate/enrichment), `comparison_requested`, and interaction status dispatch.

| Runtime branch | Trigger | Typical LLM |
|---|---|---|
| Early conversational | admission `requires_owner_surface=false` | admission + optional free-form fallback (`delia.interaction.turn`) |
| Surface inquiry | admission `surface_inquiry` | admission; answer = live surface projection |
| Owner / compare | admission owner required or fallthrough | full orchestration stack |
| Complex investigation (real) | `path_mode != native` **or** `comparison_requested` | decomposition, foreign/corroborate, multi-source |

---

## 4. End-to-end call graph (ordered stages)

| STAGE_ID | Responsibility | Owner | Key surface | LLM |
|---|---|---|---|---|
| S00 | AuthN/AuthZ | Core + delia-api middleware | `auth_middleware`, Core `/me` | No |
| S01 | Interaction session/turn | Application | `handle_interactive_turn.py` | No |
| S02 | Interaction admission | Orchestration | `_admit_conversational_turn` | **Yes** `interaction_admission` |
| S03 | Live capability surface | Adapters + Application | `_groups`, MCP/OpenAPI list | No (network) |
| S04 | Parent goal understanding | Orchestration | `_understand_goal` | **Yes** `turn_goal` |
| S05 | Prior continuation | Orchestration | `_prior_continuation_attempt` | **Yes** synthesis/continuity |
| S06 | Decomposition | Orchestration | `_decompose_objective` | **Yes** `subobjectives` |
| S07 | Acquisition filter | Orchestration | `_acquisition_subobjectives` | **Yes** `turn_goal` per sub |
| S08 | Sub investigation | Orchestration + tracker | `_investigate_subobjectives` | Cascades S09–S14 |
| S09 | Group selection | Orchestration | select_group | **Yes** |
| S10 | Capability selection | Orchestration | select_capability / `#with_goal` | **Yes** |
| S11 | Arguments | Orchestration | arguments / candidate_arguments | **Yes** |
| S12 | Discovery / candidate | Orchestration + MCP | discover → candidate_token | Mix |
| S13 | Owner execute | Provider adapter | MCP/OpenAPI invoke | No (tool) |
| S14 | Native/foreign assess | Orchestration | native_assessment, relevance | **Yes** |
| S15 | Evidence obligation + composition | Orchestration | eligibility + `evidence_composition` | Optional LLM |
| S16 | Grounding / presentation | Interaction | `_grounded_*`, `compose_presentation` | No (deterministic terminals) |
| S17 | Conversational fallback | Interaction | model invoke | **Yes** free-form |
| S18 | Delivery | HTTP/NDJSON | `interaction_routes` | No |

---

## 5. LLM call matrix (instruction catalog)

Sources: `orchestration_instructions.delpi.json` (**20** catalog keys) + runtime inventory (**21** orchestration purposes including fused `select_capability#with_goal`) + conversational fallback `delia.interaction.turn`. Hub: `_model_stage_proposal` → `InvokeModel.execute`; optional `DELIA_ARGGEN_ENGINE=pydantic_ai` bypasses InvokeModel for candidate args only.

| Instruction / purpose | Class (audit) | New information? | Often redundant? | Verify how |
|---|---|---|---|---|
| `interaction_admission` | ESSENTIAL_SEMANTIC_REASONING | owner vs conversational | Cascades with GRP “needs owner?” | Typed fields + fail-closed |
| `turn_goal` | ESSENTIAL / **REDUNDANT_REINTERPRETATION** when repeated per sub | goal_class, comparison, answer_requirements | **Yes** on every acquisition sub (+ prior_turns path) | Declared schema |
| `select_capability#with_goal` | USEFUL (fusion reduces separate GOAL) | capability + goal | Still followed by per-sub GOAL classify | Schema |
| `subobjectives` | USEFUL_CONTEXTUAL_REASONING | plan + evidence_needed | Over-fires on simple compare | Fail-closed validate |
| `select_group` | USEFUL_CONTEXTUAL_REASONING | group id | Per-sub repeat; overlaps ADM intent | Live catalog only |
| `select_capability` | USEFUL_CONTEXTUAL_REASONING | remote name | Per-sub + retry | Schema + dead-end |
| `arguments` / `candidate_arguments` | USEFUL / dual projectors | args | **Alto** ARGS↔CAND_ARGS (+ pydantic path) | Schema validate |
| `index_probe` / `index_select` | USEFUL | index membership | Path-specific | Exact declared ids |
| `native_assessment` / `goal_evidence_relevance` | ESSENTIAL_SEMANTIC_REASONING | correspondence | REL can reopen GRP/CAP/ARGS | Typed verdict + ledger reuse |
| `foreign_selection` | USEFUL | alternate owner | Risk of wrong specialist | Catalog+policy |
| `comparison` vs `evidence_composition` | USEFUL | pairing / multi-evidence | **Dois** comparadores tipados | Deterministic verifier |
| `grounded_synthesis` (prior vs outcome) | USEFUL | transform / record select | Same purpose, two contexts | Epistemic gates |
| Free-form `delia.interaction.turn` | UNVERIFIED if after owner miss | prose | Blocked when OWNER_PATH_UNBOUND | Deterministic messages preferred |

Retry: `call_retry_eligible` ≤3 per logical call (TIMEOUT / PROVIDER_UNAVAILABLE / INVALID_STRUCTURED_OUTPUT); `DELIA_LLM_CALL_MAX_ATTEMPTS` default 1, homologation often 3 — **amplifies** fragmentation. Plus stage-level re-`_propose` loops and `MAX_GOVERNED_ATTEMPTS=2` turn resume.

**Material redundancies (PROVEN inventory):** ADM↔GRP; GOAL×N after fused CAP+GOAL; ARGS↔CAND_ARGS; SYN_PRIOR↔SYN_OUT; CMP↔EVID_COMP; NAT+REL recovery reopening selection.

---

## 6. Context propagation analysis

| Artifact | Produced | Consumed later? | Loss risk |
|---|---|---|---|
| Parent `_TurnGoal` | S04 | Decomposition block may copy `comparison_requested` | Sub path may **not** reuse parent class; re-infers via S07 |
| `SubObjective.goal` text | S06 | Owner selection prompts | Free-text only; targets not typed refs |
| `evidence_needed` | S06 | S07 coverage vs sibling strings | Exact string match; omit → false auxiliary |
| `dependencies` | S06 | Tracker scheduling | Dropped deps rewritten when auxiliaries delegated |
| Prior OBSERVATION turns | Client context | Continuity / referent | Untrusted; depth>0 cannot conclude from history |
| Discovery candidates | S12 | Execute binding | Candidate-bound dead-ends if skipped (RC-C) |
| `VerifiedCompositeEvidence` | S15 | Interaction grounding | Never reached if material_satisfied=0 |

**Finding:** Parent semantic decisions are **not** stably threaded as typed obligations into sub execution — primarily **text + fresh LLM**. Aligns with doc 226 intent but not full implementation (**DRIFT_PARTIAL**).

---

## 7. Evidence obligation flow (RC-A)

```text
evidence_needed (declared in decomposition)
  → _acquisition_subobjectives coverage vs sibling evidence_needed
  → tracker material set
  → owner attempts
  → eligibility (no eligibility-time demotion; §19)
  → VerifiedCompositeEvidence
```

| Question | Answer | Confidence |
|---|---|---|
| Declared vs validated need? | **Declared** by model; validated only as structured strings | PROVEN |
| Who decides necessity? | Decomposition LLM (+ fail-closed keep if undeclared class) | PROVEN |
| Detect omitted dependency? | **Not reliably** if `evidence_needed` empty | PROVEN residual |
| AnswerRequirements help? | Different concern (sufficiency of answer shape) — **not** source obligations | PROVEN |
| Sibling share by trust link? | Exact `evidence_needed` string match only | PROVEN |
| Coverage of acquired vs planned? | Planned sibling declarations at filter time | PROVEN |
| Eligibility vs original objective? | Material tracker coverage + two roots; REF05 target oracle still open | PARTIALLY_PROVEN |

---

## 8. Owner/capability selection (RC-B)

**Status:** OPEN / NOT_PASS (functional).

Live and diagnostic history: free-text sub goals can select wrong group (e.g. TÉO) for product-structure READs that belong on DAVI/Domain. Causes under inventory:

- weak parent→sub typed target binding;
- group descriptions / retrieval ranking;
- per-sub reselection without sticky parent owner;
- foreign_selection paths.

**Not** fixable by specialist hardcode (forbidden). Needs semantic catalog + typed obligations reuse (Option B).

---

## 9. Discovery-first (RC-C)

**Status:** OPEN / NOT_PROVEN closed.

Candidate-bound execute without discover is a typed dead-end (`_capability_dead_end` / `_is_candidate_bound`). Live failures include `invalid_structured_output` on arguments and empty material_satisfied. LLM is still asked to drive protocol-shaped steps that adapters partially own — **PARTIALLY_PROVEN** “model doing provider mechanics”.

---

## 10. Composition / grounding / REF05

| Item | Status |
|---|---|
| VerifiedCompositeEvidence separate from SpecialistOutcome | PROVEN implemented |
| No model factual prose in composition (§6.145) | PROVEN intent + verifier |
| False GROUNDED after RC-A §19–§20 | PROVEN absent in executed adversarial + live sets |
| Target-set oracle REF05 | NOT_PASS / OPEN |
| Fan-in when material_satisfied=0 | Correct refusal | PROVEN live |

---

## 11. Latency and tokens

| Scenario | Source | Latency | Tokens | Notes |
|---|---|---|---|---|
| E4-R6 compare NDJSON | prior live §19/§20 | ~236–300s | NOT_MEASURED | keepalives; terminal NON_GROUNDED |
| E4-R6 compare JSON | prior live | ~126–175s | NOT_MEASURED | gateway JSON 120s risk |
| E01 SIPOC | audit probe | **TimeoutError ~90s** | NOT_MEASURED | admission/log shows conversational path eventual |
| E06 unavailable product | audit probe | ~48s | NOT_MEASURED | NON_GROUNDED honest |
| Per-stage LLM | live logs (earlier) | turn_goal 5–30s; select_group 3–26s; arguments retries | NOT_MEASURED | cold Ollama load separate |

`TIME_TO_FIRST_OWNER_READ`: often **never** in failed compares (`material_satisfied=0`) — INCONCLUSIVE success path this window.

---

## 12. Accidental complexity assessment

| Mechanism | Original reason | Still needed? | Simplification candidate |
|---|---|---|---|
| Per-sub `turn_goal` in acquisition filter | Classify analyze vs read | Yes for class; **reuse parent typed plan** for known compares | HIGH |
| Eligibility demotion (removed §19) | Auxiliaries | Removed — keep gone | N/A |
| `evidence_needed` string coverage §20 | External deps | Yes until typed SourceNeed | MEDIUM |
| select_group + select_capability per sub | Semantic routing | Yes but sticky parent owner | HIGH |
| Governed LLM retries ×3 | Provider flakiness | Yes; amplifies cost | MEDIUM (budget-aware) |
| Dual langgraph + orchestration admission logs | Engine A/B | Clarify single sequencer | MEDIUM |
| OWNER_PATH_UNBOUND deterministic messages | Anti-hallucination | **Security-critical — keep** | NO |
| NDJSON heartbeats | Gateway 120s | Keep | NO |
| Foreign selection / corroborate | Multi-owner | Keep with tighter gates | LOW |

---

## 13. Failure causal graph (E4-R6)

```text
User: compare 90260147 vs 90260148
  → admission owner_surface
  → subobjectives (often 4–6)
  → per-sub turn_goal  ……… FRAGMENTATION (latency)
  → preserve_material_dependency (RC-A OK when evidence_needed set)
  → per-sub select_group/capability ……… RC-B first failure (wrong/empty owner)
  → arguments / discover ………………… RC-C first failure (candidate/protocol)
  → material_satisfied=0
  → evidence_composition insufficient
  → NON_GROUNDED client
```

Independent roots: **RC-B**, **RC-C**, residual **REF05**.  
Derived symptoms: retries, long NDJSON, zero composition.  
RC-A no longer primary false-GROUNDED cause.

---

## 14. Architecture options

### OPTION A — Preserve current flow

Fix only proven RC-B/C/REF05 defects locally.

- Pros: lowest migration risk; keeps safety gates.
- Cons: leaves fragmentation/latency; continues doc 226 drift.
- Model-call impact: **hypothetical** modest reduction if selection only fixed.
- Complexity: LOW–MEDIUM per defect.

### OPTION B — Consolidate semantic decisions (**recommended direction**)

Realize doc 226: one validated parent typed goal → deterministic READ obligations for known two-target compares; persist `evidence_needed`/targets; avoid per-sub re-`turn_goal` when parent already declared; sticky owner from parent where safe; keep complex decomposition when dependencies unknown.

- Reuse: `_TurnGoal`, `SubObjectiveTracker`, `_acquisition_subobjectives`, VerifiedCompositeEvidence, Pydantic AI port.
- New components: **none mandatory** (optional typed `SourceNeed` id later).
- Model-call impact: **hypothetical** large reduction on compare path (eliminate N classify + reduce reselection).
- Security: preserve fail-closed / no keyword specialist hardcode.
- Contract impact: prefer internal; public schema only if new fields escape.
- Migration risk: MEDIUM; needs RED on compare + negative false GROUNDED.
- Conflicts: resolves DRIFT vs doc 226 rather than contradicting it.

### OPTION C — Evidence-driven adaptive investigation

Governed state machine: remaining obligations updated after each owner result; replan only on unmet needs.

- Reuse: tracker states, call ledger, continuity contracts.
- Risk: closest to “new planner” — requires **ARCHITECTURE_DECISION_REQUIRED** if beyond extending tracker.
- Benefit: better for multi-hop unknown domains; overkill if B closes E4-R6 compare.

---

## 15. Recommended target direction

**RECOMMENDED_DIRECTION = OPTION B (consolidate semantic decisions), sequenced before C.**

Rationale: evidence shows fragmentation and doc 226 drift; RC-A is already closed enough for false GROUNDED; functional blocker is owner/discovery with amplified cost from repeated semantics. Do **not** start with a new framework.

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
CONTRACT_IMPACT=INTERNAL_FIRST
ARCHITECTURE_DECISION_REQUIRED=ONLY_IF_TYPED_SOURCE_NEED_PUBLIC_OR_NEW_PLANNER
```

---

## 16. Decision ownership matrix (actual → recommended)

| Decision | LLM today | App today | Domain/Core | Recommended change |
|---|---|---|---|---|
| Intent / admission | Yes | Validate | — | Keep |
| Evidence need proposal | Yes (decompose) | String cover §20 | — | Persist typed needs from parent when known |
| Capability selection | Yes per sub | Catalog gate | — | Sticky + retrieval; less re-ask |
| Candidate protocol | Partial LLM | Dead-end detect | Adapter | More adapter-owned discover→execute |
| Authorization | Never final | Governance | **Final** | Unchanged |
| Evidence truth | Never final | Verify | **Authoritative** | Unchanged |
| Outcome verification | Support | **Owner** | Postcondition | Unchanged |

---

## 17. Bounded roadmap proposal (coordination only)

| STEP_ID | Problem | First failure | Reuse | Minimal correction (proposal) | Gates |
|---|---|---|---|---|---|
| R1 | Semantic re-ask per sub | S07 turn_goal×N | `_TurnGoal`, acquisition filter | Skip reclassify when parent typed compare + declared reads | RED false GROUNDED; latency stage trace |
| R2 | Wrong/empty owner | S09–S10 | retrieval, group catalog | Sticky parent owner + better ranking | RC-B E2E oracle path |
| R3 | Discovery dead-end | S12 | `_discover_candidate`, dead-end | Prefer discover-first for candidate-bound | RC-C tests |
| R4 | Target oracle | composition | VerifiedCompositeEvidence | REF05 binding vs requested roots | Oracle PASS |
| R5 | Admission cost on simple asks | S02 | admission | Budget-aware / cache-free but faster model stage | E01 p95 under turn budget |

Each step requires separate authorization; **this audit does not implement them**.

---

## 18. Evaluation cases (this audit window)

| Case | Result | Path signal |
|---|---|---|
| E01 SIPOC | Client **TimeoutError ~90s** | Later log `admission conversational/explanation`; proportional FAST **not proven** |
| E03/E04 compare (prior §19–20) | NON_GROUNDED; preserve_material_dependency | RC-A OK; RC-B/C block |
| E06 unavailable | NON_GROUNDED ~48s | Honest refusal |
| E02/E05/E07/E08 | NOT_RUN this window | Use prior ledger / next task |

Artifacts: `/tmp/audit_path_probe.json`, `/tmp/acq_live_e2e.json`, doc 228 §§19–20 logs.

---

## 19. Open architectural decisions

1. Single orchestrator sequencing authority (LangGraph engine vs application orchestrator admission dual logs).
2. Whether `evidence_needed` should become typed `SourceNeed` ids (public vs internal).
3. Model routing for admission-only turns (same 4B vs lighter) — doc 42 / separate decision.
4. Whether Option C adaptive investigation is warranted after B.

---

## 20. Evidence & trace references

- Code: `handle_interactive_turn.py`, `orchestration.py` (`_attempt`, `_governed_owner_path`, `_acquisition_subobjectives`, `_propose`), `subobjective_tracker.py`, `orchestration_instructions.delpi.json`.
- Docs: 50 §1.1; ADR 58; 226 §2; 228 §§16–20.
- Live: preserve_material_dependency + insufficient composition (228 §20); audit probe E01/E06.
- Scripts (diagnostic): `delia-api/scripts/e2e_audit_path_probe.py`, `e2e_rca_compare_probe.py`.

---

## 21. Security conclusion

Safety-critical fail-closed grounding and anti-narration of owner misses must be preserved. Simplification must not restore eligibility demotion or keyword specialist routing. Zero false GROUNDED in executed RC-A sets remains mandatory for any Option B diff.
