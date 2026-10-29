# 206 — Semantic goal-to-argument alignment for ordering/listing goals

- **Task:** `DELIA-C3-SEMANTIC-ARGUMENT-AND-ORDERING-REMEDIATION-01`
- **Base:** `c253e052fbe55348f6f66deaf82aa74781fa924c` (doc 205 deploy state)
- **Scope:** residual E2 — argument formulation and goal coverage for ordering, listing and record-selection objectives. Task 13's requirement-aware bounded page walk is preserved unchanged; this task closes the semantic gap upstream of it. No production deploy (task constraint).

## 1. Incident

```
USER_GOAL="Qual o último processo do Transforma+?"
OBSERVED=TÉO selected correctly; record_read invoked; model sent
  q="Transforma+"; owner returned total=0; DÉLIA answered with an
  empty collection. Technically consistent with the sent arguments,
  semantically a failure of the user's goal.
```

## 2. Diagnosis — real TÉO contract

`record_read` (transformometro-api MCP server): `action=search|get`, `entity`, `id`, filters (`status`, `familia_processo`, `fase_melhoria`, …), `q`, date range (`date_field`/`date_from`/`date_to`), `page`, `page_size`.

- **`q` semantics (verified in implementation):** free-text `ILIKE` over the record's own text fields (name, code, family, description, objective). It is *not* an entity filter, not an identifier lookup, not an ordering operator. Before this task, this semantics existed only in the tool-level description (`"q for text search"`); the published `input_schema` carried **zero per-parameter descriptions**.
- **Unfiltered listing:** supported (`action=search` + `entity`, all filters optional).
- **Pagination:** supported (`page`/`page_size`; envelope `{total, items, truncated}`).
- **Ordering:** no `sort`/`order_by` argument exists — but the owner returns process records `ORDER BY updated_at DESC` implicitly, and every item carries `updated_at`. The authoritative extreme-record means = unfiltered listing + authoritative owner order + bounded coverage walk (Task 13).
- **`answer_requirements`:** the governed goal contract already expresses `ordering`/`min_items`/`complete_coverage`, and the CRI instruction clause (`delia.cri.answer_requirements_instruction`, appended to `turn_goal` at runtime) already teaches superlative → `ordering`.

## 3. Causal gate

```
FIRST_PROVEN_DIVERGENCE (deterministic)=
  The argument-generation stage never received the validated
  answer_requirements. _build_arguments / _candidate_arguments /
  _propose_candidate_arguments received capability, schema,
  business_subject, relevance_feedback — but not the typed
  ordering/min_items/complete_coverage the assessment stage later
  verifies. Requirements declared at goal-understanding died at the
  stage boundary: the argument model could not know it was
  formulating an ordering goal, and defaulted to binding
  business_subject into the owner's free-text field (q).
SECOND_PROVEN_DIVERGENCE (contract)=
  TÉO published no per-parameter descriptions; q's free-text
  semantics existed only in the tool description. Combined with the
  arguments instruction's unconditional "business_subject →
  free-text field" rule, the model had no published basis to
  distinguish content-search from listing.
THIRD_PROVEN_DIVERGENCE (instruction)=
  The v25 `arguments` instruction mandated verbatim binding of
  business_subject into the descriptive/free-text field for every
  goal class — correct for content search, wrong for listing/
  ordering/count goals where the subject names the record set, not
  filter text.
CAUSE_STATUS=PROVEN (all three, deterministic surfaces)
RESIDUAL=model-semantic — whether the production model declares
  answer_requirements for superlatives is model-owned; surfaces are
  now correct on every governed layer.
```

## 4. Reuse gate

```
RESPONSIBILITY=goal-declared requirement → argument formulation
OWNER=delia-api capability_provision/orchestration (projection);
  transformometro-api MCP server (owner param semantics);
  orchestration_instructions.delpi.json v26 (semantic guidance)
CANONICAL_SOURCE=answer_requirements (existing governed contract),
  MCP inputSchema param descriptions, existing arguments instruction
CONSUMERS=_build_arguments (direct/preflight/recovery),
  _candidate_arguments, _propose_candidate_arguments
CONTRACT=declared_requirements block in the argument-stage payload;
  owner param descriptions in published schema
EXISTING_EQUIVALENT=YES — all mechanisms pre-existed
REUSE_DECISION=EXTEND (projection + owner descriptions + instruction)
ABSTRACTION_GATE=NO new port/planner/registry/lexical function; the
  existing inline requirements dict was deduplicated into the shared
  _declared_requirements_projection helper
```

## 5. Fixes (minimal diffs)

**A — TÉO owner contract** (`tm_app/interface/mcp/server.py`, +150/-27): `Annotated[..., Field(description=...)]` on every `record_read` parameter, with semantics verified against the implementation — `q` explicitly "free-text search contained in the record's own text fields … do not use it to express ordering, recency, or ranking"; `action`, `entity`, `page`/`page_size`, date-range and filter fields described from real behavior. Published MCP `input_schema` now carries the semantics the argument model reads.

**B — requirement projection** (`capability_provision/orchestration.py`, +84): `_declared_requirements_projection(requirements)` — bounded typed projection of the governed `answer_requirements` vocabulary (`min_items`/`ordering`/`complete_coverage`, non-null values only). Threaded into `_build_arguments` (preflight target, main target, relevance-recovery), `_candidate_arguments` and `_propose_candidate_arguments`. The bare-schema block shape is preserved when no extras exist (a projection-integrity lock caught and pinned this). No new model call; the block is contract data, not an instruction.

