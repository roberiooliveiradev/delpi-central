# 96 — Contextual Intelligence, Semantic Capability Selection & Multiturn Continuity

**TASK_ID:** `DELIA-C3-CONTEXTUAL-INTELLIGENCE-DAVI-MULTITURN-REMEDIATION-01`
**Date:** 2026-10-22
**Mode:** REANCHOR → CONTRACT INVENTORY → REPRODUCE → ROOT CAUSE → REUSE GATE → MINIMAL IMPLEMENTATION → TEST → GENERALIZATION → DOCUMENT → COMMIT → PUSH MAIN → REPORT

---

## 1. Incident under investigation

Production conversation (same chat):

| Turn | Input | Observed |
|---|---|---|
| T1 | `2 exemplos de terminal bala` | Generic examples, no DELPI source consulted |
| T2 | `use o davi` | "não conheço davi" |
| T3 | `o mcp davi` | DAVI selected, query failed, UI showed `api-delpi` as failure origin |

The screenshots do not prove the cause. The real chain was inspected
end-to-end before any code change.

## 2. Contract inventory — what the chain actually does today

`Input → prior_turns → admission → live surface → group selection →
capability selection → typed arguments → owner invoke → evidence →
outcome → answer` — traced in the current HEAD, not from reports.

| Question | Verified answer |
|---|---|
| Do prior turns reach the backend? | YES — `plugins/delia` builds bounded USER_INPUT/DELIA_RESULT pairs (16 384-char aggregate, whole turns); `handle_interactive_turn` validates and forwards `prior_turns` into `attempt()` |
| Which stages consume them? | `_admit_conversational_turn` (raw turns), `_understand_goal` (raw turns), `_prior_continuation_attempt`, `_select_capability`/`_select_capability_with_goal` (`prior_observation` excerpt in the catalog payload), `_select_foreign_capability` (raw turns) |
| Which stage did NOT? | **`_select_group` — the only semantic stage with zero context channel** (payload `_group_summaries(groups)` only; `prior_turns=()`) |
| Truncation defects? | None found — bounded excerpts are by design; the gap was total absence at group level |
| Live catalog contains DAVI? | YES — probe on the real authenticated surface: `mcp:davi` = `discover_delpi_information` (DISCOVERY) + `execute_delpi_information` (candidate-bound READ) |
| Other owners for materials? | YES — `openapi:delpi` advertises `delpi.search_products`, `get_product_summary`, `get_product_stock`, `search_customers`; DAVI DISCOVERY returns candidate-bound searches (Search products, Product stock by branch/location, Stock balance) |
| `api-delpi` label wrong? | NO — `api-delpi` is DAVI's `owner_ref` in the canonical `_SPECIALIST_IDENTITY` domain map; the UI shows honest provenance |
| Clarification contract? | Exists — `CLARIFICATION_REQUIRED` with bounded `_SELECTION_INCONCLUSIVE_CONTENT` |
| Advertised ≠ authorized? | Preserved — every proposal revalidated against the live surface; DISCOVERY-required candidates enforced by owner `argument_schema` |

## 3. Reproduction evidence (dev, Ollama `qwen2.5:3b` only)

Full governed turns (`ctx_multiturn_eval.py`, real authenticated MCPs):
every turn reached `interaction_admission → turn_goal` correctly
(prior turns consumed by both stages), then exhausted the 60s budget
inside the ≤3B CPU-bound model — **stage timeouts are the documented
model constraint (doc 93), not a pipeline defect**. Zero MCP invokes,
zero PREPARE/ACT, honest PROCESSING_TIMEOUT terminals.

Stage-level probes (`ctx_stage_probe_eval.py`, one real model call per
case on the real live catalog) isolated the semantic decisions:

| Case | Result |
|---|---|
| `agora use outro especialista, se ele tiver uma fonte melhor` (prior OBSERVATION naming transformometro-api) | **selected `mcp:davi`** — model resolved "outro" to a *different* owner using the embedded prior_observation |
| `o mcp davi` | **selected `mcp:davi`** |
| `use o davi` | **selected `mcp:davi`** |
| `2 exemplos de terminal bala` | **selected `openapi:delpi`** — model chose the product catalog owner, not DAVI, not TÉO |
| admission `use o davi` / `terminal bala` | fail-through to owner surface (invalid proposal → never conversational exit by accident) |

