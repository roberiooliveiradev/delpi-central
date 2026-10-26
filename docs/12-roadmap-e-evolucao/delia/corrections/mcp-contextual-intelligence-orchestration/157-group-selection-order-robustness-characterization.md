# 157 — Group Selection Order-Robustness Characterization

**Task**: `DELIA-C3-GROUP-SELECTION-ORDER-ROBUSTNESS-CHARACTERIZATION-01`
**Type**: controlled diagnostic evaluation. No production code,
instruction, catalog, canonical identifier, or model changes.
Evidence-only commit.
**Follows**: `156-catalog-presentation-name-prior-sensitivity-evaluation.md`
**Independent review consumed**: `cb3a9bee23b81eb0d211c8cdce806bedc9e47d8d`

## 1. Reanchoring

- `BASE_SHA`: `3fdb36e8834ea6b93c2ab5e38a37794a97c9c533` (consulted HEAD).
- Working tree fast-forwarded to upstream tip (`6832d564c5`) at task
  start; concurrent work preserved. The `delia-api` tree is identical
  to the document-156 baseline — frozen evaluated SHA holds.
- Authorities read: `.cursor/rules/`, `AGENTS.md`, documents 151–156,
  independent review `cb3a9bee`, execution ledger. No contract
  incompatibilities — no `ARCHITECTURE_DECISION_REQUIRED`.
- Review residual honored: the experiment permutes the **serialized**
  group list (post-projection), measures absolute vs relative order,
  separates run variance from order effect, and keeps strict oracle as
  the primary reference.

## 2. Reuse gate

| Field | Value |
|---|---|
| `EXISTING_EQUIVALENT` | `scripts/catalog_presentation_probe.py` (probe + payload capture seam), `catalog_presentation_aggregate.py` (exclusive matrix), `instruction_conflict_eval.py` (governed e2e harness + permutation seam), production `_group_summaries`/`_select_group`/`_projected_capability_ids`, contracts `CapabilityGroup`/`ProviderCapability`/`SourceRef`, instruction v23, model port, `MAX_SURFACE_CHARS=6000`. |
| `REUSE_DECISION` | `REUSE` — new code limited to `order_robustness_probe.py` (24-perm matrix runner) and `order_robustness_aggregate.py` (positional/relative/variance analysis). The e2e permutation seam extends the existing eval-only reorder seam with `EVAL_PERM_ORDER`. |
| `RESPONSIBILITY` | Evaluation-only permutation of the serialized `capability_groups` list. |
| `OWNER` | `scripts/` harness layer. |
| `CONSUMERS` | This experiment only. |
| `CANONICAL_CONTRACT` | Only the list order of the already-projected payload changes. No re-compaction; canonical ids, capability ids, scope, descriptions, omission markers, schemas byte-identical. |
| `SECURITY_BOUNDARY` | `CATALOG ORDER != AUTHORITY`, `MODEL SELECTION != PERMISSION`, `READ != WRITE`, `PREPARE != ACT`. In-process only. |

No new runtime, registry, catalog, planner, or selection mechanism.

## 3. WP0 — Frozen baseline

| Field | Value |
|---|---|
| `EVALUATED_SHA` | `148b4e0a3a` application tree (verified identical to `6832d564`) |
| `MODEL_ID` | `delia-json:latest` (`qwen2.5:3b`, Ollama) |
| `CONTEXT_WINDOW_EFFECTIVE` | 8192; surface budget 6000 chars |
| `INSTRUCTION_VERSION` | v23, fp `8eb95ebdafe8b338` |
| `CATALOG_SNAPSHOT` | 4 groups / 41 caps; canonical payload sha `916c063b…`, 5989 chars |
| `SEED` | `NOT_SUPPORTED` — variance measured, not controlled |

## 4. WP1 — Permutation matrix and payload contract

All `4! = 24` permutations tested. For every run the dispatched
payload was captured and verified:

```
SAME_GROUP_SET=YES   SAME_CAPABILITY_SET=YES   SAME_SCOPE=YES (4/4)
SAME_OMISSION_MARKERS=YES (omitted=1)   SAME_CANONICAL_IDS=YES
SAME_PAYLOAD_SIZE=YES (5989 chars)      JSON_VALID=YES (all 24 shas)
ONLY_ORDER_CHANGED=YES — 24 distinct payload shas, one per permutation
```

Permutations are applied to the serialized `capability_groups` list
after projection — no compaction re-run. Schedule interleaved
rep → permutation → prompt for temporal balance.

## 5. WP3 — Stage-1 isolation: 1440 calls (24 perms × 12 prompts × 5 reps)

