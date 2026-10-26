# 158 — Downstream Capability & Argument Fidelity Causal Evaluation

**TASK_ID:** `DELIA-C3-DOWNSTREAM-CAPABILITY-ARGUMENT-FIDELITY-CAUSAL-EVAL-01`
**Type:** Controlled causal diagnostic evaluation — evidence only.
**Primary evidence:** Document 157 (order robustness) + independent review `bd39b10`.

## 1. Reanchoring

```
BASE_SHA=bd39b100017d51d76129ebe5e06d0abd09777e2d
EVALUATED_SHA=bd39b10 (application tree; identical at evaluation time)
FINAL_HEAD=8176be1a3683c1f21e1c81f01611167951d8ea67
ORIGIN_MAIN=76e5c2553c (ff-rebase applied — concurrent cf docs only)
AUTHORITIES_READ=review bd39b10, docs 151–157, execution ledger, rules
CURRENT_PHASE=Context Intelligence — causal characterization
CP_RQ=downstream capability/argument fidelity
CONCURRENT_WORK_PRESERVED=YES (cf-docs commits kept; scope disjoint)
```

`delia-api/app/.../orchestration.py`, CRI instruction resource, catalogs,
and model config were **not** modified. All interventions live only in
`scripts/downstream_causal_eval.py` (test harness).

## 2. WP0 — Inventory & Reuse Gate

```
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND — reused _compose/_mint_bearer/_spy_propose/
  _run_turn/classify/_StageLog from semantic_fidelity_eval.py and the
  existing Scenario corpus; added downstream_causal_eval.py +
  downstream_causal_aggregate.py (eval-only) and armd_stage_debug.py
  (one-turn stage tracer, eval-only).
OWNERS=scripts/ harness layer only
CONTRACTS_REVIEWED=_select_group, _select_capability(+_with_goal),
  _select_foreign_capability, _build_arguments, _build_plan,
  _resolve_missing_inputs, _invoke_selected, _invoke,
  interaction_admission, native_assessment, foreign_selection,
  goal_evidence_relevance — all preserved unchanged.
```

## 3. WP1 — Frozen baseline

```
MODEL_ID=delia-json:latest (qwen2.5:3b, Ollama) — unchanged
MODEL_CONFIG=num_ctx 8192, no seed (NOT_SUPPORTED), default temp
CONTEXT_WINDOW_EFFECTIVE=8192 / surface 6000
INSTRUCTION_VERSION=v23 fp 8eb95ebdafe8b338
CATALOG_SNAPSHOT=live surface, 4 groups / 41 caps when healthy:
  mcp:davi(2) mcp:teo(23) mcp:vista(12) openapi:delpi(4)
```

## 4. WP2 — Authoritative oracles

11 record-family scenarios (4 base direct/code, 4 nomenclature,
3 holdout incl. `h_amb_broad`). Oracles built by authorized READ of the
owner (`delpi.search_products{description:<subject>}` /
`delpi.get_product_summary{code}`) before any run:

```
ORACLES_VERIFIED=11/11 (COMPLETED, codes 1–50 per scenario)
ORACLES_PARTIAL=0   ORACLES_UNAVAILABLE=0
```

## 5. WP3–WP6 — Arms and engagement

Four cumulative harness-only arms; interventions return real published
identifiers / real catalog objects / contract-valid oracle args. Every
run records `controls_engaged` — a CONTROLLED mark is emitted only
when the wrapper actually fired (the offered group set can legitimately
exclude `openapi:delpi` on non-operational admission paths).

```
A natural          engaged= 0/55  (baseline)
B good_group       engaged=37/55  (delpi absent from surface or
                                   selection not reached elsewhere)
C good_capability  engaged=41/55  (group+cap fired)
D good_arguments   engaged=41/55  (args fired in 3 of those)
REPETITIONS=5, interleaved rep→arm→scenario; TOTAL_RUNS=220 valid
runs on a verified-healthy surface (4 groups, 0 failures).
```

Integrity: canonical group/cap IDs real and catalog-present; schemas,
descriptions, AuthZ, downstream instructions unchanged; no WRITE /
PREPARE / ACT anywhere (all caps exercised are READ).

## 6. Results — WP9/WP12 matrix

| Arm | engaged | delpi COMPLETED invokes | GROUNDED | BUSINESS PASS |
|-----|---------|-------------------------|----------|---------------|
| A   | 0/55    | 0                       | 55       | **0/55** |
| B   | 37/55   | 2                       | 55       | **1/55** |
| C   | 41/55   | 4                       | 55       | **1/55** |
| D   | 41/55   | 3                       | 55       | **1/55** |