## 4. Root causes (proven)

**RC1 — context-loss seam at group selection.** `_select_group` was
the only semantic stage that could receive neither the raw prior
transcript nor the bounded `prior_observation` projection — the
mechanism existed exactly one level down (capability payload) and the
sibling instruction already documented its semantics. Any group-level
anaphora (*"outro especialista"*, *"essa fonte"*, a named source whose
applicability depends on what was being answered) was uninterpretable
**by construction**. This is also the stage that decides
`applicable` — a bare routing directive (*"use o davi"*) carries no
information need without the surrounding context, so `not_applicable →
conversational fallback` was a structurally produced outcome, matching
the T2 symptom.

**RC2 — admission/group instructions lacked named-source semantics.**
`INTERACTION_ADMISSION_INSTRUCTION` (payload note: *"no owner
catalog"*) listed no rule for directives that route the answer
through a named or referenced system/source/specialist — a legitimate
model could classify `use o davi` as `conversation`, which is terminal
(NOT_APPLICABLE → generic model answer, the observed *"não conheço"*).
The group instruction likewise did not state that matching a named
surface against `display_name`/`owner`/`source_system` is the stage's
job. Both are generalized semantic rules — no specialist names, no
aliases, no lexical code.

**Not root causes:** `api-delpi` provenance (honest `owner_ref`), MCP
transport/AuthZ (R4 authenticated chain re-verified green), invented
argument names (owner schema correctly refuses, e.g. `query` →
`mcp_protocol_error` — owner authority intact), frontend context
transport (verified complete end-to-end).

## 5. Reuse gate

| RESPONSIBILITY | OWNER | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| bounded untrusted prior context for selection | `_prior_observation_context` (orchestration) | YES (capability payloads) | **REUSE** — same mechanism wired into `_group_summaries` |
| group payload shape | `_group_summaries` | YES | EXTEND — `prior_observation` kwarg mirrors `_capability_payload` |
| foreign-group selection payload | `_select_foreign_capability` | YES | EXTEND — same projection |
| semantic guidance | versioned instructions (`SELECTION_INSTRUCTION_VERSION`) | YES | EXTEND — admission + group instruction text, version `12 → 13` |

No new planner, registry, catalog, adapter, continuity mechanism or
composer was created.

## 6. Minimal implementation (canonical owner only)

`delia-api/app/application/capability_provision/orchestration.py`:

1. `_group_summaries(groups, *, prior_observation=None)` — when an
   OBSERVATION-class prior result exists, the payload becomes
   `{"capability_groups": [...], "prior_observation": {...}}`; shape
   unchanged otherwise. Bounded by `MAX_SURFACE_CHARS` + the excerpt's
   own cap.
2. `_select_group` — computes `_prior_observation_context(prior_turns)`
   and embeds it (raw transcript still excluded — latency invariant).
3. `_select_foreign_capability` — same projection.
4. `GROUP_SELECTION_INSTRUCTION` — documents `prior_observation`
   semantics (untrusted, reference resolution only) + named/referenced
   source routing rule.
5. `INTERACTION_ADMISSION_INSTRUCTION` — named/referenced-source
   directives are operational-or-ambiguous, never plain conversation;
   catalog-entity examples prefer `ambiguous` over `hypothetical`.
6. `SELECTION_INSTRUCTION_VERSION` `"12" → "13"`.

`delia-api/tests/support/fake_group_proposal.py` — TEST_ONLY helper
unwraps the new envelope (still never invents a group id).

## 7. Tests

**RED** (fails on pre-fix HEAD):
`test_group_selection_payload_embeds_prior_observation` — group-stage
request must carry `prior_observation` when a prior OBSERVATION
DELIA_RESULT exists.

**GREEN / siblings / negatives** (`test_referential_detail_resolution.py`):
- prior_observation embedded (positive);
- non-OBSERVATION prior (HYPOTHESIS) → absent (negative — a
  conversational answer is never presented as observation);
- `_group_summaries` shape: wrapped vs bare-array (contract);
- existing `prior_observation`-is-not-authority invariants unchanged.

**Regression:** full `delia-api` suite green (all tests, including
admission-instruction guards `test_semarg_t21`, latency, resume,
CRI, index-probe and governed-write suites).

**Live generalization (real Ollama + authenticated MCPs):**
`use o davi`→`mcp:davi`; `o mcp davi`→`mcp:davi`;
`agora use outro especialista`→`mcp:davi` (anaphora resolved against
prior_observation, different owner); `2 exemplos de terminal bala`→
`openapi:delpi`. Zero external LLM calls.

## 8. Limits & residuals

- qwen2.5:3b on CPU cannot complete a full multiturn chain inside the
  60s governed budget under contention — stage timeouts surface as
  honest PROCESSING_TIMEOUT (documented doc 93); **no deadline or
  lexical compensation was added**, per task policy. Production
  (kimi) does not share this constraint.
- Production incident logs for the three turns predate the last
  `delpi-delia-api` recreate and were unavailable; the T3 invoke
  failure class (transport vs schema vs owner) is therefore classified
  as *observed-honest* (`api-delpi` = owner_ref provenance), not as a
  proven transport defect — none was found in the current chain.
- `Ori` fragment, CRI prosa, context-panel integration, prod recovery
  activation, global timeout mechanism, conversation persistence —
  unchanged (out of scope).
- Delegated-credential intra-turn reuse finding (doc 94) remains an
  open architecture decision; prod recovery stays OFF.

## 9. Report

```text
TASK_ID=DELIA-C3-CONTEXTUAL-INTELLIGENCE-DAVI-MULTITURN-REMEDIATION-01
CANONICAL_REANCHOR=DONE (HEAD 11514c4fa, authorities + docs 88–95)
CP_RQ=contextual continuity + semantic owner selection without
    specialist-specific rules
EXISTING_EQUIVALENT=YES (_prior_observation_context,
    _capability_payload, versioned instructions)
REUSE_DECISION=REUSE mechanism + EXTEND payloads/instructions —
    no parallel mechanism

PRIOR_TURNS_TRANSPORT=VERIFIED (MFE bounded pairs → backend →
    orchestration; whole turns, 16k aggregate)
PRIOR_TURNS_MODEL_CONSUMPTION=admission/turn_goal/continuation/
    capability+foreign selection consumed context; GROUP SELECTION
    had none — fixed
CAPABILITY_DISCOVERY=live per-turn tools/list + OpenAPI surface
    (4 groups: mcp:davi, mcp:teo, mcp:vista, openapi:delpi)
DAVI_DISCOVERY=discover_delpi_information (DISCOVERY) +
    execute_delpi_information (candidate-bound READ)
DAVI_AUTHORIZATION=delegated credential per turn; owner schema is
    authoritative (invented args refused)
DAVI_INVOKE=not exercised this task; contract path unchanged
API_DELPI_FAILURE_ROOT_CAUSE=NOT_A_DEFECT — api-delpi is DAVI's
    canonical owner_ref; honest provenance label
SEMANTIC_SELECTION_ROOT_CAUSE=group stage had zero context channel
    (RC1) + instructions lacked named-source semantics (RC2)

MULTITURN_BEFORE=group-level anaphora uninterpretable by
    construction; named-source directive could exit conversational
MULTITURN_AFTER=prior_observation reaches group selection;
    live model resolved outro_especialista→mcp:davi
GENERALIZATION=live: terminal_bala→openapi:delpi, use o davi→
    mcp:davi, o mcp davi→mcp:davi, outro_especialista→mcp:davi
NEGATIVE_CASES=non-OBSERVATION prior never embedded; invalid
    proposals fail closed; forged/invented fields refused by owner
MODEL_PROVIDER=OLLAMA EXTERNAL_LLM_CALLS=0

RED_TESTS=test_group_selection_payload_embeds_prior_observation
GREEN_TESTS=3 new + full delia-api suite green
REGRESSION=full suite green incl. admission guards, latency,
    resume, CRI, index-probe, governed-write
REAL_TASK_OUTCOME=context channel closed at group selection;
    semantic named-source routing enabled without aliases or
    provider branches
EVALUATED_SHA=<final commit>
EVALUATED_CONFIG=dev, Ollama qwen2.5:3b, MAX_ATTEMPTS=2, 60s/30s
    budgets preserved

RESIDUALS=≤3B CPU latency (doc 93); prod T3 invoke class
    observed-honest not proven; intra-turn credential reuse
    (doc 94) open
```
