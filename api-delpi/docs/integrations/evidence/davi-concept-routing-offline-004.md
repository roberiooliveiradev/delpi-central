# DAVI — Conservative concept-only routing guard (offline corrective 004)

Owner: `api-delpi` dynamic READ retrieval/routing; source of truth and backend AuthZ unchanged.

## Root cause
Observed on connected DAVI MCP on 2026-10-14 (deployed agent-directives v2026.10.07.2): `O que significa MI?` returned unrelated READ candidates. Staged Knowledge Orchestration directives are insufficient to guarantee no irrelevant broker matches when the model still invokes discover for purely conceptual questions.

## Scope and rationale
- A conservative syntax-only, endpoint-agnostic `is_pure_concept_intent` guard runs before the already eligible-operation retrieval ranking.
- Does not interpret MI, calculate values, know entity permissions or select business operations.
- Only suppresses clearly single-intent concept/definition/difference questions. Mixed concept+data, unknown/ambiguous, temporal, and normal READ questions remain available through the existing broker.
- No new MCP tool, input/output field, path, actor, permission, credential, SQL, join, data source or business capability.
- Declarative Agent Knowledge route remains the intended answer source but is **not claimed available** until native Files sync and K01–K10 provider Preview.
- Search returning zero candidates here means **not routed to an operational action**, not `no documents exist` or `no data exists`.

## Verification
- Python unit tests for 11 pure concept cases, 10 mixed/operational cases, one actual mixed stock retrieval, one discover zero-candidate shape, and synthetic actor-bound HMAC negative token case.
- Re-run existing 217-case discovery benchmark + global integration CI to prevent regression.
- Status: `SOURCE_IMPLEMENTED`; GitHub Actions CI `PENDING`; deployed MCP `TEST_NOT_RUN`; provider knowledge `TEST_NOT_RUN`.
- Deployment and Agent Studio updates explicitly deferred until SSH/provider availability and approved release.
