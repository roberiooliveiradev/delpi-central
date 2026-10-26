# 154 — Group Selection Semantic Signal Preservation

> **Status:** IMPLEMENTED_WITH_EVIDENCE — bounded projection fix,
> contract tests green, controlled before/after eval recorded.
> Independent review pending. Deploy not authorized.
>
> **Task:** `DELIA-C3-GROUP-SELECTION-SEMANTIC-SIGNAL-PRESERVATION-01`
> **Baseline eval:** Documento 153 · **Review:** `1b649bb095f5`

## 1. Defect reproduced

Stage-1 `_select_group` dispatches `_group_summaries(groups)`. On the
live 4-group / ~41-capability surface the compaction ladder zeroed
**every** capability description: `nonempty_descs 0/41`,
payload 5 909–5 969 chars under `MAX_SURFACE_CHARS=6 000`. The model
picked owners from `remote_name`/`display_name` alone — doc 153
measured GROUP_SELECTION_ERROR as a top divergent stage.

## 2. Contract review & reuse gate

```
EXISTING_EQUIVALENT=YES   REUSE_DECISION=EXTEND
OWNER   = _group_summaries (projection builder)
CONSUMERS = _select_group (stage-1), _select_foreign_capability
CONTRACTS = CapabilityGroup (no description field), SourceRef (no
            description field), MAX_SURFACE_CHARS=6000 (unchanged),
            _projected_capability_ids/_names (unchanged),
            instruction resource versioned (22 → 23)
```

`CapabilityGroup`/`SourceRef` carry **no** owner description — the
fallback licensed by WP1 §7 applies: a deterministic compact
projection of the capability descriptions the owner already
publishes. No new contract field on the dataclasses; `scope` is a
projection-only field inside the dispatched JSON block.

## 3. Design — `scope`

Per-group `scope` = verbatim prefix excerpts of the group's
published capability descriptions, `; `-joined,
≤ `MAX_GROUP_SCOPE_CHARS=160` per group (per-desc excerpt ≤ 60):

- **Deterministic & provider-neutral** — catalog order, no ranking,
  no keywords, no provider/material names in code.
- **Faithful** — verbatim prefixes only; nothing paraphrased,
  invented or recalled from model knowledge.
- **Absent when source is silent** — a group with no published
  descriptions simply omits the field; never fabricated.
- **Untrusted data** — same boundary as names/descriptions;
  instruction v23 states it explicitly.
- **Compaction priority** — `scope` is the *last* field shrunk
  (160 → 96 → drop) in the fit ladder: descriptions compact first,
  then observation, then nonessential metadata, then tail
  capabilities (truthful `capabilities_omitted`), then scope. No
  group is ever omitted; identifiers stay verbatim.

Live surface after fix (probe, same conditions as doc 153):

```
mcp:davi   scope "Find the governed DELPI READ capability…;
           Execute one candidate…"                          caps 2
mcp:teo    scope "Minimal personal context…; Current
           Transformômetro workspace…"                caps 22 (–1)
mcp:vista  scope "Lista as programações (playlists)…;
           Retorna o contexto compacto…"                   caps 12
openapi:delpi scope "Buscar produtos DELPI; Resumo de
           produto DELPI; Estoque…; Buscar clientes DELPI" caps 4
payload 5 908–5 989 chars — all 4 groups, valid JSON, ≤ 6 000
```

## 4. Tests — RED → GREEN

`tests/test_group_selection_semantic_signal.py` — 17 cases:

| | |
|---|---|
| A1 | live-shape 4×41 surface: descs zero, scope non-empty & ≤160 |
| A1b | scope is verbatim owner excerpt, not fabricated |
| A2 | all groups identifiable under pressure |
| A3/A3b | payload ≤ 6 000 & valid JSON across shapes (8 groups too) |
| A4 | 30-cap group doesn't starve 2-cap group's scope |
| A4b | no source descriptions → field absent, no fabrication |
| A5 | injection text in description stays inert data |
| A5b | every scope fragment is a verbatim prefix of source |
| A6 | omitted capability id absent from `_projected_capability_ids` |
| A6b | stage-2 `_capability_payload` names contract unchanged |
| A7 | renaming/reordering groups changes nothing but names |
| A8 | ids & remote names verbatim |
| A9 | extreme pressure → valid honest JSON, truthful markers |
| +2 | scope fairness & absent-only-when-source-empty |

