# 77 — CRI E2: Outcome-Aware Answer Execution Report

**TASK_ID:** `DELIA-CRI-E2-OUTCOME-AWARE-ANSWER-01`
**BASE_HEAD:** `e9c13e488faa0079d1b08976bd02aee82d28db3e`
**Date:** 2026-10-21
**Gate:** E2 of roadmap 74 — governed sufficiency assessment of task
outcome, connected to the E1 ON mode. No E3 personality/presentation
work; no second planner; no extra model stage.

---

## 1. Scope executed

Technical success is no longer treated automatically as task outcome.
With `DELIA_RESPONSE_INTELLIGENCE_ENABLED` ON, the governed-outcome →
response binding edge classifies typed outcome facts into the bounded
E0 vocabulary (`answered` / `empty_result` / `envelope_only` /
`insufficient`) and verifies the goal-stage `answer_requirements`
hypothesis against the evidence the owner actually returned.

With the flag OFF, every stage is byte-identical to baseline: same
prompts, same verdict path (none runs), same wire.

## 2. Reuse gate

| Element | Decision | Evidence |
|---|---|---|
| Goal interpretation | REUSE | Existing `_TurnGoal` / `GOAL_INSTRUCTION` / `CAPABILITY_AND_GOAL_INSTRUCTION` already carry semantic intent (`goal_class`, `business_subject`, `scope_constraints`, `prior_evidence_sufficient`). Extended with one typed field — `answer_requirements` — inside the same bounded proposal contract (`_GOAL_ALLOWED_KEYS` + fail-closed parse). |
| Model stage | REUSE (zero added) | Requirements ride the SAME goal/capability proposal (`input_kind=capability_selection_with_goal` or `turn_goal`). `ADDITIONAL_MODEL_CALLS=0` proven by request-count equality OFF vs ON. |
| Typed evidence | REUSE | `extract_pagination_envelope`, `_synthesis_records`, `_CONTROL_PLANE_KEYS`, `_RESOLVER_ENVELOPE_KEYS`, `SpecialistOutcome.is_complete/limitations`. No provider names, no endpoint knowledge, no lexical intent rules. |
| Insufficiency surface | REUSE | `LIMITATION_INSUFFICIENT_EVIDENCE` — the existing limitations contract; folded onto `outcome.limitations` so every render path (selection-only synthesis or deterministic `_success_attempt` render) carries it. SUCCESS is never rewritten into an error. |
| ON/OFF control | REUSE | Same `settings.response_intelligence_enabled` resolved once in `root_composer`, propagated as typed ctor bool into `OperationalCapabilityOrchestrator`. No second env read. |
| Verdict vocabulary | NEW (internal only) | `outcome_assessment.py` — leaf module, no public DTO/enum on the wire; decisions logged as `stage=outcome_assessment decision=… reasons=…`. Spec 75 vocabulary realized inside existing contracts, not as a new status. |
| Declarative JSON resource | NOT_NEEDED | The clause extends the existing Python-resident instruction family (`InstructionLineage` covers the variant — CRI content hashes distinctly). Spec 75 §8 forbids decorative resources without a consumer; migrating the instruction family to JSON is the structural redistribution doc 74 excludes from this roadmap. |

## 3. Mechanism

```text
governed read outcome (post aggregation, post synthesis)
  → _outcome_facts(outcome)          [typed projection only]
  → assess_outcome(facts, goal.answer_requirements)
  → verdict logged per turn
  → envelope_only|insufficient  ⇒  outcome.limitations += insufficient_evidence
  → existing _outcome_attempt preserves binding/provenance/limitations
```

- `EvidenceFacts`: records, `has_business_evidence`, `explicit_empty`,
  `is_complete`, `coverage_complete` (from `has_more`/`total_count`),
  `total_count`. Never raw payloads, never `content_text`.
- `AnswerRequirements` (hypothesis): `min_items`, `ordering`
  (`newest_first|oldest_first`), `complete_coverage`. Parsed
  fail-closed: unknown keys, wrong types, out-of-range or undeclared →
  `None` → nothing checked.
- Verification rules: `fewer_than_requested` only against an
  authoritative `total_count` or proven coverage; otherwise
  `quantity_unproven`. `ordering` requires a uniformly parseable
  temporal field (values carry the type evidence — field names are
  never matched) AND proven coverage; a single record without coverage
  is `ordering_unproven`. `complete_coverage` requires
  `coverage_complete is True`.
- `explicit_empty`: paginated envelope proven empty (`has_more=False`
  or `total=0`) or a list-shaped business payload that is empty
  (control-plane/envelope keys excluded). Checked before generic
  evidence presence so "no results" text never hides an empty verdict.
- `unavailable` stays upstream as `SOURCE_UNAVAILABLE` — it never
  reaches this stage.

## 4. Mandatory cases (doc 73)

| Case | Shape | Verdict |
|---|---|---|
| A — TÉO "último processo" | single record, ordering requirement, no coverage proof | `insufficient` (`ordering_unproven`) → `insufficient_evidence` limitation |
| B — DAVI envelope | technical return, zero business records | `envelope_only` → `insufficient_evidence` limitation |
| C — DELPI "três exemplos" | 2 records, authoritative `total=2` vs `min_items=3` | `insufficient` (`fewer_than_requested`) |
| D — VISTA playlists | records + complete + no declared requirements | `answered` — no marker added |

