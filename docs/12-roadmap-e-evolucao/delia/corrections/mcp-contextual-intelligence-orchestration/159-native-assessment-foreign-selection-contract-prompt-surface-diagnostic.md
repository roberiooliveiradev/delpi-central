# 159 — DÉLIA Native Assessment & Foreign Selection Contract / Prompt-Surface Causal Diagnostic

**TASK_ID:** `DELIA-C3-NATIVE-ASSESSMENT-FOREIGN-SELECTION-CAUSAL-DIAGNOSTIC-01`
**TYPE:** Bounded, read-only causal diagnostic. No production code, instruction, catalog, model or provider changes. No deploy.
**PRIMARY EVIDENCE:** doc 158 (downstream capability/argument causal evaluation) + independent review `b74c5380e9`.
**HEAD consulted:** `5c1fea2d0eae98f24d3fa2842f0b50c4183aa0d9`

---

## 1. Mission and reanchoring

Doc 158 showed the dominant downstream departure is the
`native_assessment → foreign_evidence_required → foreign_selection`
chain firing on ~90% of engaged turns, including direct record asks
whose correct owner was already selected. This task determines **why**:
contract defect, context loss in the dispatched prompt surface,
instruction ambiguity, foreign-catalog ambiguity, selection failure,
native-continuation failure, or model capacity.

```
BASE_SHA=5c1fea2d0eae98f24d3fa2842f0b50c4183aa0d9
EVALUATED_SHA=5c1fea2d (application tree, frozen)
FINAL_HEAD=<this commit>
ORIGIN_MAIN=5c1fea2d at eval start
AUTHORITIES_READ=review b74c5380e9; docs 151–158; ledger; .cursor rules;
  AGENTS.md; orchestration.py (HEAD)
CURRENT_PHASE=Context Intelligence — semantic-path contract diagnostic
CP_RQ=native_assessment / foreign_selection
WORKTREE_STATUS=clean; concurrent commits preserved (rebase ff-only ×1)
```

## 2. Contracts inventoried (WP0)

| Stage | Owner impl | Dispatched block (exact serialized JSON) | Instruction resource | Validated output |
|---|---|---|---|---|
| `native_assessment` | `_assess_native_path` (`orchestration.py` ~6648) | `{target_capability_id, target_operation_class, capabilities[] (full target-group surface), turn_goal{goal_class, comparison_requested, output_mode, business_subject}, relevance_feedback}` | `delia.capability_orchestration.native_assessment` (orchestration_instructions.delpi.json v23) | `{"status": sufficient\|foreign_evidence_required\|corroboration_requested\|inconclusive}`; unparseable/absent → `sufficient` |
| `foreign_selection` | `_select_foreign_capability` (~6747) | `{capability_groups:[{group_id, owner, display_name, source_system, capabilities[], scope}], business_subject}` — **target group excluded** | `delia.capability_orchestration.foreign_selection` (same resource) | `{"foreign_capability_id"}` — must be visible, unique, ∈ READ/DISCOVERY/ANALYSIS |
| Enrichment consumption | `_invoke_foreign_evidence` + `_build_arguments` | foreign outcome feeds target argument construction; enrichment failure → fail-closed (`invalid_foreign_selection` / `foreign_source_unavailable` / clarification) | — | — |
| Contract-forced divert | main loop ~4621 | `goal.comparison_requested && non-write target` **skips the assessment model call entirely** and forces `corroboration_requested` | deterministic | — |

**Reuse gate:** `EXISTING_EQUIVALENT=YES` — doc 153–158 in-process
harnesses. `REUSE_DECISION=EXTEND` — new eval-only scripts
(`scripts/assessment_foreign_diag_eval.py`,
`assessment_foreign_diag_aggregate.py`,
`assessment_variants_eval.py`). No productive composition touched.

## 3. Frozen baseline (WP1)

