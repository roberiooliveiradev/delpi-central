# 155 — Group Selection Instruction Semantic Conflict Experiment

> **Status:** EVALUATION_COMPLETE — hypothesis refuted, variant B
> rejected. Independent review pending. No production code or
> instruction modified. Deploy not authorized.
>
> **Task:** `DELIA-C3-GROUP-SELECTION-INSTRUCTION-SEMANTIC-CONFLICT-EVAL-01`
> **Baseline:** 74fb1ba10b (delia-api tree identical to the doc-154
> candidate `4a3d315c76`) · **Review:** `85669c79943e`

## 1. Hypothesis under test

`select_group` v23 carries two clauses that can conflict:

- **Documentation-first** — a colloquially-named record subject
  "should prefer that same documentation or knowledge surface
  FIRST".
- **Record-ownership** — record asks "belong to the group that
  exposes record search over the business register".

Hypothesis H1: the conflict drives wrong-owner picks on record
queries. Tested in isolation: same code, same catalog, same model —
only the instruction text varies.

## 2. Variants

| | fingerprint (sha256[:16]) | change |
|---|---|---|
| A | `8eb95ebdafe8b338` | canonical v23, unchanged |
| B | `15855b8c1a17ed47` | **one clause replaced** — documentation-first
  clause rewritten so the record-owning surface stays the
  destination for record asks however named; designation
  resolution explicitly deferred to the governed foreign-evidence
  step; documentation chosen only when the ask itself is
  documentation/meaning/guidance |

Exact diff: single paragraph swap inside `select_group`
(+236 chars). No provider/material names, no new mechanics.
Fixture: `delia-api/tests/fixtures/select_group_instruction_variant_b.txt`
(experimental artifact, not active config).

## 3. Experiment seam & freeze

- **No production change:** the override replaces the single entry
  in the composed orchestrator's in-process `_instructions` mapping
  (`SELECT_GROUP_INSTRUCTION_FILE` env in the eval harness). The
  versioned resource on disk stays v23 throughout.
- Code: identical `delia-api` tree for A and B (verified tree-equal
  to the doc-154 candidate).
- Catalog: live 4-group surface, `scope` present (doc-154 fix).
  `openapi:delpi` 4 caps, `mcp:davi` 2, `mcp:teo` ~22, `mcp:vista` 12.
- Model: `delia-json:latest` (qwen2.5:3b, Ollama, num_ctx 8192).
  Seed unsupported — variance measured, determinism not claimed.
- AuthZ: delegated READ-only dev-portal subject bearer, TTL-minted.
- Interleave: A → B → B → A (ABBA) to decorrelate warm-up/drift.
- Corpus: doc-154 12-scenario subset ×5 + **holdout** 8 scenarios ×5
  (unseen: abraçadeira/espaguete colloquial, explicit code,
  qualifier, two documentation asks, broad ambiguous, conversational).

## 4. Level-1 — stage isolation (frozen catalog, direct
`_select_group`, 5 reps × 10 prompts)

| catalog | A correct | B correct |
|---|---|---|
| live | 16/50 | 14/50 |
| reordered | 18/50 | 17/50 |
| **renamed providers** (alpha/beta/gamma/delta) | **35/50** | **31/50** |
| injected description | 19/50 | 15/50 |

Per-prompt (live catalog, identical for A and B): every record ask
0/5; every documentation ask 5/5; discovery 4/5→3/5; conversational
1/5; the write ask 0/5 under **both** (groups picked where none
should be — pre-existing weakness, unchanged).

**The neutral-names result is the headline:** identical capability
contracts + identical descriptions, only display/owner names
neutralized, roughly *doubles* selection accuracy under BOTH
instructions. The model's failure is dominated by name priors, not
by the instruction clause.

## 5. Level-2 — governed end-to-end

Base corpus (60 runs each):

| metric | A (v23) | B |
|---|---|---|
| select_group eligible | 39/60 | 35/60 |
| **correct** | **17/39** | **10/35** |
| wrong distribution | vista 12, teo 9, delpi 1 | teo 11, vista 14 |
| outcome PASS | 16/60 | 18/60 |
| GROUP_SELECTION_ERROR | 21 | 25 |
| ADMISSION_ERROR | 15 | 19 |
| CAPABILITY_SELECTION_ERROR | 12 | 3 |
| invalid structured output | 5 | 6 |
| model calls / in-tokens | 267 / 462 865 | 254 / 462 828 |
| median / p95 ms | 5 115 / 12 024 | 4 550 / 12 382 |

Holdout corpus (40 runs each):

| metric | A | B |
|---|---|---|
| eligible / correct | 20 / **10** | 24 / **10** |
| wrong distribution | vista 8, teo 1, davi 1 | vista 9, teo 4, delpi 1 |
| outcome PASS | 15/40 | 15/40 |
| model calls / in-tokens | 132 / 241 426 | 160 / 294 732 |

No improvement on either corpus; B is within noise of A on every
dimension. Pass differences are driven by admission variance
(`disc_candidate` B: 5/5 PASS via surface-inquiry answer with zero
group proposals — legitimate), not by selection quality.

## 6. Security

- Injected-catalog probe: the injected group's pick rate did not
  rise (2–3/50 wrong picks, comparable to non-injected runs) —
  instruction text does not obey description content under either
  variant.
- 0 AuthZ bypasses, 0 PREPARE/ACT invocations, 0 invented group ids
  accepted, 0 unauthorized writes across 200 e2e runs + 400 stage-1
  calls.
- Bearer/creds never committed; sanitized artifact at
  `docs/.../evidence/instruction-conflict-eval-runs.json`.

## 7. Causal classification

| hypothesis | verdict | evidence |
|---|---|---|
| **H1 instruction conflict** | **REFUTED** as operative cause — removing the clause changed nothing at the isolated stage (identical per-prompt outcomes) and did not improve e2e or holdout |
| **H2 model capacity** | **SUPPORTED** — identical failures under both instructions + ~2× accuracy when provider names are neutralized: the 3B model keys on misleading specialist names over descriptions/scope |
| **H3 catalog ambiguity** | **REFUTED** for descriptions — same descriptions under neutral names yield ~35/50; semantic signal is sufficient, names carry the misleading signal |
| **H4 admission upstream** | **SUPPORTED** — 15–19/60 base and 10–15/40 holdout admission errors, invariant to the variant (different stage, untouched instruction) |
| **H5 downstream** | **SUPPORTED** — correct delpi picks still FAIL via capability/argument stages (CSE present under both); selection is necessary but not sufficient |

## 8. Decision

**INSTRUCTION_B_RECOMMENDATION = REJECT.** No reproducible
improvement on base, holdout, or stage isolation; security bounds
intact but equal. Per WP7, the variant stays a fixture only.

**Recommended next bounded step:** the residual failure is now
localized to *name-prior dominance at the 3B model* — the only
evidence-backed directions are (a) a separately authorized
bounded model-capacity comparison on this frozen corpus, or
(b) a catalog-presentation experiment neutralizing misleading
display names in the stage-1 projection (owner-neutral labels such
as `group_1..n` with descriptions/scope intact — a projection-level
change, again needing its own task). Admission misrouting and
argument fidelity remain independent known divergent stages.

Artifacts: harness `scripts/instruction_conflict_eval.py`,
`instruction_conflict_stage1_probe.py`,
`instruction_conflict_aggregate.py`, fixture
`tests/fixtures/select_group_instruction_variant_b.txt`, sanitized
runs `docs/.../evidence/instruction-conflict-eval-runs.json`.
