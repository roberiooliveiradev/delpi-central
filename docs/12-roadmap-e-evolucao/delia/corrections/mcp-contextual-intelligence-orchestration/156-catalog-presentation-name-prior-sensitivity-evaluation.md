# 156 — Catalog Presentation Name-Prior Sensitivity Evaluation

**Task**: `DELIA-C3-CATALOG-PRESENTATION-NAME-PRIOR-SENSITIVITY-EVAL-01`
**Type**: read-only controlled diagnostic experiment. No production code,
instruction, catalog, model, or configuration changes. Evidence-only commit.
**Follows**: `155-group-selection-instruction-semantic-conflict-experiment.md`
**Independent review consumed**: `479a8a78f1b7105a7f55150385871d75b9287b9e`

## 1. Reanchoring

- `BASE_SHA`: `148b4e0a3af101069db10c79324ef6e128dc37ae` (consulted HEAD).
- Working tree fast-forwarded to upstream tip at task start; concurrent work
  preserved. The `delia-api` tree is identical to the document-155 baseline —
  all comparison data from 155 remain on the same code surface.
- Authorities read: canonical engineering rules (`.cursor/rules/`),
  `AGENTS.md`, documents 150–155, independent review `479a8a78`, execution
  ledger. No contract incompatibilities found — no
  `ARCHITECTURE_DECISION_REQUIRED` was triggered.
- Environment: `c3r-eval` container with `delpi-delia-api`, `delpi-ollama`,
  `delpi-keycloak`, `delpi-gateway`. Keycloak required restart once before
  token minting (environmental, documented).

## 2. Reuse gate

| Field | Value |
|---|---|
| `EXISTING_EQUIVALENT` | `scripts/instruction_conflict_eval.py` (e2e runner), `instruction_conflict_stage1_probe.py` (stage-1 isolation), `instruction_conflict_aggregate.py` (metrics); production `_group_summaries`, `_group_scope_text`, `_select_group`, `_projected_capability_ids`, `CapabilityGroup`, `ProviderCapability`, `SourceRef`; instruction resource v23; model invocation port; `MAX_SURFACE_CHARS=6000`. |
| `REUSE_DECISION` | Reuse all. New code limited to (a) an env-gated in-process catalog-presentation seam inside the existing harness, (b) a new stage-1 presentation probe, (c) a corrected aggregator. |
| `RESPONSIBILITY` | Evaluation-only projection variant of model-visible group bodies. |
| `OWNER` | `scripts/` harness layer — no runtime composition impact. |
| `CONSUMERS` | This experiment only. |
| `CONTRACT` | Canonical group IDs, capability IDs, owner refs, `source_system`, `remote_name`, schemas, AuthZ, operation classes, eligibility unchanged. The proposal contract still returns real published IDs. |
| `SECURITY_BOUNDARY` | `CATALOG METADATA != INSTRUCTION`, `DISPLAY LABEL != AUTHORITY`, `MODEL GROUP SELECTION != AUTHORIZATION`, `READ != WRITE`, `PREPARE != ACT`. In-process only; nothing persisted to the live catalog. |

No new planner, registry, catalog, or routing rule was introduced.

## 3. WP0 — Oracle and metric correction

The prior aggregator could increment `correct` when `applicable=false`
without incrementing `eligible` — inflating a selection metric with
non-selection outcomes. Corrected in
`scripts/catalog_presentation_aggregate.py`:

Exclusive per-run selection classification (exactly one bucket each):

```
ADMISSION_STOP               — turn ended before group selection
GROUP_CORRECT                — selected group satisfies oracle
GROUP_WRONG                  — selected group violates oracle
GROUP_NOT_APPLICABLE_CORRECT — correctly abstained on no-owner prompts
GROUP_NOT_APPLICABLE_WRONG   — selected a group on no-owner prompts
GROUP_INVALID_OUTPUT         — unparseable/missing structured output
GROUP_NOT_REACHED_OTHER      — other upstream failure
```

Metrics use stage-specific denominators: group-selection accuracy excludes
admission-stop; no-owner accuracy uses only no-owner scenarios; invalid rate
uses proposals at the stage.

**Oracle reconciliation**: record-family prompts accept `openapi:delpi`
(direct search) as strict-correct, and `mcp:davi` (discovery→execute route)
as lenient-correct — a legitimate available path to the objective. Both
numbers are reported; the lenient column is marked. No-owner prompts
(greeting, unauthorized delete) require abstention for correctness.

## 4. WP1 — Frozen baseline