Global strict: 542/1440 (37.6%); lenient 630/1440 (43.8%);
invalid 73; not-applicable-correct 68.

### 5.1 Per-permutation strict accuracy (correct/60)

| Perm | Order | Strict | Lenient | Invalid | Dominant share | Top pick |
|---|---|---|---|---|---|---|
| 0 | davi teo vista delpi (canonical) | 22 | 22 | 0 | .533 | vista 32 |
| 1 | davi teo delpi vista | 17 | 17 | 1 | .633 | vista 38 |
| 2 | davi vista teo delpi | 23 | 24 | 0 | .533 | delpi 32 |
| 3 | davi vista delpi teo | 25 | 25 | 3 | .533 | teo 32 |
| 4 | davi delpi teo vista | 20 | 23 | 1 | .367 | vista 22 |
| 5 | davi delpi vista teo | 28 | 30 | 0 | .550 | teo 33 |
| 6 | teo davi vista delpi | 26 | 34 | 4 | .350 | delpi 21 |
| 7 | teo davi delpi vista | 31 | 31 | 4 | .583 | vista 35 |
| 8 | teo vista davi delpi | **32** | 32 | 2 | .733 | delpi 44 |
| 9 | teo vista delpi davi | 24 | 32 | 0 | .583 | delpi 35 |
| 10 | teo delpi davi vista | 31 | 34 | 0 | .367 | vista/delpi 22 |
| 11 | teo delpi vista davi | 30 | 34 | 2 | .500 | delpi 30 |
| 12 | vista davi teo delpi | 27 | 27 | 2 | .650 | delpi 39 |
| 13 | vista davi delpi teo | 23 | 23 | 0 | .500 | teo 30 |
| 14 | vista teo davi delpi | **32** | 33 | 2 | .767 | delpi 46 |
| 15 | vista teo delpi davi | **32** | 32 | 1 | .750 | delpi 45 |
| 16 | vista delpi davi teo | 23 | 24 | 0 | .567 | teo 34 |
| 17 | vista delpi teo davi | 24 | 30 | 0 | .333 | delpi 20 |
| 18 | delpi davi teo vista | 19 | 19 | 2 | .517 | vista 31 |
| 19 | delpi davi vista teo | 15 | 15 | 6 | .733 | teo 44 |
| 20 | delpi teo davi vista | 15 | 24 | 3 | .417 | davi 25 |
| 21 | delpi teo vista davi | **5** | 19 | **26** | .483 | davi 29 |
| 22 | delpi vista davi teo | 12 | 19 | 0 | .600 | teo 36 |
| 23 | delpi vista teo davi (reversed) | **6** | 27 | **14** | .667 | davi 40 |

Permutation accuracy range: **5/60 → 32/60** (stdev .13 across perms).
The same catalog content produces a 6.4× spread purely from order.

### 5.2 Absolute position effect

Pick-rate when a group sits at each position (exposures=360 each):

| Group | pos1 | pos2 | pos3 | pos4 |
|---|---|---|---|---|
| mcp:davi | .089 | .075 | .208 | **.364** |
| mcp:teo | .031 | .067 | .203 | **.581** |
| mcp:vista | .000 | .006 | .178 | **.475** |
| openapi:delpi | .008 | .297 | .389 | **.514** |

Position 1 is nearly never selected (0–9%); position 4 dominates
(36–58%). The mechanism is **recency/last-position attraction** — not
primacy — confirmed by doc 156's observation that davi *gained* share
moving from pos1 to pos4 under reversal.

delpi correct-rate by position: pos1 3/360, pos2 75/360, pos3 94/360,
pos4 113/360 — correctness tracks pick position, not semantics.

### 5.3 Relative order effect (record prompts, n=360 per cell)

| Condition | Strict acc |
|---|---|
| delpi BEFORE teo | 17.8% |
| delpi AFTER teo | **61.4%** |
| delpi BEFORE vista | 21.7% |
| delpi AFTER vista | **57.5%** |
| delpi BEFORE davi | 30.8% |
| delpi AFTER davi | **48.3%** |

Delpi placed after the specialist/doc groups roughly doubles-to-triples
record-ask accuracy. Conversely delpi-first + davi-last (perms 21, 23)
is catastrophic: strict 5–6/60 with 14–26 invalid outputs — the model
locks onto the last-listed group.

### 5.4 Variance separation

- Between permutations: accuracy stdev .13, range .45 — dwarfs
  within-condition noise.
- Within permutation (5 identical reps per prompt): 5–12 of 12 prompts
  show inconsistent picks across reps — RUN_VARIANCE is real but
  bounded (~±15% per doc-156 A/A bands).