Generalization negatives proven: invalid requirement payloads fail
closed; non-temporal fields (ids/counters) are never ordering evidence;
partial outcomes (`is_complete=False`) mark `partial_outcome`;
unproven coverage never upgrades to answered; malicious owner text
cannot create facts (assessment reads typed facts only).

## 5. Observability

`orchestration stage=outcome_assessment decision=<verdict>
reasons=<csv> correlation_id=<id>` — decision + bounded reason codes
only; no payloads, no user text, no provider values.

## 6. Contracts preserved

- `PUBLIC_CONTRACT_CHANGES=NO` — `GovernedCapabilityAttempt`,
  `InteractiveTurnResult`, routes, serialization untouched.
- `SELECTION_ONLY_PRESERVED=YES` — no model-authored prose; the clause
  proposes typed requirements, never content.
- `AUTHORITY_BOUNDARIES_PRESERVED=YES` — READ stays READ; no flag or
  verdict reaches provider arguments, AuthZ, PREPARE/ACT.
- `TURN_BUDGET_PRESERVED=YES` — assessment is deterministic and local;
  the requirement hypothesis rides the existing goal stage.
- `MATERIAL_ACT=0`, `PRODUCTION_DEPLOY=NO`, `I04_ACCEPTED=NO`,
  `C3_EXECUTED=NO`.

## 7. Evidence

- `tests/test_cri_e2_outcome_assessment.py` — 43 tests: requirement
  parsing matrix, verdict unit coverage, ON engagement per case,
  OFF parity (identical limitations, no stage log even when the model
  proposes requirements), zero additional model calls, CRI instruction
  prefix/variant proof, provider-text injection, invalid proposals.
- Full backend suite: **1756 passed, 3 skipped** (was 1713+3).
- `py_compile` clean on all touched files.

## 8. Residuals

- `REAL_MODEL_EVALUATION=NOT_RUN` — E4 scope; unit/integration proof
  only.
- Corroboration path (`_corroborate_attempt`) keeps its existing
  bounded comparison semantics — assessment currently binds to the
  single-owner read edge.
- A bare empty collection (`{"items": []}` without pagination
  metadata) is treated as a definitive empty result — the residual
  ambiguity vs. an unmarked first page is documented, never silently
  resolved in the confident direction elsewhere.
- Instruction-family JSON migration remains out of roadmap scope;
  CRI clause versioning rides `InstructionLineage` content hashes.


## 9. Independent coordination review — 2026-10-21

**Verdict: `REWORK` (one bounded correction cycle), not accepted yet.** Static review of published SHA `ef590f31ed90d699116599fdf837f594a38a5eec` and report 77. Executor claims `1756 passed / 3 skipped`; independent suite re-execution `TEST_NOT_RUN`. Reviewed `outcome_assessment.py`, `_outcome_facts`/`_apply_outcome_assessment` and `_ANSWER_REQUIREMENTS_CLAUSE` in `orchestration.py`.

**E2-R1 / temporal ordering:** `_temporal_order` ignores records whose candidate field is absent (`value is None: continue`) and considers two or more parseable values sufficient, potentially returning a direction while some rows lack comparable timestamps. Require all relevant returned records to carry a comparable typed temporal value; provide negative tests for missing fields and ambiguous/nonuniform temporal evidence. Also ensure sorting direction is not mistaken for an owner-proven global latest without legitimate coverage.

**E2-R2 / requested examples:** `_unproven_requirements` accepts `total_count >= min_items` as sufficient even when `len(records) < min_items`. An authoritative total may prove the owner has enough records, but does not prove the requested examples were delivered in the current result. Separate available total from delivered/selected item count; tests with `total_count=100` and only 1–2 returned rows for a three-example request must not classify `answered` merely from total count.

**E2-R3 / declarative instructions:** `_ANSWER_REQUIREMENTS_CLAUSE` is a new multiline natural-language prompt embedded in Python, conflicting with product front 73 §9, roadmap 74 and E0 75 resource-separation requirement. The exception for not migrating **legacy** orchestration strings does not cover adding new long CRI instructions. Move only the new CRI-specific clause into an approved, versioned declarative resource and a minimal validated loading boundary that reuses existing `load_declarations` conventions, without bulk migration, new registry, separate planner or changed OFF prompt bytes. Preserve `InstructionLineage` hash/version and missing/invalid resource fail-safe; demonstrate OFF and ON tests. If an existing mechanism prevents this safely, STOP with precise `ARCHITECTURE_DECISION_REQUIRED`, not a silent exemption.

**Limited rework acceptance:** fix exactly R1–R3, run focused adversarial regressions plus complete backend suite, prove OFF parity/ON behavior, residual search, commit/push and report. No broad E2 rearchitecture, new capability engine, real-model deployment or E3 work. As per roadmap 74, this is the **single permitted bounded rework** for E2. 

`E2_VERDICT=REWORK`; `E2_ACCEPTED=NO`; `E2_REWORK_ALLOWED=ONE_BOUNDED_CYCLE`; `E3_AUTHORIZED=NO`; `REAL_MODEL_EVAL=TEST_NOT_RUN`; `I04_ACCEPTED=NO`; `C3_EXECUTED=NO`.