| Field | Value |
|---|---|
| `EVALUATED_SHA` | `148b4e0a3af101069db10c79324ef6e128dc37ae` |
| `MODEL_ID` | `delia-json:latest` (`qwen2.5:3b`, Ollama) |
| `CONTEXT_WINDOW_EFFECTIVE` | 8192 (`num_ctx`), surface budget 6000 chars |
| `INSTRUCTION_VERSION` | v23, fingerprint `8eb95ebdafe8b338` |
| `CATALOG_SNAPSHOT_HASH` | `916c063b67e54cd6da9802b77d4fb36a97f904c5c80796dc41d7a8a991608e6d` (sha256 of the exact serialized stage-1 surface) |
| Catalog snapshot | `docs/.../evidence/catalog-presentation-snapshot.json`: `mcp:davi` 2 caps, `mcp:teo` 23, `mcp:vista` 12, `openapi:delpi` 4 (41 total) |
| `SEED` | not supported by the stack — determinism limitation declared |

## 5. Structural finding — what actually reaches the model

The live stage-1 payload (5989/6000 chars) contains per group **only**:

```json
{"capability_group_id": "...", "capabilities": [...],
 "scope": "...", "capabilities_omitted": 1}
```

`display_name`, `owner`, and `source_system` are **compacted out** by the
budget ladder before dispatch — verified in the exact serialized payload
(`display_names: [null×4]` on every run).

Consequence: document 155's "renamed providers" gain (35/50 vs 16/50) could
not have come from display labels — that experiment rewrote
`capability_group_id` strings themselves. The effect lives in the
**canonical identifier tokens**, not in any non-authoritative label.

## 6. WP2 — Variants and validity gates

| Variant | Model-visible change | Wire result |
|---|---|---|
| A `real` | none (baseline) | sha `916c063b…` |
| B `neutral` | `display_name`→"Grupo A/B/C/D", `owner`→"OWNER-N" | **identical sha `916c063b…`** |
| C `respforward` | `display_name` replaced by capability-derived description, owner blanked | **identical sha `916c063b…`** |
| D `reorder` | reversed group list order | sha `e0328e74…` (same 5989 chars) |

Gate results for B and C: `CANONICAL_IDS_IDENTICAL=YES`,
`OWNER_IDENTITIES_IDENTICAL=YES` (authority object untouched — only the
projected label string was rewritten in-process), `CAPABILITY_IDS/REMOTE_NAMES/
SCHEMAS/SCOPE/DESCRIPTIONS_IDENTICAL=YES`, `DISPLAY_FIELDS_CHANGED=YES`.
Per the task contract these variants are valid — but the experiment also
proves their changed fields never survive to the wire, so they function as
**A/A replicates** measuring run-to-run model variance on identical input.

## 7. WP4 — Stage-1 isolation results (240 calls)

12 prompts (6 record, 3 doc, 1 discovery, 2 no-owner) × 5 reps × 4 variants:

| Variant | Payload sha | Valid sel. | Correct (lenient) | Correct (strict) | Notable distribution |
|---|---|---|---|---|---|
| A real | `916c063b` | 60/60 | 27/60 | 24/60 | teo 21, vista 24, delpi 7, davi 8 |
| B neutral | `916c063b` (identical) | 59/60 | 26/60 | 25/60 | teo 22, vista 26, delpi 5, davi 6 |
| C respforward | `916c063b` (identical) | 57/60 | 21/60 | 20/60 | teo 29, vista 18, delpi 7, davi 3 |
| D reorder | `e0328e74` | 47/60 | 28/60 | **5/60** | **davi 46**, invalid 13, vista 1, teo 0 |

Interpretation:

- A/B/C spread (21–27/60) on **byte-identical input** is the model's own
  stochastic noise band (~±15%). No label effect is measurable because no
  label reaches the wire.
- D shows **extreme ordering sensitivity**: under reversed order the model
  collapsed onto `mcp:davi` for 46/60 prompts — including all three doc
  prompts (teo was correct 5/5 in every other variant) — and produced 13
  abstentions/invalids where A had 0. Davi moved from first position
  (sorted order) to last yet *gained* share, so this is not simple primacy;
  the reorder itself destabilized selection — consistent with a
  recency/anchoring failure at this model scale. The probe's lenient
  28/60 "correct" for D is inflated by the same mechanism later seen e2e:
  record asks dominate the corpus and davi counts lenient-correct for
  them; strict owner accuracy on the reorder arm is far lower.
- No-owner prompts: `apague o produto…` still attracted group selections
  (vista/teo) in all variants — security boundaries are enforced downstream,
  unchanged by variants (0 bypasses observed).

## 8. WP5 — End-to-end arm

`real` vs `reorder` on the base (12 scenarios) and holdout (8) corpora ×
5 reps = 200 governed turns. The e2e reorder seam reverses the serialized
`capability_groups` list inside the same `_group_summaries` contract (the
provider-return order alone cannot move presentation because keys are
sorted) — so the wire payload provably differs; this is a real variant.