**C — `arguments` instruction v26** (`orchestration_instructions.delpi.json`): the `business_subject` paragraph now distinguishes goal classes — on a content-search goal the subject binds verbatim to the descriptive/free-text field; on a listing, count, ordering or extreme-record goal "the subject names the record set — leave free-text fields empty rather than filter on it; `declared_requirements`, when present, carries the governed requirements guiding this choice". The resource is governed by a strict 8192-byte bound; the amendment was paid for by semantics-preserving compression of four non-locked clauses (preserve-information, concept-artifact, foreign_evidence, relevance_feedback). All locked phrases verified: `naming rule, canonical designation`, `naming rules or canonical designations`, `canonical designation copied verbatim`, `concept`, `prior_result_preview`. Final size 8001 bytes.

**Not changed:** `turn_goal` text (its `answer_requirements` field spec already exists at v25; the CRI clause already teaches superlative → ordering — an attempted duplicate clause there failed the separation-of-responsibility lock and was reverted). `cri_instructions.delpi.json` unchanged. Task 13 page walk unchanged. PREPARE/ACT, budgets, retries, authz unchanged.

## 6. RED → GREEN

- `delia-api/tests/test_c3_declared_requirements_argument_projection.py` (new, 3 tests): **RED** — the arguments block carried only `capability`/`description`/`input_schema`; expected `declared_requirements={"ordering":"newest_first"}`. **GREEN** — ordering and min_items reach the block; requirement-free goal keeps the prior block shape.
- `transformometro-api/tests/test_teo_mcp_surface_v2.py` (+41): **RED** — published schema had no param descriptions. **GREEN** — all `record_read` params carry bounded descriptions; `q` semantics explicit. 7/7.
- `delia-api/tests/test_evidence_schema_projection_integrity.py`: caught a block-shape regression (bare schema must stay bare when no extras) — fixed before GREEN; now passing.
- Task 12/13 suites preserved: `test_c3_goal_to_owner_execution.py` 11/11 (walk unchanged), projection/omission/recovery contract suite GREEN.

## 7. Semantic eval (local model, bounded 10-case corpus)

Real instruction resource (v25/v26), real TÉO `input_schema` (undescribed/described), real CRI clause appended to `turn_goal` exactly as production does, real `OpenAICompatibleModelInvocationAdapter` against local Ollama. Two-stage eval: `turn_goal` → `arguments` with production-shaped blocks. Evidence: `docs/12-roadmap-e-evolucao/delia/evidence/semantic-argument-ordering-eval-206-runs.json`.

```
ARM              BASELINE(v25+no desc)  CORRECTION(v26+desc+projection)
passed           3/10                   4/10
model calls      20                     20
latency          ~36.5s                 ~41.0s
tokens           not reported by local endpoint
```

Per-case deltas (correction vs baseline):
- `count_processes`, `by_id`, `list_all`: PASS both arms (by_id/list_all were baseline failures in the first no-clause run).
- `text_search` (explicit content search): `q="melhoria"` preserved — no regression.
- `recent_updated` ("processos atualizados recentemente"): baseline `q="recentemente"` → correction **no `q`** (unfiltered listing) — correct per the amended instruction.
- `e2_incident` / superlatives: the local eval model still binds `q` and does not declare `answer_requirements` even with the CRI clause present — **model-bound residual**, not a surface defect: every deterministic layer now carries the information (owner param semantics, declared-requirements projection, instruction distinction). The task's own §10 forbids inferring production (Kimi) behavior from this local model; the eval is recorded as the honest bounded signal.

## 8. Regression / audits

- Focused delia-api matrix (goal→owner, declared-requirements, evidence relevance, pagination, argument schema parity, projection integrity, governed knowledge, instruction resource, argument validation, Engine B isolation, production engine selection, goal-selection handoff, typed capability+goal, self-awareness relevance, CRI toggle): **369/369 GREEN**.
- TÉO MCP surface: 7/7 GREEN.
- `audit_architecture_phase3.py`: 0 findings. `audit_backend_boundaries.py`: 0 findings. `audit_platform_guardrails.py`: 0 findings.
- Full delia-api suite: pre-existing failures only — 2 environmental (`/docs`, `/plugins` mounts absent — same class as Tasks 12/13) + 1 stale assertion (`test_cri_instruction_variant_carries_requirements_clause` predates this diff; `answer_requirements` was already merged into base `turn_goal` at HEAD — verified via `git show HEAD:`).
- No new direct-DELPI bypass, no provider path added, no secrets/argument values logged, no budget/retry/authz change.

## 9. Compatibility / residuals

- Engines: projection lives in the shared argument paths — LangGraph B1 and Engine A inherit identically.
- `declared_requirements` is additive optional payload data: older instruction versions ignore unknown block keys; no consumer break.
- **Residual 1 (model-bound):** superlative → `ordering` declaration is a model-semantic step. Governed surfaces are correct; production-model compliance is unverifiable locally and must be observed in production (next bounded step).
- **Residual 2 (owner):** TÉO has no explicit `sort` argument — "latest" relies on the owner's implicit `updated_at DESC` order plus `ordering_semantic` evidence. If the owner's implicit order is insufficient for a future requirement, the correct outcome is `ARCHITECTURE_DECISION_REQUIRED`, never a simulated sort.
- `semantic_decision_eval.py` version pin updated 25→26 (it binds the instruction resource version).

## 10. Next bounded step

Observe the original E2 goal in production (post-deploy authorization): whether Kimi declares `ordering="newest_first"` under the CRI clause, omits `q`, and the Task-13 walk completes coverage → supported latest record, or produces the typed limitation. If `q`-filter recurs under a capable model, the divergence is then model-interpretation-only and the next surface is the CRI clause wording — not new machinery.