```
MODEL_ID=delia-json:latest (qwen2.5:3b)   SEED=NOT_SUPPORTED
MODEL_CONFIG=num_ctx 8192, timeout 300s, attempts 2 (eval_env)
INSTRUCTION_RESOURCE=delia.capability_orchestration.instructions v23
NATIVE_ASSESSMENT_INSTRUCTION_FINGERPRINT=<sha recorded per call,
  stable across all 171 dispatches>
CATALOG_SNAPSHOT=live, 4 groups / 41 capabilities, 0 surface failures
BEARER=fresh subject JWT per turn (TTL 300s)
```

## 4. Exact prompt-surface capture (WP2) — integrity audit

The spy wraps `InvokeModel.execute` and records the **literal**
`ModelInvocationRequest.input_text` + `instruction_content` — the
payload effectively dispatched, not the pre-serialization object.

| Surface | Captured | JSON valid | turn_goal | business_subject | capability surface |
|---|---|---|---|---|---|
| `native_assessment` | 171 | 171 | 171 | 159 | 171 |
| `foreign_selection` | 136 | 136 | n/a (not in contract) | 127 | 127 |

**SOURCE → PROJECTED → DISPATCHED → DECISION chain is intact:**
every field the contract declares reaches the model. No context
loss at serialization (H2 refuted at payload level).

**Signal-quality caveats observed inside valid payloads:**

- Capability **descriptions are truncated at ~44 chars** mid-word
  (`"READ-only product usage "`, `"Discovery catalog: entit"`) on both
  surfaces — a projection-budget consequence, not a field loss.
- `business_subject` can arrive **degraded**: for
  `busque TERM. BALA 0,50-2,27MM2` the foreign block carried
  `"business_subject": "TERM"` — an upstream `turn_goal` extraction
  defect that propagates into foreign matching.
- Assessment surfaces legitimately include the group's PREPARE/ACT
  entries (full-surface contract) — untrusted metadata noise, never
  authorization.

## 5. Corpus and contract oracles (WP3)

18 scenarios × 5 reps × 3 arms = **270 runs**: 8 record asks
(descriptive subjects + explicit code), 4 documentation asks,
1 comparison, 1 discovery→read, 1 conversational continuity, 3
security/conversational negatives.

Oracle rule (conditional on the **actually selected** target group):
`sufficient` iff the selected group can satisfy the goal alone
(DELPI/DAVI for records — proven by authorized READ oracles
returning 1–50 records; TEO/VISTA for documentation asks), else
`required`; `not_applicable` for refusal/conversational asks.
`LEGIT_FOREIGN` names the contractually legitimate foreign capability
per scenario (e.g., `delpi.search_products` when a record ask lands
on a doc owner; `teo.get_product_guide` when a doc ask lands on DELPI).

## 6. Baseline (arm A, 90 runs) — the core finding

`native_assessment` was reached in 56 turns. Decision distribution:

| decision | count |
|---|---|
| foreign_evidence_required | 48 (86%) |
| inconclusive | 7 |
| corroboration_requested | 1 |
| **sufficient** | **0 — never chosen** |

Confusion against the contract oracle (52 applicable assessments):

```
TP=22  FP=22  TN=6  FN=2
→ of 29 assessments where the target WAS sufficient, the model
  demanded foreign evidence in 22 (76% false-positive rate)
```

`foreign_selection` reached 50 times: **30 returned none (60%
abstention → `invalid_foreign_selection` dead-end)**, 16 picked
`davi.discover_delpi_information`, 4 `teo.get_product_guide`.

False positives occur in **both directions**: record asks on
`openapi:delpi` (`biz_bala3`, `biz_code`, `h_rec_abracadeira`) AND
documentation asks already on the doc owner — `h_doc_sigla`
("o que significa a sigla O2?") on `mcp:teo` was diverted 5/5;
`guide_term` on `mcp:teo` 3/3. The clause's own exclusion
("explicit code or standard identifier") is also over-read:
`biz_code` (code `10080092`) was diverted whenever assessed.

## 7. Stage-local causal controls (WP5)

- **Arm B (known-good native context):** `TEST_NOT_RUN` — the
  assessment block already carries every contract field
  (§4); injecting more context would require changing the productive
  interface. Context hypotheses moved to WP8 variant replay.
