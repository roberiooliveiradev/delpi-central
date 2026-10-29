# 204 — Evidence-to-answer causal remediation and isolation

- **Task:** `DELIA-C3-EVIDENCE-TO-ANSWER-CAUSAL-REMEDIATION-AND-ISOLATION-01`
- **Branch/HEAD at delivery:** `main` — code landed on top of `1f6f6d1970` (final published SHA recorded in the ledger entry)
- **Scope:** bounded diagnosis + minimal owner fix inside `delia-api`. No production deploy, no production model calls. Engine B1 unchanged.
- **Authorities:** docs 16, 50, 17, 49, 51, 52, 21, 20, 25, ADR 58 / roadmap 59, docs 187–203, API-DELPI remediation changelog (owner authority for product search), execution ledger.

## 1. Production incidents (sanitized trace)

Two read-only production evidence pulls on `delpi-delia-api` logs (srv-api, sanitized — arg values/tokens/secrets are never logged by design).

**E1 — `correlation_id=fa4f6444-77ba-4f35-807a-b33164110edf`** ("dois exemplos de terminal bala", 2026-10-29 ~81s, 14 model calls):

```
interaction_admission → select_group(mcp:davi) → select_capability(discover_delpi_information)
→ native_assessment(sufficient) → plan(direct)
→ davi.discover_delpi_information ok 262ms (arg_keys=query,top_k)
→ select_candidate → candidate_arguments → select_group → select_capability
→ native_assessment(foreign_evidence_required)
→ foreign_selection mode=enrichment capability=teo.get_catalog
→ teo.get_catalog ok → discovery_terminal CAPABILITY_NOT_ENUMERABLE → foreign_invocation ok
→ relevance_recovery reinvoke davi.discover_delpi_information (arg_keys=query)
→ select_candidate → candidate_arguments
→ davi.execute_delpi_information ok 74ms (arg_keys=arguments,candidate_token)
→ cri_response presented=0 delivered=0 → outcome_assessment empty_result
```

**E2 — `correlation_id=a5283249-222f-4c8a-a58b-5e013b89446e`** ("último processo do Transforma+", ~23s, 5 model calls):

```
interaction_admission → select_group(mcp:teo) → select_capability(record_read)
→ goal_understanding interpreted class=read comparison=False output_mode=snapshot
→ native_assessment(sufficient) → plan(direct) → arguments built
→ teo.record_read ok 43ms (arg_keys=action,entity,q)
→ cri_response presented=0 delivered=0 → outcome_assessment empty_result
```

## 2. Causal replay — what is proven

### Proven at the projection boundary

`provider_invoke decision=ok` requires `provider.invoke()` to return — an `isError=true` CallToolResult raises `SpecialistInteropError` upstream and logs `decision=error`. Both incidents therefore carried `success:true` envelopes.

`delivered=len(facts.records)` at `cri_response`. `facts.records` comes from `outcome_facts(outcome.structured)` → `extract_pagination_envelope` → `_synthesis_records`.

Deterministic replay of the **real owner payload shapes** (captured live from `delpi-api-delpi` / `delpi-transformometro-api` in-container, same code as prod images):

| Replay | `outcome.structured` shape | `facts.records` |
|---|---|---|
| `davi.execute_delpi_information` + `{"description":"terminal bala"}` | `{action_id,status,data:{items:[6 TERM. BALA products],total:6,...}}` | **6** — projects correctly |
| `davi.discover_delpi_information` | `{query,candidate_count,candidates:[5],capability_surface,...}` | **5** — *candidates projected as business records* |
| `teo.record_read(action=search,entity=process)` | `{success,message,data:{total:109,items:[40]}}` | 40 — projects correctly |
| `teo.record_read(...,q="Transforma"|"último processo")` | `{success,...,data:{total:0,items:[]}}` | 0 — authoritative empty |

**E1 proven divergence chain:**