| Arm | Lenient acc | Strict acc | Invalid | Admission-stop | Outcome PASS |
|---|---|---|---|---|---|
| real_base | 16/37 (43%) | 15/37 (40%) | 0/37 | 13/60 | 16/60 |
| reorder_base | 29/40 (72%) | **4/40 (10%)** | 3/40 | 10/60 | 19/60 |
| real_holdout | 11/25 (44%) | 11/25 (44%) | 0/25 | 10/40 | 15/40 |
| reorder_holdout | 10/24 (42%) | **0/24 (0%)** | 7/24 | 11/40 | 15/40 |

The lenient/strict divergence is the signature of the positional collapse:
under reversed order the model converges on `mcp:davi` (strict
wrong-owner distribution: davi 29 base, 17 holdout — versus 1 in real).
Because the lenient oracle accepts the DAVI discovery→execute route as a
legitimate path for record asks, lenient accuracy *rises* while strict
owner accuracy collapses — the model is not selecting better, it is
anchoring on a different group regardless of the ask. Doc-ask scenarios
(guide/h_doc/disc) are the honest discriminator: real order keeps them
viable; reorder drives them to davi or invalid output.

Wrong-owner distribution (strict, applicable proposals):

- real_base: teo 9, vista 9, davi 1 — spread across specialists
- reorder_base: davi 29, teo 2, vista 1 — single-anchor collapse
- real_holdout: vista 12, teo 1, davi 1
- reorder_holdout: davi 17, invalid 7

Invalid-output rate under reorder: 3/40 base, 7/24 holdout versus 0 in
real order — reordering not only shifts picks, it degrades structured
output validity.

## 9. WP6 — Causal classification

| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 display-name prior | **NOT TESTABLE → not confirmed** | Changed fields compacted out; byte-identical payloads |
| H2 canonical-ID prior | **SUPPORTED** | Doc-155 renamed-provider gain is now attributable entirely to `capability_group_id` tokens — the only identity string on the wire |
| H3 positional bias | **SUPPORTED** | Reorder collapsed selection to a single group (davi 46/60) and raised invalids 0→13 |
| H4 scope ambiguity | **INCONCLUSIVE** | Scope survives compaction, but selection errors persist even with scope present; cannot separate from ID-prior at this model scale |
| H5 model capacity | **SUPPORTED** | Large run-to-run variance on identical input; cannot hold stable group mapping under reorder |
| H6 upstream/downstream | **SUPPORTED** | E2e failures persist at admission/capability/argument stages independently of group selection |

## 10. Security

- Zero invented IDs accepted; proposal contract still returns real
  published `capability_group_id` values.
- Zero AuthZ bypasses, zero PREPARE/ACT attempts, zero unauthorized writes.
- Injection text in catalog descriptions remained inert in doc-155 testing;
  this task introduced no new injection surface (variants only relabeled).
- Canonical IDs, owner identity, `source_system`, provenance untouched.

## 11. Experiment verdict

**`NAME_PRIOR_NOT_CONFIRMED`** — for display labels specifically. The
hypothesis that *non-authoritative presentation labels* drive misrouting is
refuted in the only form testable under current contracts: those labels
never reach the model. What doc-155 measured was **canonical-identifier
prior sensitivity** (`capability_group_id` tokens) plus strong positional
fragility — both properties of the wire surface, not of display metadata.

The next bounded interventions this evidence supports (each its own task):

1. **A separately authorized wire-level experiment** measuring whether
   `capability_group_id` token content drives selection — e.g., comparing
   accuracy on catalogs where only the ID strings differ, which requires an
   architecture decision because it touches canonical identifiers.
2. **Order-robustness hardening evaluation** on the current frozen corpus
   (the positional collapse is the largest single reproducible defect
   observed: one permutation destroyed doc-ask accuracy 15/15 → ~2/15).
3. **Model-capacity comparison** on the same frozen corpus, since variance
   on byte-identical input (~±15%) dominates every label-level manipulation.

## 12. Artifacts

- `delia-api/scripts/instruction_conflict_eval.py` — env-gated catalog-variant
  seam (`EVAL_CATALOG_VARIANT`), evaluation-only.
- `delia-api/scripts/catalog_presentation_probe.py` — stage-1 probe with
  exact dispatched-payload inspection.
- `delia-api/scripts/catalog_presentation_aggregate.py` — corrected exclusive
  confusion-matrix aggregator.
- `docs/.../evidence/catalog-presentation-snapshot.json` — frozen catalog
  surface (sanitized).
- `docs/.../evidence/catalog-presentation-probe-runs.jsonl` (+ `.json`
  wrapped form) — 240 stage-1 run records with payload sha/chars/
  field-survival per call.
- `docs/.../evidence/catalog-presentation-e2e/{real_base,reorder_base,
  reorder_holdout,real_holdout}.json` — 200 governed e2e turns
  (sanitized; no token material).
- Execution ledger updated.
