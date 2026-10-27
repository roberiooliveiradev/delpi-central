# DÉLIA — Documento 166 · R1.5 Semantic Judgment & Owner-Reach — Causal Investigation

**TASK_ID:** `DELIA-C3-R15-SEMANTIC-JUDGMENT-OWNER-REACH-CAUSAL-EVAL-01`
**STATUS:** `CAUSAL_INVESTIGATION_COMPLETE` — root causes proven with payload-level evidence
**TYPE:** Stage-local causal decomposition — eval-harness only, zero production change.
**BASELINE:** Documento 165 (R1, `R1_INCONCLUSIVE`) · independent review `0833c58c21` accepted at `0464cf0878`.

---

## 1. Reanchoring

| Field | Value |
|---|---|
| `BASE_SHA` | `0464cf0878` (post-review `origin/main`) |
| `EVALUATED_SHA` | `0464cf0878` — orchestration contracts ≡ runtime |
| `ORIGIN_MAIN` | `0464cf0878` at eval time |
| `WORKTREE_STATUS` | clean; only `delia-api/scripts/semantic_judgment_reach_eval.py` added |
| `CURRENT_PHASE` | C3 / R1.5 — not advanced |
| `CP_RQ` | not advanced |
| `AUTHORITIES_READ` | 16, 50, 17, 49, 51, 52, 21, 20, 25 · docs 163, 164, 165 · R1 review `0833c58c21` · ledger |

No authority conflicts. Independent R1 review requirements adopted as acceptance gates: record-level labels, actual dispatched payloads, explicit invalid/empty/inconclusive categories, separation of owner-search vs admission vs judgment causes.

---

## 2. Reuse gate (WP0)

| NEED | OWNER | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| admission contract | `orchestration._admit_conversational_turn` + `INTERACTION_ADMISSION_INSTRUCTION_ID` | YES | REUSE — same instruction, same static block, same parse |
| goal typing | `orchestration._understand_goal` + `turn_goal` instruction | YES | REUSE — real method called |
| evidence judgment | `orchestration._judge_goal_evidence` + `goal_evidence_relevance` instruction | YES | REUSE — exact production block construction + `_fit_json_block`/`_omit_tail_entries` |
| judgment parse | `outcome_assessment.parse_goal_evidence_judgment` | YES | REUSE |
| owner READ oracles | `orch._providers` + `provider.invoke` + `bind_subject_bearer` | YES | REUSE — same seam as R1 oracle |
| model calls | `r4._compose` → `_GuardedAdapter`/`InvokeModel` | YES | REUSE + `_spy_wire` for dispatched payload capture |
| deadline/budget | `TurnDeadline.start` | YES | REUSE |

No new LLM stage, no new judgment mechanism, no regex/keyword rules, no planner. Harness-only instrumentation (spies + labeled corpus).

### Contract inventory (verified in code)

| Component | Responsibility | Input contract | Output contract | Error behavior |
|---|---|---|---|---|
| `interaction_admission` | classify owner-need + interaction class | `input_text` + fixed `admission` block + prior_turns | `{requires_owner_surface, interaction_class}` | invalid/absent → `(None, False)` falls through to selection |
| `turn_goal` (`_understand_goal`) | typed goal interpretation | `input_text` + empty `{}` block | `_TurnGoal` (class, subject, constraints, requirements, bound) | invalid/absent → neutral undeclared default |
| `goal_evidence_relevance` (`_judge_goal_evidence`) | evidence↔goal correspondence | block: `business_subject`, `scope_constraints`, `records[:16]`, `declared_requirements` (when present) | `{correspondence, mismatch_hint}` | `None` → unproven, never assume pertinence |
| `outcome_facts` / `EvidenceFacts` | owner outcome → typed facts | provider structured payload | records, totals, coverage flags | structural projection only |
| `select_group`/`select_capability` | surface selection | live catalog blocks | group/capability ids | fail-closed to not_applicable |

**Key contract detail (proven in code):** `interaction_class == "surface_inquiry"` short-circuits to the deterministic live-surface listing **regardless of `requires_owner_surface`** (comment in source: the flag is "output noise" for that class). The class token — not the flag — carries the routing decision.

---

## 3. Frozen baseline (WP1)

