# 203 — Semantic decision & evidence relevance: diagnosis, candidate A/B, boundary verdict

**Task**: `DELIA-C3-SEMANTIC-INTELLIGENCE-PLUGGABLE-AB-01`. **Base**:
`7a75a7d39d` → delivery HEAD moved by concurrent work (verified
ancestry). **Status**: DIAGNOSIS_DONE + LOCAL_AB_DONE. **Deploy**: NO.
**Production calls**: 0 (LLM). Local owner READ probes only.

## 1. Authorities and reanchor

ADR 58 (LLM owns semantics via typed proposals; deterministic code owns
gates; `LEXICAL_INTENT_DECISION_ENGINE=DEPRECATED`), docs 187–202,
doc 189 register, doc 191 framework fit assessment, doc 192 boundary
discovery, ledger. Phase C3 unchanged.

## 2. Incident corpus and responsibility matrix

| INCIDENT | GOAL | OBSERVED | STAGE | RESPONSIBILITY | CAUSE_STATUS |
|---|---|---|---|---|---|
| I1 prod T1/T2 (docs 188/190) | products with codes | `read_governed_technical_knowledge` picked over `search_products` | select_candidate | CAPABILITY_CONTRACT (goal not projected) | PROVEN — **FIXED** by doc 190 |
| I2 prod T3/T4.2 (doc 188) | terminal-bala examples | 16–19 model calls, recovery loop, no outcome | recovery | RECOVERY_SEQUENCING | PROVEN — partial fix Tasks 04/05 (reuse); residual = legitimate re-assessment when premises change |
| I3 Task-09 smoke S2 (`3a117602`) | "dois exemplos de terminal bala" | correct selection → owner records irrelevant ×2 → honest `insufficient_evidence` | retrieval | **DOMAIN_RETRIEVAL** | **PROVEN this task** — §3 |
| I4 F4 retries (doc 188) | any | invalid structured output retries, 16–36s cost | model output | MODEL_OUTPUT_VALIDATION | FIXED (Task 08 eval + Task 09 fail-closed) |
| I5 stage-level corpus (local) | paraphrase/group picks | wrong group/capability on 3.1B eval model | select_group/select_capability | SEMANTIC_SELECTION | PROVEN at eval-model scale — §5 |

Historical defects I1/I2/I4 already have owners and fixes — no residual
boundary work. The live question was I3 (C-vs-D split) and whether a
DÉLIA-owned semantic defect justifies a pluggable boundary (I5).

## 3. PROVEN root cause — terminal-bala is owner-side retrieval

Local api-delpi (same TOTVS backend) probed via `SearchProductsUseCase`
directly (READ-only, no HTTP auth, no production):

| `description` arg | total | result |
|---|---|---|
| `TERM. BALA` (owner vocabulary) | 1.678 | **10080092 + 10081004 ranked #1** |
| `terminal bala` (user vocabulary) | 445 | TERMINAL*/BALA* prefix flood — **real records don't match at all** |
| `bala` | 33 | BALANCA/BALANCIM prefix collisions dominate |
| `TERM BALA` | 3.404 | worst flood |

The owner's `description` search is token-OR/prefix matching with no
abbreviation bridging (`TERMINAL` ≠ `TERM.`). Model-generated arguments
in the user's vocabulary can **never** reach the real records — the
production trace shows correct semantic selection and correct honest
rejection; the failure is the owner contract.

**Owner remediation brief** (no DÉLIA code): evolve
`ProductRepository.search_products` description matching —
per-token AND prefix-any-position, and/or an abbreviation/synonym
normalization table (TERM↔TERMINAL etc.), and/or relevance-ranked
full-text. Bounded alternative already partially in place: governed
knowledge carries canonical designations that recovery can reuse
verbatim (goal_evidence_relevance `mismatch_hint` contract) — works
only when a knowledge document names the designation.

## 4. Reuse-before-design

```text
RESPONSIBILITY=semantic stage decisions (select_group /
  select_capability / goal_evidence_relevance)
OWNER=delia-api application layer (orchestration.py)
CANONICAL_SOURCE=_model_stage_proposal + _propose + per-stage v25
  instructions + typed downstream validators
CONSUMERS=_governed_owner_path (Engine A and LangGraph B1 share it)
CONTRACT=in: input_text + bounded block; out: typed proposal keys

EXISTING_EQUIVALENT=YES — ModelInvocationPort + _propose contract
REUSE_DECISION=EXTEND (evaluation harness only, Task-08 pattern)
ABSTRACTION_GATE=no new production port — no candidate earned one
```