**Causal RED on baseline:** 10 of 17 fail on the pre-fix checkout
(scope never emitted) — including the live-shape case where every
description is compacted to `""`.

Version-pin updates: `test_r1_instruction_resource` (snapshot sha
for the two touched instruction entries), `test_c3_*` and
`test_projection_omission_recovery_contract` version "22"→"23".

## 5. Controlled before/after eval — honest result

Same model (`delia-json` qwen2.5:3b, ctx 8192), same delegated
READ-only bearer class, same 12 scenario subset × 5 reps = 60 runs
each, same eval script/classifier:

| Metric | BEFORE (v22, no scope) | AFTER (v23 + scope) |
|---|---|---|
| outcome PASS | 10/60 | 15/60 |
| GROUP_SELECTION_ERROR | 25 | 25 |
| ADMISSION_ERROR | 18 | 12 |
| CAPABILITY_SELECTION_ERROR | 4 | 6 |
| invalid structured output | 8 | 5 |
| INCONCLUSIVE | 4 | 5 |
| groups chosen (all runs) | delpi 10, teo 13, vista 4 | delpi 9, teo 4, **vista 23** |
| model calls / tokens | 246 / 386 k in | 251 / 432 k in |

**What changed:** `disc_candidate` 0→5/5 PASS (the model now answers
the surface inquiry against a described catalog); admission errors
down 18→12; structured-output errors down 8→5.

**What did NOT change:** GROUP_SELECTION_ERROR stayed at 25/60 and
wrong-owner picks *moved* — teo 13→4, vista 4→23. Product queries
still misroute; `biz_bala3`/`nom_technical` picked `mcp:vista` 5/5.

### Reading the result

The defect fixed is **real and proven**: scope now delivers verbatim
owner signal inside budget (0/41 → 4/4 groups signalled). But the
eval refutes the naive expectation that restoring descriptions alone
fixes 3B routing:

1. The model still misroutes with signal present — either it ignores
   `scope`, or `mcp:vista`'s playlist/data-route wording attracts
   "search-like" phrasings. This is **model-capacity evidence
   (direction C)**, not a projection defect.
2. Instruction v22/v23 *itself* steers colloquial subjects to a
   "documentation or knowledge surface FIRST" — "terminal bala" is
   colloquial, so teo/vista picks are partially **instruction-
   compliant** routing whose outcome fails downstream. That is a
   bounded **instruction-semantics candidate (direction B)** — a
   separate experiment, not this task.
3. `records` outcome stays 0 — next divergent stages downstream
   (admission misclassification, capability/argument fidelity)
   still gate business results; they were never in this task's
   scope.

## 6. Regression

- Focused: new suite (17) + selection envelope + outcome/payload +
  projection/recovery + C3 + R1 resource — **all green**.
- Full backend in container: 0 FAILED/ERROR to 100%.
- Architecture gates (backend boundaries, phase-3, platform
  guardrails): 0 findings.
- AUTHZ unchanged; PREPARE/ACT untouched; READ-only eval only.
- Secrets: eval bearer/env destroyed post-run; none in diff.

## 7. Residuals & next bounded steps

- `disc_candidate` improved; record-family outcome unchanged —
  evidence now cleanly separates *signal availability* (fixed) from
  *signal use* (model/instruction).
- Recommended next: bounded **instruction experiment** isolating the
  colloquial-subject "documentation-first" clause (direction B from
  doc 153), on the same frozen corpus; then re-measure before any
  model-capacity decision (direction C).
- `scope` shrink-to-96/drop ladder is exercised only in synthetic
  extreme-pressure tests; real surface fits at full 160.
- `_select_foreign_capability` shares the same block — foreign
  selection gains the same signal for free; no consumer change
  needed beyond the instruction note.
