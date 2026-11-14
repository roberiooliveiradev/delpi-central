# 333 — C3/T2 INT-2: scope fingerprint integrity, pagination semantics and safe multipage grouping

**Task:** `DELIA-C3-T2-INT2-SCOPE-FINGERPRINT-LOSS-AND-SAFE-MULTIPAGE-GROUPING-REWORK-01`
**Base:** `6fb80fe9ea5bfb3e504ba02f15e99751e919d7f3` (reanchored, clean)
**Coordination verdict:** REWORK — `INT2_SCOPE_FINGERPRINT_LOSS`
**Result:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — not acceptance.

## 1. Findings reproduced (RED)

| Finding | Base behavior | Evidence |
|---|---|---|
| R1 — 24-pair cap loses args | scopes differing only beyond pair #24 collided | `test_scope_integrity_beyond_pair_cap` failed (equal) |
| R1b — type blur | `a=5` vs `a="5"` produced equal scope | `test_scope_value_types_distinguish` failed |
| R2 — ambiguous window names | `before`/`after`/`start`/`first`/`top` excluded globally — a business `before` filter vanished | `test_scope_window_keys_unambiguous_only` failed |
| R2b — list order normalized | `[a,b]` ≡ `[b,a]` without contract authorization | `test_scope_pairs_scalar_list_order_sensitive` failed |
| R3 — whole-set scope check | any foreign-scope observation poisoned a valid same-scope union | `test_scope11_valid_subset_with_unrelated_observation` failed |
| — deep nesting | `params.periodo.fim` beyond depth 1 dropped | `test_scope_deep_nested_filters_distinguish` failed |

## 2. Remediation (single canonical mechanism, no new authority)

### R1 — Integrity digest

`_invocation_scope` now strips window keys recursively and emits a
`__scope_digest__=<sha256[:16]>` token over the canonical
serialization of the WHOLE remaining argument set (`sort_keys`,
deterministic separators, list order preserved). The flattened
`path=value` pairs remain (bounded, observability) but the digest is
the integrity proof — differences in any scope argument, at any
depth, of any type, in any list order, can never silently collide.
Serialization failures degrade to a bounded digest anyway; nothing is
dropped.

### R2 — Contract-honest classification

`_PAGINATION_ARG_KEYS` narrowed to unambiguous slice selectors only:

```text
page, pages, page_size, per_page, limit, offset, cursor,
next_cursor, continuation, continuation_token, skip, max_results
```

`before, after, start, start_at, first, top` removed — they are
temporal/business filters in real owner contracts and now remain in
scope (unclassifiable → fail-closed, never excluded). Scalar list
order is preserved (no normalization without contract authority) —
fail-closed. Nested flattening extended to depth 3 for pair
observability; deeper structure still enters the digest intact.

### R3 — Grouped union

`_joint_collection_coverage` now partitions candidates by proven
query identity — `(specialist_id, provider_id, remote_capability,
action_id, capability_group_id, invocation_scope,
invocation_identity)` — and evaluates each group independently:

- a group needs ≥2 attempts and exactly ONE declared total
  (contradictory totals for one scope disprove it);
- the distinct-record union (`_record_token`) must equal that total;
- one complete group suffices; foreign-scope observations neither
  join nor poison it.

Single-attempt completeness still belongs to
`_attempt_collection_proven_complete`; the union never substitutes
for it.

## 3. Contract inventory (WS-A)

Owner invocations observed in traces: `teo.read` args
`{entity, action, params{status?, page?, page_size?}}` —
`page`/`page_size` confirmed slice selectors; `status` business
filter → scope. `davi.read` `{capability, arguments{code}}` —
`code` is identity/scope. No owner exposes snapshot/collection ids
(residual DOCUMENTED_ABSENT). No capability schema currently
classifies arbitrary argument names — hence the conservative
rule: only proven slice names are window; everything else is scope.

## 4. Tests RED→GREEN

14 new scope/grouping tests + prior 26 — all green; full
`pytest tests/ -q` green (0 failures). RED list above covers
AC-SCOPE-01..12 materially (pair cap, deep nesting, window
classification, unknown args, type fidelity, ordering, subset
grouping, cross-scope rejection); owner isolation, record
identity, aggregation, unknown completeness preserved by the
existing suite.

## 5. Transversal revalidation (P1–P5)

Union exists only inside `_evaluate_material_obligations` → the
grouping fix propagates to P1/P3/P4/P5 without new call sites; P2
still has no typed obligations. No other sum/merge/dedupe-to-complete
path exists. `ARE_ALL_RELEVANT_COMPLETENESS_PATHS_GOVERNED=YES`.

## 6. Real evaluation

Isolated OpenRouter INT-2 corpus on the mounted working tree;
`PROD_CONTAINER_UNTOUCHED=YES`.

- EVAL_IDs: `or-qwen14b-fcfbab951da1` (INT-2 ×12) + `or-qwen14b-dce013ef2394` (A/B focado)
- MODEL_ID: `qwen/qwen3-14b` | pydantic_ai 2.50.0 | fp `e4a5b706a3b3156b`

| Run | Cen. | Resultado |
|---|---|---|
| fcfbab | A | `process` aceito; needs_clarification honesto (teo instável) |
| fcfbab | A2 | **SATISFIED** + `declared_unmet_overridden` (avaliador prevalece) |
| fcfbab | B..G2 | insufficient honesto — `mcp_authentication_failed` intermitente em teo; `declared_status_overridden` aplicado onde declarado complete |
| fcfbab | F | zero declaração, zero write — seguro |
| dce01 | A | 1 página (`params={}`, 40/109) → **INCONCLUSIVE** — completude desconhecida preservada, nenhum falso SATISFIED |
| dce01 | B | aggregation `process` → **SATISFIED** + `complete`, GROUNDED |

A prova multipágina real (3×`teo.read` `params={}/page2/page3` →
109 distintos == total) já foi demonstrada em
`or-qwen14b-1f76a1a093d0` (Doc 332); neste SHA o agrupamento
preserva o mesmo comportamento — as três páginas compartilham
owner+scope-digest+identity e unem — coberto deterministicamente
(`scope11/mp05`) e pela direção fail-closed observada ao vivo
(página única parcial → INCONCLUSIVE). `FALSE_SATISFIED=0`,
`FALSE_COMPLETE=0`, `FALSE_INCONCLUSIVE=0` nas duas runs.

## 7. Residuals

- `INT2_SCOPE_FINGERPRINT_LOSS` — **REMEDIATED**: digest covers the
  whole arg set; ambiguous names stay in scope; list order honored.
- Snapshot identity — DOCUMENTED_ABSENT (no owner contract).
- Argument semantics beyond names — DOCUMENTED: unclassifiable
  args default to scope (fail-closed); no owner metadata currently
  declares filter-vs-window semantics.

## 8. Outcome

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — `INT2_ACCEPTED=NO`;
`PRODUCTION_DEPLOY=NOT_AUTHORIZED`;
`PHASE_ADVANCEMENT/INT3/T3=NOT_AUTHORIZED`.

**NEXT:** `COORDINATION_INT2_SCOPE_INTEGRITY_AND_FINAL_ACCEPTANCE_REVIEW`.