All 3 PASSes are `biz_code`/`h_rec_code2`-family (`get_product_summary`
with an explicit code) — the exact-identifier path. The multi-record
search path never completed a business outcome.

## 7. First-divergent-stage distribution (healthy surface)

```
A (natural):   ADMISSION:surface_inquiry 20 | GROUP:wrong 28 |
               CAPABILITY:abstain 2 | foreign/invoke misc 5
B (grp ctl):   ADMISSION 18 | CAPABILITY:abstain 16 |
               FOREIGN_DIVERT ~12 | ARGS 1 | EVIDENCE_REJECT 1 | PASS 1
C (cap ctl):   ADMISSION 13 | FOREIGN_DIVERT ~37 |
               EVIDENCE_REJECT 3 | PASS 1
D (args ctl):  ADMISSION 14 | FOREIGN_DIVERT ~37 |
               EVIDENCE_REJECT 2 | PASS 1
```

### Stage-level findings

1. **`interaction_admission` (pre-selection, ~40–55% of turns)** —
   record asks classified `surface_inquiry` (deterministic surface
   listing; honest) or `hypothetical`/`ambiguous` (reduced surface —
   in one observed path only 2 doc groups offered; fabricated
   "hypothetical" examples, disclaimed + NON_GROUNDED). `operational`
   admission only ~5–16%.

2. **`native_assessment → foreign_selection` diversion — the dominant
   downstream blocker.** Even with group+capability+arguments all
   contract-correct (arm D), `native_assessment` declares
   `foreign_evidence_required` and `foreign_selection` picks
   doc-family capabilities (`teo.get_product_guide`,
   `vista.get_catalog`, `teo.get_my_context`, …) instead of
   `davi.discover_delpi_information` or the already-selected native
   path. ~37/41 engaged runs in C and D die here. These turns never
   reach `_build_arguments`/`_invoke_selected` — which is why arm D's
   argument control engaged only 3×.

3. **`_select_capability` abstention** — with `openapi:delpi` forced
   and all 4 record capabilities presented, the model answers
   `{"applicable": false, "remote_name": null}` while still extracting
   `business_subject="terminal bala"` correctly — 16/37 engaged runs
   (43%) in arm B. It understands the goal; it does not bind the
   capability. When it does pick, picks are mostly right
   (`search_products` 16, `stock`/`summary` 4, `customers` 1).

4. **`_build_arguments`** — rarely reached. When reached naturally,
   observed: hallucinated required fields (`missing_inputs:["code"]`
   on `search_products`, whose schema has none required), wrong-field
   binding, scope loss, fabricated identifiers (all classes from the
   earlier evidence re-observed in small n). When forced (arm D), the
   invoke always succeeded mechanically — 3/3 COMPLETED.

5. **Resolver** — rarely engaged; when it is, wrong-domain selection
   observed (`delpi.search_customers` for a product goal), then
   `applicable:false` → clarification dead-end. Confirms the earlier
   anec-data.

6. **`goal_evidence_relevance` — deepest confirmed divergence.** Of
   the 9 real delpi invokes across B/C/D, **6 ended with the model
   returning an empty `{}` relevance proposal → fail-closed
   "the source returned real records but they do not match the
   request"** — while the invoked arguments were byte-identical to the
   oracle query that returns the 50 pertinent records. The records
   were pertinent; the judgment produced nothing usable.

7. **Owner** — REFUTED as bottleneck: 9/9 delpi invokes COMPLETED;
   oracle READs return 1–50 pertinent records.

## 8. WP11 — Hypothesis classification

```
H1_CAPABILITY_SELECTION = SUPPORTED — 43% abstention with correct
    group surfaced (contract presented, model declines to bind).
H2_ARGUMENT_FIDELITY    = PARTIALLY SUPPORTED — real when reached
    (hallucinated requireds, wrong binding, fabricated ids) but the
    stage is rarely reached; not the dominant blocker.
H3_RESOLVER             = SUPPORTED (small n) — wrong-domain resolver
    pick + unnecessary clarification; reproduces earlier evidence.
H4_OWNER                = REFUTED — owner data and contracts healthy.
H5_EVIDENCE_RELEVANCE   = SUPPORTED — empty relevance proposals
    reject pertinent owner records (~67% of completed invokes).
H6_SYNTHESIS_OUTCOME    = INCONCLUSIVE — rarely reached; the exact-
    code path proves end-to-end works when prior stages align.
H7_MODEL_CAPACITY       = SUPPORTED for semantic stages — with all
    contracts, surface, and data correct, the model still diverts to
    wrong-domain foreign caps ~90% of engaged runs, abstains 43% on
    capability binding, and emits empty relevance judgments.
```

