# 289 — DÉLIA · Review P0 hardening: aceite funcional com residuais VISTA/coverage

**DATA:** 2026-11-05  
**TASK_ID REVIEWED:** `DELIA-C3-P0-SOURCE-REFS-AND-DYNAMIC-TOOL-CONTRACT-HARDENING-01`  
**BASE_HEAD:** `745ae26ae69f4bc51e168e9f21e638bcab02e88c`  
**REVIEWED_SHA:** `de8f9db454936c7016068d1f6ac18f54df0cd82e`  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` — P0 real READ grounded and client delivery reported; P1 generalization PARTIAL; production NOT_AUTHORIZED.

## Independent source review

- Exact task commit modifies `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` by extracting `_capability_tool_signature`, using `KEYWORD_ONLY` for schema-derived parameters (handles optional-before-required ordering), filtering invalid/Python keyword/ctx/kwargs names, promoting bounded `enum` values to `Literal`, preserving optional `arguments` bag and Application-owner validation.
- Three focused test modules added: `test_dynamic_tool_signature.py`, `test_candidate_token_boundary.py`, `test_investigation_answer_contract.py`. Code and tests support reported 41 new tests; full suite PASS is executor-reported, not independently executed by GitHub review.
- Candidate-token boundary itself was implemented in previous SHA, not newly modified in this commit; newly added tests cover verbatim relay, invalid input denial, non-candidate capability, orchestrated keys and malformed argument object. This is not evidence that arbitrary owner-issued tokens authorize anything; owner/Core remains authoritative, and real cross-session/owner replay authorization is not established by these fixture tests.
- `InvestigationAnswer.schema_version=Literal["1"]` was introduced in prior SHA; current commit adds positive/negative serialization tests. This is a regression hardening delivery, not a new schema change.
- **Source refs:** doc288 shows the earlier empty `source_refs` check queried the wrong JSON path; supported response contract uses `provenance.sources[]` with source_id, source_system, action_id and observed_at. This corrects the prior diagnostic; no provenance code changed in this commit. These are canonical owner/source identities, not necessarily per-field citations; verify any stronger source granularity claim against the original contract.
- **Documentation drift:** doc288 says `enum/const` mapped to `Literal`; code reads `spec.get("enum")`, does not explicitly read `spec.get("const")`. Do not claim const support without separate proof. Fix documentation or implement only if a legitimate owner contract demands const and tests demonstrate defect.
- **Owner evaluation nuance:** case C invokes `teo.get_context` SUCCESS but answer reportedly sourced from `vista.knowledge`; do not generalize this into verified TÉO business content-grounded answer. Case D VISTA `get_context/knowledge` succeeds while `vista.read/analyze` produce `mcp_protocol_error`; verify provider/owner interface before assigning fault. Case F code 99999999 is an **existing owner record**, so it cannot serve as an absent-record negative oracle; `NON_GROUNDED` due to coverage matching is a meaningful remaining limitation, not proof of correct absent record behavior.
- Doc288 and execution ledger updated with real local eval outcomes and stated partials. No deployment authorized. `DELIA_RUNTIME_SHA` baked vs mounted remains recorded drift; ensure release verification is tied to actual runtime SHA.

## Minimal next work, no orchestration reopening

**A. VISTA owner path:** task `DELIA-C3-P1-VISTA-READ-ANALYZE-PROTOCOL-BOUNDARY-01`. Reanchor authorities, owner contract and MCP adapter, reproduce auth READ with a known-present VISTA dataset, inspect request schema/operation IDs/errors at boundary. If issue in owner, fix owner with contract tests, security/auth and full regression; if provider interoperable adapter, fix there. No second planner, no tool metadata authority, no synthetic business facts. Prove full client response grounded for read and analyze, or mark precise BLOCKED. No production deployment.

**B. DAVI coverage:** task `DELIA-C3-P1-DAVI-SINGLE-RECORD-COVERAGE-BINDING-01`. Reanchor contract/evidence schema and `_uncovered_named_identifiers` before changing code; reproduce actual positive code 99999999, compare owner response identifiers, outcome projection, evidence targets, final coverage decisions. Add RED test for actual response shape; fix minimally if true bug; validate another distinct real code and authorized not-found control. Never reinterpret a present owner record as nonexistent. No manual per-code exception.

**C. Documentation accuracy:** in next bounded task, correct doc288 `const` claim if unsupported, or provide code+contract evidence. Retain frozen decisions and genuine valid code; do not invent new support gratuitously.

For each: same-delivery removal of replaced legacy, fix consumers/imports/config/tests, full regression, residual search, doc/ledger, committed SHA and real end-to-end business outcome. P0 baseline (code 50220013 client delivery and provenance.sources) must remain PASS.

**Review classification:** P0 `ACCEPT_WITH_RESIDUAL`; P1 `PARTIAL`; provenance path false negative resolved, signature/enum fix verified, VISTA protocol and DAVI record coverage remain bounded residuals.