1. `presented=0` on an `ok` execute whose shape is verifiably projectable ⇒ the owner legitimately returned `items=[]`/non-list **for the args actually sent**. Replay also shows `arguments={"description":"dois exemplos de terminal bala"}` (verbatim user text in the filter) returns `total=0` under the corrected owner AND-semantics — a plausible concrete trigger, but arg *values* are sanitized out of logs → the exact arg divergence is `TO_INVENTORY`, never synthesized.
2. **First proven divergence (deterministic):** the discover outcomes project `candidates` into the business-record channel. `_resolver_entities` prefers the `candidates` collection key (correct for entity resolution) and `_is_capability_descriptor` does not recognize the DAVI candidate vocabulary (`candidate_token`, `action_id`, `argument_schema`, `semantic_hints`, `retrieval_score`, `required_arguments`, `pagination_hints`). Consequences: `_activity_outcome_summary` emits `record_count=N` → the "2 registro(s) localizado(s)" the user saw at SOURCE_QUERY_COMPLETED were **capability candidates, not products**; and `outcome_facts` marks `has_business_evidence=True` on DISCOVERY outcomes, suppressing the `contract_facts` fallback.

**E2 proven divergence chain:**

1. `record_read` `process` filterable fields = `{filial_id,setor_id,status,familia_processo,q,has_improvement,page,page_size}` — **no ordering/date fields**. Any natural-language `q` (`"último"`, `"Transforma"`) → `total=0` (replayed). Unfiltered search → `total=109`, items carry comparable `created_at`/`updated_at`.
2. The owner-empty was authoritative for the sent args; "último" requires either a full pagination walk + `updated_at` ordering or a typed limitation. `goal_understanding` captured `output_mode=snapshot` with no ordering requirement — an interpretation/argument-generation gap, which is model-owned semantics under the boundary contract (no deterministic lexical shortcut may be added; no prompt change is authorized).

### Diagnosis gate (§9)

```
INCIDENT=E1
FIRST_PROVEN_DIVERGENCE=evidence projection — DISCOVERY candidates
  extracted as business records (activity record_count + facts.has_business_evidence)
LEGITIMATE_OWNER=delia-api outcome projection
  (outcome_assessment._is_capability_descriptor + _resolver_entities)
CAUSAL_MECHANISM=descriptor-shape vocabulary incomplete for the
  owner-published candidate contract
EVIDENCE=deterministic replay + RED tests
REPRODUCED=YES
FIX_LOCATION=outcome_assessment._CAPABILITY_DESCRIPTOR_STRONG_KEYS
CONTRACT_CHANGE_REQUIRED=NO

INCIDENT=E1 (final empty claim)
FIRST_PROVEN_DIVERGENCE=authoritative-empty owner page for the sent
  args; the sent arg values are unrecoverable from sanitized logs
CAUSE_STATUS=TO_INVENTORY (argument-generation semantics, model-owned)

INCIDENT=E2
FIRST_PROVEN_DIVERGENCE=ordering goal formulated as text filter `q`
  → authoritative empty presented as empty_result
CAUSE_STATUS=PROVEN mechanism; the interpretation/argument stage is
  model-owned (no lexical shortcut, no prompt change authorized)
```

## 3. Responsibility inventory (§10)

| RESPONSIBILITY | OWNER | CONTRACT | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|---|
| Envelope/pagination detection | `paginated_result_semantics.extract_pagination_envelope` | structural | YES | REUSE |
| Business-record projection | `outcome_assessment._resolver_entities` / `orchestration._synthesis_records` | `record_resolver` injectable seam | YES | EXTEND (descriptor vocabulary) |
| Descriptor classification | `outcome_assessment._is_capability_descriptor` | canonical strong/weak key sets | YES | EXTEND |
| Typed facts | `outcome_assessment.outcome_facts` | `EvidenceFacts`, class-aware `contract_facts` | YES | REUSE |
| Verdicts A/B/C/G | `assess_outcome` → `empty_result`/`envelope_only`/`insufficient`/`answered`/`contract_facts` | typed | YES | REUSE |
| Activity summary | `_activity_outcome_summary` | `record_count` only when counted | YES | inherits the fix |