| Field | Value |
|---|---|
| `MODEL_ID` | `delia-json` (`delia-json:latest` on `delpi-ollama`) |
| `MODEL_DIGEST` | `7b8f4ab14fc1` |
| `MODEL_CONFIG` | qwen2.5 3.1B · Q4_K_M · `num_ctx` 8192 · JSON-only |
| `CONTEXT_WINDOW` | 8192 |
| `INSTRUCTION_VERSION` | production `orchestration_instructions.delpi.json` sha256 `adb3685506721cc2` — unmodified |
| `CATALOG_HASH` | `adb3685506721cc2` (instructions as-loaded) |
| `PRODUCTION_QUERIES` | 0 (authorized dev owner surface only) |

---

## 4. Corpus & authoritative oracles (WP1–WP3)

**Intent oracle** — 17 queries × 3 reps = 51 stage-local rows: 13 owner-required reads (R1 + "exemplos" colloquial forms), 4 non-owner (surface inquiry, greeting, concept, injection), 1 write ask. Oracles declare `requires_owner_surface`, acceptable classes, expected `goal_class`, subject tokens — derived from interpreted intent and legitimate contracts, never keyword-matching as semantic judge.

**Judgment oracle** — 15 labeled (goal, evidence) pairs × 3 reps × 4 variants = 180 judgments. All records are REAL owner reads via the governed provider path (delegated bearer, `search_products`):

| Class | Pairs | Construction |
|---|---|---|
| `corresponds` | P_borne, P_ilhos, P_disjuntor, P_fusivel, M_borne_fusivel, P_code_exact | ≥3 records whose description carries every family token; 1 exact-code record |
| `irrelevant` | X_bala_vs_borne, X_borne_vs_disjuntor, X_faston_vs_fusivel, X_fusivel_vs_ilhos, X_bala_page, X_code_wrong, E_empty, H_fusivel_vs_sapata | real pages of a different family; real 0-pertinent page; wrong-code record; empty |
| `partial` | L_borne | 2 pertinent records for a 3-item goal |

`P_bala`/`P_faston`/`L_faston` could not be built — the owner search genuinely returns fewer than 3 token-pertinent items for those queries (itself an owner-search limitation already documented in R1/R0).

---

## 5. Owner-reach findings (WP2)

### 5.1 R1 turn reconstruction — first divergent stage (96 turns)

| Divergent stage | ARM A | ARM B | Total |
|---|---|---|---|
| `OWNER_INVOKED` | 20 | 15 | 35 |
| `ADMISSION_SURFACE_INQUIRY` | 16 | 19 | **35** |
| `ADMISSION_HYPOTHETICAL` | 5 | 6 | **11** |
| `GOAL_MISCLASSIFIED` | 1 | 2 | 3 |
| `ARGUMENTS_INVALID` | 2 | 2 | 4 |
| `OTHER` (budget/no-goal-stage) | 4 | 4 | 8 |

**75% of non-reaches (46/61) die at admission**, driven by the `interaction_class` token, not `requires_owner_surface`. Per-scenario: `colloquial_terminal_bala` 6/6 hypothetical; `desc_conector` 4/6 hypothetical; `h_desc_ilhos` 5/6 and `h_doc_manual` 5/6 surface_inquiry; `discovery_surface` 4/6 surface_inquiry. Legitimate negatives that reached the owner (`neg_write_ask` 3/6, `neg_nonexistent` 3/6) were correctly gated downstream.

### 5.2 Stage-local admission/goal accuracy (51 rows, real contracts)

| Metric | Value |
|---|---|
| `read_recall` (`requires=true` on legit asks) | **1.000** — the flag is never the blocker |
| `adm_class_accuracy` | **0.804** |
| legit class errors | `surface_inquiry` ×5, `hypothetical` ×5 — 10/39 (26%) deflection |
| `negative_hold` (`requires=false` on non-legit) | **0.25** — over-admission is symmetric: `convo_concept`, `inject`, `surface_legit` all emitted `requires=true` (fails *toward* owner path; capability/AuthZ gates hold downstream) |
| `goal_class_accuracy` | **0.744** — errors: `create_or_modify` ×6 on read asks, `analyze` ×2, `clarify` ×2 |
| `subject_fidelity` | **0.564** — subject often reduced to "produto"/"products" (qualifier/code dropped) |
| `invalid_adm` | 0 |
| `undeclared_goal` | 3 |

### 5.3 The hidden composition gap — `answer_requirements` never extracted