- ORDER_EFFECT therefore >> RUN_VARIANCE for extreme permutations;
  neighboring perms in the mid-range are within variance of each other.

## 6. WP6 — Stage-1 holdout (pre-declared perm set)

Pre-declared BEFORE observing holdout results: `{0 canonical, 5, 14,
16, 21, 23}` — best/worst/reversed/intermediate from the base matrix.
8 unseen prompts × 5 reps × 6 perms = 240 calls:

| Perm | Order | Strict/40 | Lenient/40 | Invalid | Top pick |
|---|---|---|---|---|---|
| 0 canonical | — | 9 | 10 | 1 | vista 19 |
| 5 | davi delpi vista teo | 13 | 13 | 0 | teo 27 |
| 14 best-base | vista teo davi delpi | **22** | 22 | 1 | delpi 26 |
| 16 | vista delpi davi teo | 20 | 20 | 1 | teo 19 |
| 21 worst-base | delpi teo vista davi | **1** | 10 | **17** | davi 12 |
| 23 reversed | delpi vista teo davi | **1** | 17 | **11** | davi 23 |

Holdout reproduces the ordering gradient: best-perm 22/40 vs worst-perm
1/40; delpi-first+davi-last again collapses to davi with high invalid
rates. `GENERALIZATION=PASS`.

## 7. WP7 — E2E confirmation (pre-declared subset {0, 14, 21, 23})

480 governed turns via the existing eval harness (`EVAL_PERM_ORDER`
seam — the serialized `capability_groups` list permuted post-projection,
same wire-level mechanism as the stage-1 probe). Exclusive-matrix
aggregation (`catalog_presentation_aggregate.py`):

| Arm | Strict group-sel | Lenient | Admission-stop | Invalid | Strict wrong-owner | Outcome PASS | Median ms |
|---|---|---|---|---|---|---|---|
| p0_base (canonical) | 5/27 (19%) | 5/27 | 23/60 | 0 | teo 10, vista 11 | 20/60 | 1723 |
| p14_base (delpi last) | 24/35 (69%) | 24/35 | 17/60 | 0 | delpi 7 | 16/60 | 3757 |
| p21_base (delpi first, davi last) | 1/36 (3%) | 17/36 | 14/60 | 15 | davi 19, vista 1 | 19/60 | 2030 |
| p23_base (reversed) | 9/28 (32%) | 14/28 | 27/60 | 0 | davi 5 | 10/60 | 3625 |
| p0_holdout | 10/22 (45%) | 10/22 | 13/40 | 0 | vista 8, teo 2, davi 2 | 15/40 | 4708 |
| p14_holdout | 9/22 (41%) | 10/22 | 12/40 | 3 | delpi 7, davi 1 | 15/40 | 3375 |
| p21_holdout | 5/23 (22%) | 7/23 | 12/40 | 2 | davi 2 | 15/40 | 2533 |
| p23_holdout | 1/22 (5%) | 12/22 | 13/40 | 0 | **davi 21** | 15/40 | 5189 |

Notes:

- The delpi-last perm (14) triples strict group selection on base
  (69% vs 19% canonical) but **business outcome does not improve**
  (16/60 vs 20/60 PASS) — correct owner selection still dies at
  capability selection, argument fidelity, or downstream stages. The
  stage-1 improvement does not propagate; H6/upstream-downstream
  limits dominate end-to-end.
- Lenient ≥ strict on bad perms because the model's davi lock counts
  as a "legitimate discovery route" — confirming why strict is the
  primary reference.
- Invalid structured output e2e: 15/60 on p21_base — the
  delpi-first+davi-last pathology reproduces in the real pipeline.

## 8. WP8 — Security

- Canonical IDs untouched in all 24 permutations; proposal contract
  still returns real published ids.
- No invented group accepted (invalid outputs fail closed).
- Zero AuthZ bypasses, PREPARE/ACT attempts, or writes.
- No secrets in artifacts; payloads contain catalog metadata only.

## 9. WP9 — Causal hypotheses

| H | Verdict | Evidence |
|---|---|---|
| H1 absolute position | **SUPPORTED** | pos1 ~0–9% picks, pos4 36–58%; monotone gradient |
| H2 relative ordering | **SUPPORTED** | delpi-after-{teo,vista,davi} 2–3× delpi-before |
| H3 stable group preference | **INCONCLUSIVE→weak** | last-position dominates regardless of identity; residual id-level bias (davi collapse under delpi-first perms) suggests interaction, not pure stability |
| H4 stochastic variance | **PARTIALLY** | within-perm spread real but bounded; cannot explain 5↔32/60 range |
| H5 interaction effect | **SUPPORTED** | invalid output concentrates in delpi-first+davi-last perms (26, 14) — order × catalog interaction, not uniform fragility |
| H6 model capacity | **INCONCLUSIVE** (by design) | no alternative model authorized; consistent with capacity limits |

