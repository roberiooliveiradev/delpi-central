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