**`goal_min_items` was `None` on all 51 rows** — including "Busque três produtos…" and "Me dê dois exemplos…". The goal stage never populates `answer_requirements`, so `declared_requirements` is absent from the production judge block for every quantity ask: the judge cannot verify sufficiency because it never receives the requested count. In production, DÉLIA's judge always runs in the "no-requirements" condition.

---

## 6. Evidence-judgment findings (WP3–WP4)

### 6.1 Payload verification (SOURCE → DISPATCHED)

Dispatched blocks were captured verbatim. **Projection is lossless** for this path: records arrive as full owner items with `code`, `description`, `group_code`, and all scalar fields; `business_subject` and `declared_requirements` arrive when supplied. Example (P_borne, A_gold): the dispatched `<evidence>` block literally contains `"code": "10210436", "description": "BORNE DIVISIVEL 12BCL/1VIS 10 POSICOES PARTEX"` — identity + description preserved.

### 6.2 Stage-local judgment metrics (45 judgments/variant)

| Variant | TP | FN | TN | FP | invalid | uncertain | precision | recall | neg_acc |
|---|---|---|---|---|---|---|---|---|---|
| `A_gold` (oracle context) | 3 | 15 | 23 | 0 | 1 | 0 | 1.000 | **0.167** | 1.000 |
| `A_pipe` (real goal stage) | 3 | 12 | 24 | 0 | 3 | 0 | 1.000 | **0.200** | 1.000 |
| `B_cov` (+coverage metadata) | 0 | 12 | 24 | 0 | 4 | 2 | n/a | **0.000** | 1.000 |
| `D_noreq` (no requirements) | 3 | 13 | 21 | 0 | 4 | 2 | 1.000 | **0.188** | 1.000 |

**False positives: 0 across all 180 judgments.** The judge is perfectly conservative — and almost never affirms.

### 6.3 Per-pair behavior

- `P_code_exact` (single record, exact code in goal): `corresponds` 3/3 on gold/pipe/noreq — **the only multi-run affirmation**. Trivially verifiable identity survives.
- Every multi-record pertinent set (P_borne, P_ilhos, P_disjuntor, P_fusivel, M_borne_fusivel): `irrelevant` in 3/3 reps on nearly every variant — with self-contradictory hints:
  - "records for **disjuntor**, but the user request is for **disjuntor**" (P_disjuntor)
  - "metallic clips ('Ilhós Metálico'), which does not match the request for **ilhós metálico**"
  - "products related to **dividers and fuses**, not 'borne de ligação'" — `BORNE DIVISIVEL` (divisible terminal block) parsed as English "divider"; the Portuguese electrical-component nomenclature (borne = terminal block = the asked subject) was not bridged, despite the instruction's explicit synonym clause.
- All 8 irrelevant classes: correctly rejected 3/3 nearly everywhere (TN≈1.0). Partial evidence (L_borne): rejected — defensible under the contract, and never false-accepted.

### 6.4 Variant conclusions

- **A_gold ≈ A_pipe** (recall .167 vs .200 = noise): goal-stage context loss (weak subjects, missing requirements) is *not* the judge's bottleneck — even oracle-perfect context fails.
- **B_cov ≤ baseline** (recall 0.000): coverage metadata does not restore recall; it adds noise (more INVALID/uncertain). R1's B-arm design could not have worked at this scale even with perfect coverage fields.
- **D_noreq ≈ baseline**: the missing `declared_requirements` is not what breaks the judge — rejection dominates regardless.

---

## 7. Hypothesis classification (WP9)

| H | Statement | Verdict | Evidence |
|---|---|---|---|
| H1 | Admission misclassification | **SUPPORTED** | 46/61 R1 non-reaches at admission; 10/39 stage-local class errors; `surface_inquiry` short-circuits owner path unconditionally; colloquial "exemplos" asks → `hypothetical` 100% |
| H2 | Goal context loss | **REFUTED** (as judgment cause) | A_gold ≈ A_pipe; weak subjects don't change judge outcome. Composition residue: `answer_requirements` never extracted (0/51) — real gap, but not the dominant blocker |
| H3 | Evidence projection loss | **REFUTED** | dispatched payload verified: full `code`/`description` identity preserved |
| H4 | Contract ambiguity | **PARTIALLY SUPPORTED** | admission contract holds near-twin concepts (`surface_inquiry` vs owner coverage questions; `hypothetical` vs `ambiguous` for "exemplos") the model can't separate; judge contract itself is adequate |
| H5 | Semantic judgment failure | **SUPPORTED** | recall ≤0.20 with complete context + preserved identity; self-contradictory rejections; fails only where matching is semantic (description↔subject) — exact-identity works |
| H6 | Harness classification defect | **PARTIALLY SUPPORTED** | R1 harness mislabeled at least one delivered turn (single-product envelope); R1's "90% rejection" direction confirmed here with labels — now measured at 83% (15/18 gold FN) |
| H7 | Model capacity | **SUPPORTED AS RESIDUAL** | after context/projection/coverage controls the error persists on two fronts: description-semantics correspondence and 6-way admission class discrimination. Not a verdict on all tasks — exact-identity matching, JSON structure and governed argument construction demonstrably work |

