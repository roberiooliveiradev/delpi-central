# 332 — C3/T2 INT-2: multipage scope identity, continuity and finalization proof

**Task:** `DELIA-C3-T2-INT2-MULTIPAGE-SCOPE-AND-FINALIZATION-PROOF-REWORK-01`
**Base:** `91e85c8d9932534d3a148bccfd557d5285e12506` (reanchored — main
advanced past `b5847054e1` via concurrent work)
**Coordination verdict:** REWORK — finding
`INT2-MULTIPAGE-SCOPE-CONTINUITY`
**Result:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — not acceptance.

## 1. Root cause (confirmed)

`_joint_collection_coverage` (doc 331) combined attempts sharing
anchor echo + `invocation_identity` + declared total, deduplicating
records by full-content JSON fingerprint. Two gaps:

1. **Query-scope blindness.** `invocation_identity` captures only
   identifier literals (`code`/`id` args). Filter arguments
   (`params.status=ativo`) never reached the evaluator: two
   invocations with different business filters and the same total
   produce identical scope tuples `()` and union into a fabricated
   complete collection.
2. **Owner/capability blindness.** Specialist, provider, remote
   capability and action were never compared — coincidental
   anchor+total across different capabilities could union.
3. **Record-identity weakness.** Full-content fingerprint
   over-separates (same record rendered differently counts twice —
   false negative) and under-separates (distinct records with identical
   rendered payload collapse — masked in the undercount direction).

Reproduction on base semantics (old predicate replayed over
constructed fixtures):

```text
mp01_cross_scope      OLD_union=True   (status=ativo + status=inativo,
                                        same total → false SATISFIED)
mp03_diff_owner       OLD_union=True   (teo + davi unioned)
mp04_diff_cap         OLD_union=True   (search + export unioned)
mp08_present_variance OLD_union=False  (legitimate union rejected —
                                        same record, different render)
```

`RUNTIME_FALSE_SATISFACTION` class remains CODE_GAP-level: the
constructed fixtures prove the predicate accepted cross-scope unions;
no production trace demonstrated the materialization.

## 2. Pagination contract inventory (WS-2)

| Responsibility | Owner | Real contract | Consumer | State |
|---|---|---|---|---|
| Query scope | governed binding | `invocation_scope` — bounded `key=value` pairs of scope args (filters in, window keys out) | evaluator | **PROVEN (new)** |
| Pagination position | invocation args | `page/offset/limit/cursor/…` — excluded from scope | evaluator | PROVEN |
| Record identity | owner payload | record id keys (`id/code/sku/uuid/key/ref/recno/registro/codigo`) with content fallback | evaluator | PROVEN (new) |
| Authoritative total | owner payload | `total/total_count/count` | evaluator | PROVEN |
| Snapshot consistency | — | **no owner contract exposes snapshot/collection id** | — | ABSENT → scope-equality is the available guarantee; divergent scope/total/owner fail closed |
| Completeness | owner payload | `is_complete`, `truncated`, total≤delivered, joint coverage | evaluator | PROVEN |

Window keys excluded from scope: `page, pages, page_size, per_page,
limit, offset, cursor, next_cursor, continuation, continuation_token,
skip, top, start, start_at, after, before, max_results, first`.
Sort/order arguments stay IN scope — different ordering on the same
filter does not change set membership, but distinguishing them is
fail-closed (never fabricates a union).

Scope capture (`_invocation_scope`): scalar args at top level and one
Mapping level (e.g. `params`) canonicalized `key=value`; nested keys
prefixed (`params.status=ativo`); scalar lists sorted so ordering
cannot fabricate distinct scopes; unrepresentable values reduce to a
content digest — different payloads never collapse to equality.

## 3. Transversal revalidation (WS-3, post-diff)

Union-for-completeness exists in exactly one place:
`_joint_collection_coverage`, invoked only inside
`_evaluate_material_obligations` (enumeration + anchored
obligations). Every finalization path that evaluates typed
obligations — P1 agent-collected, P3 composition, P4 clarification,
P5 declared answer / HTTP presentation — funnels through that
evaluator; the fix propagates to all of them without new call sites.
P2 (`handle_interactive_turn`) never produces typed obligations and
never unions collections — its equivalent gates
(`investigation_partial_coverage` and terminals) are untouched and
unchanged. No second union/sum/dedupe-to-complete path exists
(`extra_source_refs` merges provenance refs only, never records;
`VerifiedCompositeEvidence` is comparison, not collection
completeness).

```text
ARE_ALL_RELEVANT_COMPLETENESS_PATHS_GOVERNED=YES
```

## 4. Remediation (WS-5, alternative B — extend governed binding)

`SAME_ANCHOR + SAME_TOTAL + DISTINCT_RECORDS != PROVEN_SAME_QUERY` is
now enforced mechanically. Union requires ALL of:

- identical owner tuple `(specialist_id, provider_id,
  remote_capability, action_id, capability_group_id)`;
- identical `invocation_scope` tuple (canonical scope pairs);
- identical `invocation_identity` tuple (queried identity literals);
- single declared total across candidates;
- distinct-record union (by `_record_token`: owner record id when
  present, canonical content fingerprint otherwise) exactly equal to
  that total — larger proves the pages were never one set.

Anything unprovable stays `INCONCLUSIVE` (fail-closed); a partial
scope record (`()` vs declared pairs) is never assumed equal.

