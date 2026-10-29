# Product Description Search Remediation — Industrial Matching

- Task: `DELIA-C3-API-DELPI-PRODUCT-SEARCH-REMEDIATION-01` (follow-up
  owner remediation requested by DÉLIA doc 203)
- Date: 2026-10-29
- Scope: `search_products` description matching only
- Owner: `api-delpi` / `ProductRepository` (TOTVS `SB1010`)
- Production code changed: 1 repository + 1 new matching module
- Schema/migrations: none. New dependencies: none. New services: none.

## 1. Proven root cause

`ProductRepository.search_products` split the `description` filter on
whitespace and OR-joined each token as an unbounded substring LIKE
(`%t%`), with a weak scorer (`+100` phrase prefix, `+20` token prefix).

Consequences proven against the real TOTVS `SB1010` (local
`delpi-api-delpi` container, same database family as production):

| Query | Before | After |
|---|---|---|
| `TERM. BALA` | 1,678 hits (correct, but noise flood) | **6** — all TERM. BALA family |
| `terminal bala` | 445 hits, expected products absent | **6** — `10080092` rank 1 |
| `bala` | 33 hits, BALANCA/BALANCIM dominate top | 21 hits, exact-word BALA products rank first (`10080092` #2) |
| `TERM BALA` | 3,404 hits | **6** |
| `Terminal Bala` (mixed case) | 445 | **6** |
| `terminal de bala` (held-out) | — | **6** |
| `terminal` | 412 | 2,248 (semantically correct — all terminals incl. `TERM.` abbreviations) |
| `TERM.` | — | 2,248 |
| `cabo flexivel` | 6,666 | 108 |
| `parafuso sextavado` | 225 | 11 |
| `BALANÇA` (accent) | — | 9 (AI collation folds Ç→C correctly) |
| `terminal 6,3` (numeric) | — | 300 |
| `xyzzy kqqq` | 0 | 0 (honest empty) |
| `parafuso` | — | 211 |
| `conector` | — | 1,487 |
| exact code `10080092` | 1 | 1 (untouched path) |
| empty description | — | 55,350 (no filter — same as before) |

## 2. Chosen strategy (smallest correct fix)

All in `app/infrastructure/persistence/totvs/product_repositories/`:

- **B — AND semantics**: every significant query token must match.
  Portuguese connectives (`de`, `da`, `e`, `para`, `com`, …) are dropped
  so connectors cannot force impossible AND clauses; if the query is
  stopword-only, raw tokens are kept.
- **C — Controlled abbreviation bridging**: a small reviewed table maps
  `TERMINAL ↔ TERM` (the proven catalog equivalence). The abbreviated
  member requires an *exact-word* match — `TERM` never prefix-matches
  `TERMO*`/`TERMINALO`. Unknown abbreviations get **no** expansion
  (P11). The table is deliberately minimal; new entries require the
  same owner review.
- **D — Word-boundary matching**: tokens match as word-prefixes using
  `CONCAT(' ', col) LIKE '%[^A-Z0-9]{token}%'` — a token must start a
  word (start of description or after a non-alphanumeric char). Interior
  substrings (`REPARO`→`PAR`) no longer match.
- **Relevance scoring**: exact-word hits (+30) outrank word-prefix hits
  (+15). Multi-token phrase-prefix bonuses (+100 raw, +60 normalized
  `TERM.`→`TERM`) preserved **with a word boundary required after the
  phrase** — this prevents `TERM BALA%` from promoting `TERM BALANCA`
  items, and single-token queries skip phrase bonuses entirely (a
  single token's "phrase prefix" is just prefix noise, which is why
  `BALANCA` used to outrank `BALA` products — a pre-existing scorer
  defect also corrected).

Rejected alternatives: full-text/Elasticsearch/vector search (new
service — explicitly out of scope); unrestricted synonym dictionary
(task forbids); pure substring-AND without expansion (cannot bridge
`terminal`→`TERM.`).

## 3. Contract compatibility

- Request/response JSON shape unchanged (`Page[Product]`); filters
  `code`, `group_code`, `subgroup`, `product_type`,
  `customer_reference`, `page`, `page_size`, `sort`, `direction`
  untouched.
- **Behavioral change** (documented, intended): multi-token
  `description` queries now require all significant tokens; result
  totals shrink accordingly. Single-token queries keep recall (word
  prefix instead of interior substring — strictly more precise).
- `relevance_score` remains a projection used only for ordering;
  Product entity fields unchanged.
- Consumers verified: `gpt_search_products` (DAVI/DÉLIA path),
  supplies products router, `ProductAnalyserUseCase` (uses `code`
  only — unaffected), `product_search_service` external capability.
- Authorization, authentication, provenance, read-only semantics:
  unchanged. All patterns remain `?`-bound params with `ESCAPE '\'`.

## 4. Tests

`tests/test_product_description_matching.py` — 20 contract tests:
token normalization, stopwords/fallback, AND grouping, word-boundary
params, TERM↔TERMINAL bridge (both directions), unknown-abbreviation
non-expansion, LIKE-metachar escaping (`%`, `_`, `[`), `ESCAPE`
presence on every LIKE, scoring contract (multi-token phrase bonuses,
single-token exclusion, exact>prefix ordering), param alignment, and
repository integration.

Regression: `tests/test_product_description_matching.py` +
product/search consumer suite — 143 passed, 1 pre-existing env failure
(`test_v3_flow_b_web_research_starts_from_register`, fails on clean
HEAD — unrelated DAVI acceptance test).

## 5. Performance

Description search was and remains a bounded table scan (`LIKE '%…%'`
cannot use an index; `OFFSET/FETCH` pagination and total count
preserved). The `CONCAT`-padding formulation keeps each exact-word test
at one LIKE. Measured on real `SB1010`:

| Query | Baseline ms | New ms |
|---|---|---|
| `terminal bala` | 3,077 | ~2,300 |
| `TERM. BALA` | 1,804 | ~3,300 |
| `bala` | 1,374 | ~1,200 |
| `terminal` | 842 | ~2,400 |
| `cabo flexivel` | 1,511 | ~1,300 |
| `parafuso sextavado` | 1,542 | ~2,400 |

Heavier single-token expansion queries (~2.4s) do legitimately more
work (2,248 matching rows vs 412). No new index or timeout change
required; no unbounded fetch introduced.

## 6. Files changed

- `app/infrastructure/persistence/totvs/product_repositories/product_description_matching.py` (new)
- `app/infrastructure/persistence/totvs/product_repositories/product_repository.py` (description block only)
- `tests/test_product_description_matching.py` (new)

## 7. Residual limitations

- Equivalences beyond `TERM↔TERMINAL` (e.g. `FLEX.`↔`FLEXIVEL`,
  `SEXT.`↔`SEXTAVADO`) are **not** expanded — each requires the same
  domain-approved evidence loop before being added to the table.
- Descriptions remain authoritative `SB1.B1_DESC`; no alternate-name
  index exists owner-side.
- Ranking is heuristic (phrase > exact-word > word-prefix), not
  learned relevance.