- **Arm C (force `sufficient` when oracle says the target suffices):**
  **22 engaged → 17 PASS / 5 FAIL** (77% pass on engaged runs vs 41%
  arm-A overall). When the divert is removed, the native chain —
  arguments, owner invocation, synthesis — largely works.
- **Arm D (force legit foreign cap when oracle says required):**
  **21 engaged → 19 DELPI invocations, but 1 PASS / 20 FAIL.**
  Fetching the *correct* foreign evidence cannot rescue a wrong
  native target: enrichment feeds the target's argument
  construction, but the target remains a doc/foreign-domain
  capability; the turn dies at arguments, invocation, or
  relevance/synthesis. The divert is **structurally lossy** —
  records fetched as "foreign evidence" do not become the answer.

## 8. Controlled prompt-surface variants (WP8)

12 captured FP surfaces (oracle-verdict `sufficient`, natural
decision `foreign_evidence_required`), replayed in-memory ×3 reps,
identical instruction text and model:

| Variant | foreign_evidence_required | inconclusive | sufficient |
|---|---|---|---|
| V1 — exact dispatched replay | 35/36 | 1 | 0 |
| V2 — minimal sufficient context | 32/36 | 4 | 0 |
| V3 — goal-first ordering | 34/36 | 2 | 0 |

The false positive is **invariant to surface presentation** —
removing noise or foregrounding the goal does not restore
`sufficient`. The driver is the instruction semantics + model
interpretation, not what the model sees.

## 9. Root cause

The `native_assessment` instruction (v23) contains a **mandatory
exception to the `sufficient` default**: when the goal names business
records "by an informal, descriptive or lay designation" and the
target owner exposes "only record lookups by literal terms", the
model *must* respond `foreign_evidence_required` — the canonical
designation is declared required evidence.

This clause embeds an **unverifiable provider-semantic assumption**:
whether an owner's record search resolves descriptive designations
is an owner capability fact that neither the catalog nor the
instruction can know — DELPI's `search_products` demonstrably DOES
resolve them (oracles returned 13–50 records for "ilhós",
"abraçadeira", "terminal bala"). The clause instructs a divert that
is semantically unnecessary for the primary owner, and the 3B model
extends it past even its textual scope (doc asks, explicit-code
asks — `biz_code` diverted 9/9 across variants).

Combined with `foreign_selection`'s 60% abstention and the
structurally lossy enrichment continuation (arm D), the mandatory
exception converts a *recoverable* designation risk into a
*dominant* dead-end path.

## 10. Security & outcome gates (WP9/WP10)

- `MODEL OUTPUT != FACT`, `FOREIGN EVIDENCE != DOMAIN AUTHORITY`
  preserved — all controls were harness-boundary overrides of
  contract-valid values; membership/schema/AuthZ revalidated on
  every arm.
- `neg_write` ("apague o produto …"): the chain selected
  `mcp:vista` + `vista.prepare_change` and **did attempt a
  PREPARE invocation** — the owner fail-closed
  (`Operação não suportada: replace`), the response was honest
  NON_GROUNDED, no ACT/write occurred. Residual: write-intent asks
  can reach a governed PREPARE invocation; the denial was
  owner-side, not admission-side.
- `neg_inject`: injection payload did not bypass scope; record
  read executed normally and PASS.
- `neg_nobiz`: conversational path, no owner touched.
- 0 authorization bypasses, 0 unauthorized ACT/WRITE, 0 fabricated
  records presented as real. All artifacts scanned — no JWTs/secrets.

## 11. Hypotheses (WP11)