## 4. Fix (minimal owner diff)

`outcome_assessment.py` — `_CAPABILITY_DESCRIPTOR_STRONG_KEYS` extended with the owner-published candidate vocabulary: `candidatetoken`, `argumentschema`, `semantichints`, `retrievalscore`, `paginationhints`. 12 added lines; no new port, helper, or contract. `candidates` stays a preferred collection key — the *shape*, not the key, is the criterion, so entity-resolution candidates still project.

DELIA planner/LangGraph/prompts/budgets/auth untouched; no provider metadata promoted to authority; no model output promoted to FACT.

## 5. RED → GREEN

`tests/test_c3_evidence_to_answer_isolation.py` (10 tests, real replayed shapes as sanitized fixtures):

- **RED before fix (5):** discovery candidates project as records; `_synthesis_records` returns descriptors; activity `record_count` on discovery; DISCOVERY outcome suppresses contract_facts; sparse `{candidate_token}` entry extracted.
- **GREEN after fix (10/10):** all five corrected; locks preserved — execute envelope projects products (E1 terminal shape), TÉO record_read envelope projects (E2 shape), authoritative empty stays distinguishable, dense business record with homonymous `action_id` survives, entity-resolution `candidates` still project.

Focused regression: `test_c3_contextual_discovery`, `test_i02_grounded_knowledge_synthesis`, `test_r45_pagination_integrity_rework`, `test_r4_r5_personal_ticket_count_and_pagination` — 131 GREEN; CRI/evidence/relevance/pagination suites — all GREEN.

## 6. Efficiency assessment (§14/§17)

The E1 detour (`teo.get_catalog` enrichment on a DELPI product query → `CAPABILITY_NOT_ENUMERABLE` → recovery re-discover) cost ~4 model calls / ~21s for zero evidence — model-side selection noise inside existing budgets; no structural fix earned by one incident. The descriptor fix removes a false "located records" signal that fed user perception (and potentially relevance judgment) — it does not by itself cut model calls; measured token savings are not claimed (fixtures invoke no provider). `MODEL_CALLS_BEFORE_AFTER = 14→? (not measurable offline)` / `TOKENS = not claimed`.

## 7. Replaceability verdict (§11/§13/§18)

The proven responsibility (business-record projection) already sits behind the injectable `record_resolver` seam on `outcome_facts`, with the descriptor classifier as its shared gate — a future alternative extractor can satisfy the same conformance surface without touching the orchestrator. **NO_NEW_PORT_REQUIRED** — the defect lived inside an existing contract, not in a missing boundary.

## 8. Residuals (honest evidence gaps)

- **E1 arg values unrecoverable** (sanitized logs carry keys only) — the exact arg divergence stays `TO_INVENTORY`; replay shows verbatim-phrase descriptions now legitimately return `total=0` under owner AND-semantics (arg *quality* is model-owned).
- **E2 ordering intent** — `process` has no owner ordering fields; a truthful "latest" needs pagination walk + `updated_at` ordering or a typed limitation. Goal-interpretation completeness is model-owned; no deterministic shortcut added.
- **Pre-existing failures at HEAD (not this diff):** `test_cri_instruction_variant_carries_requirements_clause` (concurrent commit added `answer_requirements` to the governed goal text — stale assertion), `test_infra_and_env_carry_no_direct_delpi_wiring` (`env.example` residual).

## 9. Acceptance verdict

AC01 ✔ (E1 divergence proven), AC02 ✔ replayed, AC03 ✔ owner fix, AC04 ✔ single projection owner, AC05 ✔ (nonempty evidence cannot silently become empty — regression-locked), AC06 ✔ typed verdicts kept distinct, AC07/08 ✔, AC09/10 ✔ engines untouched, AC11 ✔ budgets intact, AC12 ✔ no dependency, AC13 ✔ existing seam suffices, AC14 ✔, AC15 ✔ (2 pre-existing failures only), AC16 ✔ doc+ledger, AC17 ✔ no deploy.
