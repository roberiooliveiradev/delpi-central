# DAVI Enterprise Stage 3 — offline broker acceptance 005

Base: `91e7eb921c98491cfed693550bd47c3af7474377` (PR #71), current Stage 3 fixture EI01–EI14. End-user parity, runtime and Knowledge provider remain unproven without deploy.

## Scope
- Use actual `get_technical_actions`, lexical broker discovery, candidate token mint/parse, execution plan, projected output, and an **in-memory fake canonical executor**. No DB, SSH, Keycloak, Core HTTP or Agent Studio.
- Positive coverage: EI01–EI07 retrieval; EI08 conceptual no-candidate; EI09 mixed intent with source-appropriate candidate; EI02 + EI07 successive bounded reads with owner-approved output filtering.
- Negative: fake backend forbidden ⇒ no success; actor-bound candidate token cannot be used by another actor; required branch validation and arbitrary URL/operationId smuggling fail before adapter.
- Core proposal: `TO_INVENTORY` with explicit approval gates and no registered DAVI tool. Business owner and audience compatibility remain unratified.
- The fixture's mock values are synthetic (e.g. `SYNTHETIC-OP`) and **do not prove** runtime business data or a global shortage decision.

## Evidence ladder
| Gate | State |
|---|---|
| Source implementation and contract review | IMPLEMENTED_ON_BRANCH |
| Focused Python tests on GitHub Actions | PENDING_CI |
| Prior Stage 1–3 integrated CI | PASS at SHA `79254c61df11d525d80620426543c63664dc1500` |
| Concept-routing integrated CI | PASS at SHA `5e7b07785d2853836651566b7786de8dc1a8de33` |
| Core owner contract ratification | TO_INVENTORY |
| Agent Studio Files + K01–K10 | TEST_NOT_RUN |
| End-user second-person negative backend AuthZ | TEST_NOT_RUN |
| Deployment/runtime, rate decision, publication | PENDING |

No merge/deploy or authorization change.

## CI root-cause correction after first integration failure

GitHub Actions at integration `1f48a08a65556fd667b0464f805ec8c0d46ccb3a` produced 9 FAIL / 141 PASS. Six of the failures shared a single cause: the approved `get_product_raw_material_set_shortages` action was invisible for E07's natural-language paraphrase, whereas the wrong `get_product_production_status` appeared. E01 item-description query returned metadata-column search instead of `search_products`. A third failure incorrectly equated allowlist entries (89) with runtime baseline eligible actions (87); those inventories represent different contracts.

Fix in the `api-delpi` semantic allowlist owner: add explicit item-description and per-product production-set shortage synonyms; no change to operation set, input/output projections, endpoints, RBAC, or runtime executor. Fix the test to measure real broker eligible actions rather than a hardcoded allowlist count. Add positive and semantic sibling tests: metadata-column and normal production-status queries must remain discoverable.

All owner/runtime tests must be re-executed on the new commit. No weakening of hard-negative, actor binding, input protection or provider gates.