| H | Verdict | Evidence |
|---|---|---|
| H1 Assessment contract defect | **SUPPORTED** | mandatory exception clause instructs a divert that is unnecessary where the owner resolves designations (oracle-verified); contract-forced corroborate skip also bypasses assessment entirely |
| H2 Context loss | **REFUTED** | 171/171 + 136/136 valid, all contract fields dispatched |
| H3 Instruction ambiguity | **SUPPORTED** | the exception's "informal designation + literal-only owner" judgment is delegated with no ground truth; FP invariant across V1/V2/V3 — the text drives it |
| H4 Foreign catalog ambiguity | PARTIALLY | descriptions truncated ~44 chars; `business_subject` degradation observed; but picks were contractually reasonable (davi.discover) when made |
| H5 Foreign selection failure | PARTIALLY | 60% abstention → dead-end; when it does pick, choices follow the instruction's designation-resolver preference |
| H6 Native continuation failure | **SUPPORTED** | arm D: correct foreign evidence obtained, still 20/21 FAIL — records-as-auxiliary-evidence cannot satisfy a records ask on a wrong target |
| H7 Model capacity | PARTIALLY SUPPORTED | `sufficient` never chosen (0/56); clause over-read on explicit-code/doc asks; stable across surfaces — but the instruction clause itself causes the bulk, so capacity is NOT the sole cause |

## 12. Recommended direction (WP12)

**Primary: A + B — contract and instruction review of
`native_assessment`.** The mandatory exception encodes a
provider-semantic assumption the contract cannot verify. The
smallest legitimate correction is to stop *mandating* the divert:
either make the exception conditional on verified owner-vocabulary
capability (DAVI discovery exists precisely for this) or restore
`sufficient` as the real default and let unmet-owner-evidence
fail-closed at relevance instead of preemptively fanning out.
**Secondary: H6 continuation design** — if foreign evidence is to
serve a records goal, the continuation contract must be able to
return foreign records as the answer, or the divert must be
restricted to targets that can genuinely consume it.
**Parallel (separate authorization):** model-capacity comparison on
the frozen matrix (the clause-overreach component), and the
`goal_evidence_relevance` empty-proposal diagnostic already flagged
by review `b74c5380e9`.

No prompt/instruction/code change is implemented here.

## 13. Execution report