---

## 8. Proven root causes

1. **Owner reach (Problem A):** the `interaction_class` token is the decisive routing field, and two class definitions are semantically too close for the frozen model: `surface_inquiry` vs "coverage/catalog questions" (opposite routing for near-identical surface descriptions) and `hypothetical` vs `ambiguous` for "N exemplos de X" (the contract's nuance — "prefer ambiguous when the item type could be a registered entity" — is systematically lost). When the class is wrong, `requires_owner_surface=true` cannot recover: the class short-circuits or the flag is false in the same proposal.

2. **Evidence judgment (Problem B):** the judge collapses to conservative rejection on every judgment requiring description-level semantics — i.e., virtually every real search case. The instruction is adequate, the evidence is complete, the context variants don't matter: the 3B cannot reliably affirm semantic correspondence except trivially-verifiable identity (exact code). Its failures are self-contradictory (naming the matching term while denying it), indicating capacity — not context — is binding.

3. **Composition gap (secondary):** `answer_requirements` is never populated by the goal stage (0/51), so production always judges without the declared quantity. Proven not to be the dominant cause (D_noreq ≈ baseline) but a real contract-consumption gap worth fixing.

---

## 9. Security (WP8)

| Gate | Result |
|---|---|
| `AUTHZ_BYPASSES` | 0 — all reads via governed provider + delegated bearer |
| `UNAUTHORIZED_ACTS` | 0 — stage-local eval never invokes writes; inject ask fails *toward* owner path (safe direction), gated downstream |
| `UNAUTHORIZED_PREPARES` | 0 |
| `FABRICATED_RECORDS` | 0 — every judgment record is a real owner return |
| Negative preservation | R1: 12/12 both arms; R1.5 stage-local: `convo_greet` correctly conversational 3/3 |

Coverage is partial: denied-READ AuthZ path, prepare/ACT gates and write-capability selection were not re-exercised (unchanged since R1).

---

## 10. Cost

| Field | Value |
|---|---|
| `TOTAL_MODEL_CALLS` | 327 (102 admission+goal · 45 goal-for-pairs · 180 judge) |
| `INPUT_TOKENS` / `OUTPUT_TOKENS` / `LATENCY` | not captured post-resume — usage counters reset when the run resumed after the `/docs` path fix; per-call usage exists in-process only. Dispatched chars captured: 602,933 across rows |

## 11. Limitations

- Same-model judging the same model is avoided by construction (oracle labels are contract-derived, not model-derived).
- `P_bala`/`P_faston` pairs absent (owner search can't produce ≥3 pertinent items) — terminal-bala *positive* judgment untested; negatives cover it.
- Token/latency totals lost on resume (calls counted from rows).
- Holdout thin: `H_fusivel_vs_sapata` n=1 record.
- `create_or_modify` goal-class noise did not measurably gate reach in R1 traces (runs still invoked) — its downstream risk is real but not causally proven here.

## 12. Recommended next direction (WP10)

**`PROVEN_ROOT_CAUSE`:** admission class-token misrouting (H1+H4) for owner reach; judge conservative-collapse on description-semantics (H5+H7) for evidence judgment. Both are instruction/contract-vs-capacity boundary problems, not projection or context problems.

**Next bounded candidates (no implementation in this task):**

| Candidate | Owner | Minimal change | Risk |
|---|---|---|---|
| A. Admission class consolidation | `interaction_admission` contract | collapse near-twin classes; make `requires_owner_surface` the routing field, class advisory | low — pure contract/instruction revision |
| B. Judge contract reframing | `goal_evidence_relevance` contract | judge **per-record correspondence** (list of pertinent record indices), deterministic sufficiency check by backend — LLM keeps semantics, backend counts | medium — contract redesign, but preserves LLM-owns-meaning |
| C. Requirements extraction fix | `turn_goal` contract | make `answer_requirements.min_items` reliably populated for quantity asks | low |
| E. R1 re-run with corrected arms | eval harness | after A/B land | — |

**`NEXT_BOUNDED_STEP`:** B → A → C — reframing the judge contract to per-record correspondence (LLM semantics + deterministic sufficiency) is the single highest-leverage change; it converts an unverifiable set-level judgment into an auditable per-record one while *reducing* model surface area. A model-scale comparison remains possible later under separate authorization, but is not required to act on these findings — the contract fixes are justified on their own evidence.

## 13. Artifacts

- `delia-api/scripts/semantic_judgment_reach_eval.py` — stage-local harness
- `docs/12-roadmap-e-evolucao/delia/evidence/semantic-judgment-r15-runs.json` — full rows: queries, proposals, dispatched payloads, judgments, pairs, matrices

**PRODUCTION_CODE_MODIFIED=NO · PRODUCTION_INSTRUCTIONS_MODIFIED=NO · MODEL_CHANGED=NO · PRODUCTION_QUERIES=0 · DEPLOY_EXECUTED=NO**


## 14. Independent coordination review — 2026-10-27

**VERDICT=ACCEPT_WITH_RESIDUAL (R1.5 diagnostic); production contract/implementation changes NOT authorized.** Static GitHub independent review of published doc 166 and executor evidence; no independent local model re-execution or production probes. The reconstructed owner-reach attribution 46/61 non-invoked turns stopping in admission is material, and its deterministic `surface_inquiry` short-circuit overriding `requires_owner_surface` is an architectural contract inconsistency worth correcting **after contract-first experimentation**. The latter flag's 100% recall applies only to positive READ cases in this particular stage-local corpus; negative_hold=0.25 demonstrates **poor negative discrimination**. Never route directly to owner on this flag alone without testing non-owner and unsafe cases and preserving live permissions and operation-class gates.

**Judgment data:** reported oracle-context A_gold TP=3, FN=15 (recall=0.167) and real dispatched source records contained codes/descriptions; this supports observed false-negative behavior with the current stage contract. Other variants similarly low. `FP=0` does NOT mean broadly 'perfect precision' or validate the contract: the model overwhelmingly abstains/rejects, the positive sample is small and derived from lexical/domain-token criteria, and invalid/uncertain outputs are not positive acceptances. Confirm that each labeled pair truly meets user-goal semantics/quantity independently; `P_borne` and `P_ilhos` may involve distinct product subclasses. For binary relevance vs multi-record sufficiency, specify exactly whether label=any pertinent item, all returned items pertinent, or enough pertinent items for the requested cardinality. The present `partial` class is rejected as expected under a sufficiency contract but would be positive for a per-record correspondence contract. These labels are not interchangeable.

**Causal caveats:** Gold-vs-pipeline and coverage/no-requirements arms show that merely restoring tested context fields did not repair recall; they do not establish that the current judge instruction/format is optimal or that model capacity is independently proven. H7 must remain `TO_EVALUATE/INCONCLUSIVE` as a causal attribution until a bounded local same-model contract reframing test. Claim that `answer_requirements` is never extracted is grounded in 51 sampled rows, not all production turns; its absence is a separate functional gap for quantity validation. Note discrepancy in corpus description (`17 queries` versus `13 owner READ + 4 non-owner + 1 write`) and reconcile labels/denominators. Token/latency metrics missing are a residual, not PASS on cost.

**Next bounded action approved only as experimental planning:** stage-local A/B on frozen local `delia-json`: existing set-level judgment vs per-record correspondence using identical owner records, with record-level verified oracle labels and deterministic sufficiency counted **after** LLM semantic labels. Explicitly measure TP/FN/TN/FP/invalid/partial, false accepts, tokens/latency and holdout. Independently stage-local compare admission current contract vs reduced class taxonomy or a coherent single routing decision, ensuring negative examples do not increase owner over-admission; no production prompt/code change. Prefer two separately controlled causal experiments rather than changing judge and admission together. Confirm `EXISTING_EQUIVALENT` and reuse before new stages; preserve CRI and deterministic safety gates. Do not assume per-record reframing will outperform; if it does not, report REWORK/INCONCLUSIVE. R1 business-outcome rerun should occur only after these controls improve stage metrics. No paid-model switch, deploy, or production tests.