New stage named by this eval (not in the original list):
**`native_assessment`/`foreign_selection` semantic diversion** — the
first downstream blocker once the correct group is available. The
LLM's decision that "foreign evidence is required" for a direct
record ask, and its pick of doc-family foreign capabilities, dead-ends
~90% of runs that survived selection.

## 9. WP13 — Security & architecture gates

- Zero AuthZ bypass: all denials traced to expired JWT TTL (300 s),
   surfaced as AUTHZ_DENIED → truthful "acesso negado" — fail closed.
- Zero unauthorized ACT/WRITE/PREPARE; every exercised capability READ.
- Zero fabricated records **presented as real**: hypothetical-path
   outputs are explicitly disclaimed and NON_GROUNDED.
- Artifacts JWT/secret-scanned clean.
- `mcp_protocol_error` observed on teo/vista invokes (foreign path
   mechanically flaky, ~5–8 per arm) — reported, not masked.

## 10. Execution drift (documented)

- Two mass stack restarts during the session killed `delpi-api-delpi`
  mid-startup (DB still recovering) → `openapi_document_unavailable` →
  `openapi:delpi` silently absent from the live surface, and
  `mcp:davi` `mcp_unavailable` (same host). First 220-run batch
  partially invalidated; kept as fragility evidence only.
- Subject JWT TTL = 300 s vs ~40 min matrix → raised provider 401s
  invisible to the (success-only) invoke spy → second batch partially
  invalidated. Harness fixed: fresh bearer per turn + error-capturing
  spy (`ERROR:<code>` statuses) + engagement flags.
- Keycloak dev-realm re-import reset the eval user password on
  restart; restored via admin API (environment recovery, no config
  change).
- WSL transport blips; container-side runs unaffected (checkpoint
  resume).
- Final dataset (`downstream-causal-runs.json`, 220 runs) collected
  entirely on the verified-healthy surface (4 groups, 0 failures,
  fresh bearer/turn).

## 11. Causal decomposition (WP14)

| Stage | Evidence | Effect when controlled |
|---|---|---|
| admission | ~50% of turns die before selection | still dominant in all arms |
| group (doc 157) | A: 28/55 wrong | eliminated in B/C/D |
| **native_assessment→foreign_selection** | ~90% of engaged C/D runs divert to teo/vista doc caps | **NOT controllable by group/cap/args — the real downstream wall** |
| capability binding | 43% abstain in B | eliminated in C/D |
| arguments | hallucinated requireds, wrong binding (small n) | eliminated in D — invoke then always COMPLETED |
| resolver | wrong-domain pick (small n) | — |
| owner | REFUTED | — |
| evidence relevance | empty `{}` proposals reject pertinent records (~67% of invokes) | untouched by any arm |
| business outcome | PASS only via exact-code path | 1/55 per controlled arm |

```
EXPERIMENT_VERDICT=DOWNSTREAM_CHAIN_CAUSALLY_DECOMPOSED —
  first blocker after correct group is the native_assessment→
  foreign_selection semantic diversion (~90% of surviving turns),
  followed by capability abstention (43%), then empty relevance
  judgments (~67% of completed invokes). Argument fidelity is real
  but secondary. Owner and contracts are healthy.
RECOMMENDED_NEXT_DIRECTION=
  (a) contract review of native_assessment/foreign_selection —
      why "foreign_evidence_required" fires for direct record asks
      and why doc-family caps are selectable as record evidence;
  (b) model-capacity comparison on this frozen matrix (semantic
      stages stay fragile with correct contracts — decision class E);
  (c) NO ordering/instruction/routing patch justified by this data.
NEXT_BOUNDED_STEP=bounded native_assessment/foreign_selection
  contract+prompt-surface diagnostic (eval-only) under separate
  authorization.
```

```
INDEPENDENT_REVIEW=PENDING
DEPLOY_AUTHORIZED=NO   DEPLOY_EXECUTED=NO
FINAL_VERDICT=CAUSAL_CHARACTERIZATION_COMPLETE
```