## 5. Local A/B — baseline vs DSPy (same model, same corpus)

Harness `delia-api/scripts/semantic_decision_eval.py` — REAL v25
instructions, REAL block builders (`_capability_payload`,
`_group_summaries`), REAL adapter parse, REAL downstream validators.
Candidate: `dspy==3.4.1` (MIT, ≥3.10, published 2026-10-12 = 17d),
`Predict` + `JSONAdapter`, temperature 0, cache off, eval-only in
`.venv` (requirements-eval.txt). Framework output flows through the
same validators — never authoritative.

Model: `delia-json:latest` (3.1B local eval model — **not** production
kimi-k3; absolute numbers are eval-model data, per docs 185/188
semantics are not production-equivalent).

| Stage | Baseline run1 | Baseline run2 | DSPy |
|---|---|---|---|
| select_capability top-1 | 67% (8/12) | 75% (9/12) | **42% (5/12)** |
| select_group top-1 | 38% (3/8) | 38% (3/8) | **62% (5/8)** |
| relevance accuracy | 67% (4/6) | 67% (4/6) | 50% (3/6) |
| input tokens | 33.2k | 33.2k | **16.7k (−50%)** |

Run-to-run noise (baseline, default temperature): 10/26 cases flip —
selection stage is nondeterministic on this model; deltas partly inside
noise. DSPy behavior: markedly fail-closed (not_applicable/uncertain
overuse) — safer posture but loses recall on capability selection;
modest gain on group selection; half the prompt tokens.

Representative failures (baseline): unknown goal ("cotação do dólar")
wrongly applicable; "como cadastro um produto" → `search_products`
instead of documentation; bare id → `execute_delpi_information`
(requires a discovery token it cannot have). DSPy fixed those three
classes but at the cost of answering `not_applicable` to 6/12 real
business asks.

## 6. Verdict

```text
CANDIDATE_VALUE_VERDICT=REWORK_BENEATH_THRESHOLD
RECOMMENDED_INTEGRATION=none — no pluggable boundary created
EXECUTOR_VERDICT=OWNER_REMEDIATION_REQUIRED (retrieval) +
  NO_ABSTRACTION_JUSTIFIED (semantic layer, this evidence)
```

- No new port/engine/validator/registry — the smallest legitimate
  boundary stays the existing `_propose` stage contract; production
  code: **zero lines changed**.
- Token savings (−50%) without task success is not optimization
  (task §15); DSPy net-lost accuracy on the finest-grained stage.
- The only proven real-world defect is owner retrieval → owner
  remediation brief in §3, not a DÉLIA plugin.
- Remaining lever inside the existing boundary: capability
  descriptions/instruction quality (Candidate D) and, if pursued,
  model-side — not framework-side.

## 7. Gates

- Harness tests `tests/test_semantic_decision_eval.py`: 17/17 —
  corpus classes, REAL_CONTRACT reuse, downstream gates reject forged
  group/remote_name, no `dspy` under `app/`, module imports without
  SDK, no provider branching, local model only.
- Focused regression: 287 + 22 engine tests GREEN in container
  (orchestration, recovery/reuse, observability, engines A/B0/B1
  conformance incl. Task-05/06/09 suites).
- `audit_architecture_phase3.py --base HEAD`: OK.
  `audit_backend_boundaries.py`: 0 findings.
- Residual: `dspy` appears only in `scripts/` + `requirements-eval.txt`.
- PRODUCTION_CODE_CHANGED=NO; DEPENDENCIES_CHANGED=eval-only
  (`dspy==3.4.1`); DEPLOY=NO; PRODUCTION_CALLS=0.

## 8. UNRESOLVED

- Whether kimi-k3 shows the same selection fragility — eval-model
  numbers do not transfer; a production-model stage eval needs the
  authorized-model A/B path (separate authorization).
- Owner remediation scheduling for `search_products` matching —
  handed to the api-delpi owner.
- If a future candidate is proposed, the evaluation boundary is ready:
  same corpus, same validators, `arm=` parameter.