## 10. Verdict

**`ORDER_EFFECT_CONFIRMED`** — reproducible, large (6.4× accuracy
spread), generalizing to holdout, structurally distinct from run
variance. The mechanism is dominated by **last-position attraction**
with a delpi-first+davi-last catastrophic interaction that also
degrades structured-output validity.

This is a model-level fragility in consuming the group surface — not a
catalog defect and not a mandate to reorder production (which would be
a provider-coupled heuristic masking semantic failure).

Recommended next bounded steps (each separately authorized):

1. **Model-capacity comparison** on this frozen permutation matrix —
   the cleanest separation of H6 from catalog/surface causes.
2. **Architecture decision** on whether stage-1 surface design should
   mitigate recency sensitivity (e.g., contract-level measures) —
   *not* a provider-ordering policy.

## 11. Artifacts

- `delia-api/scripts/order_robustness_probe.py` — 24-perm stage-1
  matrix runner (interleaved, payload-captured).
- `delia-api/scripts/order_robustness_aggregate.py` — positional/
  relative/variance aggregation over the exclusive matrix.
- `instruction_conflict_eval.py` — `EVAL_PERM_ORDER` eval-only
  permutation seam (extends the doc-156 reorder seam).
- `docs/.../evidence/order-robustness-stage1-runs.json|.jsonl`
  (1440 records), `order-robustness-holdout-runs.json` (240),
  e2e permutation artifacts.
- Execution ledger updated.


## Independent coordination review — 2026-10-26

**VERDICT=ACCEPT_WITH_RESIDUAL (diagnostic), DEPLOY_AUTHORIZED=NO.** Independent static inspection of commit `001e3cc55c70328c4c1d3bc84dd567cf7375a67e`, order_robustness_probe.py, order_robustness_aggregate.py, EVAL_PERM_ORDER seam and executor report; 1440 stage-1, 240 holdout, 480 E2E executions not independently rerun. Evaluation-specific files only; no production code/instruction changes in reviewed diff. Review takes effect for frozen evaluated application tree, not for later concurrent commits.

**Verified method:** evaluator permutes the *serialized* projected group list without recompaction, maintaining 5989 characters, 4 groups, scope and capability fields; 24 distinct permutation payloads reported and all 24 permutations tested. Interleaving across repetitions helps temper temporal confounds. Strong reported selection instability: strict stage-1 5/60–32/60 across permutations, holdout p14 22/40 vs p21/p23 1/40, and E2E p14 24/35 vs canonical 5/27 base; business outcome unchanged. This supports `ORDER_EFFECT_CONFIRMED` in this environment and catalog. The label `recency` remains mechanistic interpretation rather than established cause; position-4 selection dominance may mix label/ID lexical interactions with order. No production sorting/ranking policy is authorized.

**Measurement residuals:** aggregator `_acc` computes `GROUP_CORRECT/reached`, excluding correct no-owner abstentions from numerator; name it strictly `selected-owner-correct / stage-decisions`, not overall semantic decision accuracy. `inconsistent_prompts` counts prompts with >1 selected group over five reps and is NOT variance decomposition or confidence interval. Pairwise relative-order comparisons pool different permutations and can be confounded by absolute positions; use paired position-controlled contrasts to make causal claims about before/after individual groups. The report provides min/max/stdev but no uncertainty interval or multiple-comparison correction for selecting best/worst. Holdout confirmation of p14/p21 is useful but those permutations were chosen on training matrix, so avoid unbiased estimates of best-permutation generalization.

**Oracle/security constraints:** strict oracle scores direct record owner only, lenient permits DAVI discovery route; neither is proof of authoritative retrieval. Any `GROUNDED` or outcome PASS must remain separately validated against concrete requested records and source evidence. Zero AuthZ bypass/unapproved ACT is executor-reported and has not been independently run. Document known deployment gap for unknown effective model-window configuration separately; experiment does not close it.

**Next direction:** accept diagnostic, **stop trying to solve routing by fixing list order**. Because improved selection does not produce record outcomes, prioritize a bounded causal characterization of downstream capability/argument fidelity with forced **test-harness-only, contract-valid selected group** (no production routing override) to isolate where known-good group selection stops producing results; also separately consider an authorized same-corpus model comparison. Do not conflate improved group selection with Business Outcome or authorize a runtime workaround without independent end-to-end evidence.