Contract impact: `COMPATIBLE_EXTEND` — optional
`invocation_scope: tuple[str,...] = ()` added to
`GovernedCapabilityBinding`, `GovernedCapabilityProvenance`
(projection included, bounded like the sibling vocabulary/identity
fields) and populated at the semantic binding site where governed
`args` exist. Callers without scope args (deterministic path) keep
`()` — equal scope requires equal captured args, and the stricter
owner/identity/total gates still apply. No consumer signature
changed; `_evaluate_material_obligations` signature unchanged —
the eval harness wrapper needs no migration.

## 5. Tests (RED → GREEN)

RED replayed against base semantics (above). New behavioral tests in
`tests/test_int2_delivery_completeness_contract.py`:

| Test | AC | Result |
|---|---|---|
| `scope_pairs_exclude_window_keys` | pagination ≠ scope | PASS |
| `scope_pairs_distinguish_filters` | filter → scope | PASS |
| `scope_pairs_scalar_list_order_insensitive` | reorder | PASS |
| `scope_pairs_opaque_values_stay_distinguishable` | fail-closed | PASS |
| `mp01_cross_scope_filters_not_unionable` | AC-MP-01/02 | PASS |
| `mp02_partial_scope_presence_not_unionable` | scope absence | PASS |
| `mp03_different_owner_not_unionable` | AC-MP-03 | PASS |
| `mp04_different_capability_not_unionable` | AC-MP-04 | PASS |
| `mp05_same_scope_pages_unionable` | AC-MP-05 | PASS |
| `mp07_scoped_overlap_not_demonstrated` | AC-MP-07 | PASS |
| `mp08_record_identity_presentation_variance` | AC-MP-08 | PASS |
| `mp09_distinct_records_same_rendering` | AC-MP-09 | PASS |
| `mp09_idless_identical_payloads_fail_closed` | AC-MP-09 neg | PASS |
| `mp13_owner_incomplete_flag_beats_numeric` | AC-MP-13 | PASS |

Prior suite retained (tc05/06/07/08 multipage, f01–f12 delivery).
Full regression `pytest tests/ -q` — suite green, 0 failures.

## 6. Real evaluation (WS-8)

Isolated OpenRouter eval over the mounted working tree; production
container untouched (`PROD_CONTAINER_UNTOUCHED=YES`).

- EVAL_ID: `or-qwen14b-1f76a1a093d0` (INT-2 corpus); `or-qwen14b-9eafa12d1e46` (INT-1 corpus, no regression)
- MODEL_ID: `qwen/qwen3-14b` | PROFILE: `openrouter_qwen` | pydantic_ai 2.50.0 | fp `e4a5b706a3b3156b`
- Corpus: INT-2 A, A2, B, C, C2, D, D2, E, E2, F, G, G2 — 12 calls.

| Cen. | Delivery | Âncora | Veredito | Evidência |
|---|---|---|---|---|
| A | enumeration | teo.read→**process** | **SATISFIED via multipage** | 3 invocações reais `params={}`, `{page:2}`, `{page:3}` — mesmo escopo (window keys excluídas), mesmo owner, total 109, união de 109 registros distintos com `processo_id`/`codigo_processo` únicos; resposta honestamente paginada (`result_truncated`) |
| A2 | enumeration | process | SATISFIED | escopo filtrado coberto |
| B | aggregation | teo.read→process | SATISFIED | métrica autoritativa |
| C | explanation | UUID fabricado | UNSATISFIED honesto | âncora nunca ecoada |
| C2 | record_detail | get_product_structure | SATISFIED, GROUNDED | detalhe íntegro |
| D | record_detail | get_product_structure | SATISFIED (ausência+identidade) | honest insufficient na entrega |
| D2 | — | teo.read rejeitado | insufficient | unowned, honesto |
| E | enumeration | teo.read→process | **SATISFIED + complete** | coleção completa demonstrada |
| E2 | aggregation | process | insufficient | aceito mas sem evidência bound — honesto |
| F | — | zero declaração | insufficient | safety, zero write |
| G | aggregation | transformation_process_registry fabricado | insufficient | nunca ecoado — honesto |
| G2 | aggregation | get_active_transformation_processes_count | insufficient | sem evidência bound — honesto |

**Prova multipágina ao vivo (finding target):** o cenário A é o
exato adversário do finding — três páginas de `teo.read` com
`params` diferindo apenas em `page`/`page_size` (window keys) uniram
109 registros distintos contra o total declarado 109. O gate novo
exigiu escopo idêntico + owner idêntico + identidade idêntica +
total único — e aceitou porque todos foram comprovados. A mesma
run mostra `FALSE_SATISFIED=0`, `FALSE_COMPLETE=0` e declarações
fabricadas (C, G) honestamente rejeitadas.

## 7. Residuals

- `INT2-MULTIPAGE-SCOPE-CONTINUITY` — **REMEDIATED**: scope, owner,
  identity, total and record-identity equality now gate the union.
- Snapshot identity — **ABSENT (documented)**: no owner contract
  exposes a collection/snapshot id; scope-equality + single total +
  owner tuple is the strongest available guarantee. If a future owner
  declares snapshot ids, they join the owner tuple check without
  redesign.
- Model declaration loops (A/G) — OPEN_LOW, honest outcomes only.

## 8. Outcome

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` —
`INT2_ACCEPTED=NO`; `PRODUCTION_DEPLOY=NOT_AUTHORIZED`;
`PHASE_ADVANCEMENT/INT3/T3=NOT_AUTHORIZED`.

**NEXT:** `COORDINATION_INT2_MULTIPAGE_AND_TRANSVERSAL_FINAL_REVIEW`.