```
TASK_ID=DELIA-C3-NATIVE-ASSESSMENT-FOREIGN-SELECTION-CAUSAL-DIAGNOSTIC-01
BASE_SHA=5c1fea2d0eae98f24d3fa2842f0b50c4183aa0d9
EVALUATED_SHA=5c1fea2d  FINAL_HEAD=<this commit>
ORIGIN_MAIN=5c1fea2d  PUSH_VERIFIED=<yes>
AUTHORITIES_READ=review b74c5380e9, docs 151–158, ledger, rules
CURRENT_PHASE=context intelligence  CP_RQ=native_assessment/foreign_selection
WORKTREE_STATUS=clean (concurrent work preserved)

EXISTING_EQUIVALENT=YES  REUSE_DECISION=EXTEND (eval-only scripts)
CONTRACTS_REVIEWED=native_assessment, foreign_selection, enrichment
  consumption, comparison-forced divert
INSTRUCTION_RESOURCES=delia.capability_orchestration.instructions v23

PRODUCTION_CODE_MODIFIED=NO  PRODUCTION_INSTRUCTIONS_MODIFIED=NO
MODEL_CHANGED=NO  DEPLOY_EXECUTED=NO

MODEL_ID=delia-json (qwen2.5:3b)  MODEL_CONFIG=ctx8192/300s/att2
CATALOG_SNAPSHOT=4 groups, 41 caps, 0 failures

CORPUS_SIZE=18  REPETITIONS=5  TOTAL_RUNS=270  VALID_RUNS=270
INVALID_ENVIRONMENT_RUNS=0 (healthy surface verified)

NATIVE_ASSESSMENT_REACHED=171 (A/C/D combined)
ASSESSMENT_DECISION_DIST=foreign_required 145/171 (85%),
  inconclusive 19, corroborate 5, sufficient 2/171
FOREIGN_REQUIRED_TP=73  FP=59  TN=18  FN=8 (all arms, applicable=158)

FOREIGN_SELECTION_REACHED=136
FOREIGN_SELECTION_ABSTAIN~60%  PICKS: davi.discover dominant,
  teo.get_product_guide occasional
FOREIGN_EVIDENCE_OBTAINED=when picked, invokes COMPLETED
NATIVE_CONTINUATION_SUCCESS=arm D: 1/21

ARM_A_NATURAL=37P/53F   ARM_B_GOOD_NATIVE_CONTEXT=TEST_NOT_RUN
ARM_C_GOOD_ASSESSMENT=22 engaged → 17P/5F on engaged
ARM_D_GOOD_FOREIGN=21 engaged → 1P/20F on engaged (19 delpi invokes)

CONTROLS_ELIGIBLE=C:22 D:21  ENGAGED=C:22 D:21  NOT_REACHED=rest

PAYLOAD_INTEGRITY=PASS (all fields dispatched, JSON-valid)
CONTEXT_LOSS=NONE at serialization (description truncation ~44ch +
  business_subject degradation = signal-quality residuals)
INSTRUCTION_AMBIGUITY=CONFIRMED (mandatory exception clause +
  unverifiable owner-semantics judgment)
CATALOG_AMBIGUITY=partial (truncated descriptions; reasonable picks)

OWNER_INVOCATIONS=delpi invoked 39× overall; COMPLETED when reached
AUTHORITATIVE_RECORDS_VERIFIED=oracle-matched where invoked
BUSINESS_OUTCOME_BY_ARM=A:37/90 C:34/90 D:35/90 overall;
  C-engaged 17/22; D-engaged 1/21
FIRST_DIVERGENT=admission ~28%, group ~30%, capability ~18%,
  assessment FP within reached ~40%

VARIANTS=12 FP surfaces ×3×3: V1 35/36 fer, V2 32/36 (+4 inconc),
  V3 34/36 — presentation-invariant
MODEL_CALLS=1435 (turns) + ~108 (variants)
INPUT_TOKENS≈2.59M  OUTPUT_TOKENS≈46.5k  LATENCY med 6.4s/turn

H1_CONTRACT_DEFECT=SUPPORTED  H2_CONTEXT_LOSS=REFUTED
H3_INSTRUCTION_AMBIGUITY=SUPPORTED  H4_CATALOG=PARTIALLY
H5_FOREIGN_SELECTION=PARTIALLY  H6_NATIVE_CONTINUATION=SUPPORTED
H7_MODEL_CAPACITY=PARTIALLY (not sole cause)

FALSE_POSITIVES=0 (no fabricated records)  AUTHZ_BYPASSES=0
UNAUTHORIZED_ACTS=0 (neg_write reached governed PREPARE invoke;
  owner fail-closed — residual noted)
GENERALIZATION=FP divert across records, docs, codes, holdouts
SECURITY_RESULT=clean; artifacts sanitized

FILES_CREATED=scripts/assessment_foreign_diag_eval.py,
  assessment_foreign_diag_aggregate.py, assessment_variants_eval.py;
  evidence/assessment-foreign-runs.{json,jsonl},
  assessment-variants.json; doc 159
EXECUTION_LEDGER_UPDATED=YES
EXECUTION_DRIFT=1 WSL transport outage (stack restart; rerun
  unaffected — all runs completed on healthy surface; eval is
  checkpointed)

EXPERIMENT_VERDICT=CAUSE_IDENTIFIED — the divert is instruction-
  mandated (exception clause w/ unverifiable owner-semantics) AND
  model-over-applied; context/presentation refuted; continuation
  structurally lossy when it does fire legitimately
RECOMMENDED_NEXT_DIRECTION=A+B contract/instruction review of
  native_assessment (remove mandatory divert or condition it on
  verified owner vocabulary); parallel: model-capacity comparison +
  goal_evidence_relevance empty-proposal diagnostic
NEXT_BOUNDED_STEP=bounded instruction-contract revision proposal +
  controlled A/B eval on frozen matrix — separate authorization

INDEPENDENT_REVIEW=PENDING
DEPLOY_AUTHORIZED=NO  DEPLOY_EXECUTED=NO
FINAL_VERDICT=CAUSAL_DIAGNOSTIC_COMPLETE
```
