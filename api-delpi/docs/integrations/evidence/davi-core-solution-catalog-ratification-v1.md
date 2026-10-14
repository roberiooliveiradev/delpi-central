# DAVI — Core Solution Registry Contract Ratification (DRAFT / NOT AUTHORIZED)

**Date:** 2026-10-14  
**State:** `TO_INVENTORY` — design proposal only, not an implementation decision.  
**Architectural escalation:** DAVI — Architecture / Coordination; the Core technical owner is `core-api`. The business/human owner remains to be ratified. This document does not approve cross-context access.

## Factual inventory (source-grounded)

The Core API owns `GET /solutions` and `GET /solutions/<plugin_id>`, both authenticated with `@require_auth()`. The list exposes safe projections of **all ACTIVE registered solutions**, not only solutions a user can open; `accessible` reports Core's access decision and never grants it. Source: `core-api/app/interfaces/http/solutions_controller.py`, `list_solutions_use_case.py`, and `solution_projection.py` at main SHA `8dc1fcc57a792788b3e7cfb5dd7023733b29d891`.

Core currently projects `id/name/description/icon/type/category/version/active/basePath/routes/features/permissions/dependencies/accessible/updatedAt` and detail-only recent versions/evolution. These exposed fields are **source inventory**, not approval to republish all fields in DAVI.

TÉO has a `SolutionCatalogPort` + Core gateway pattern; VISTA has a source-scoped fallback after a TV route miss. These examples **do not grant DAVI access** or prove its MCP token can call Core. Do not import other bounded contexts' Domain/Application code.

## Proposed narrow READ

| Decision dimension | Proposed position | Status |
|---|---|---|
| Business need | “Qual app Minha DELPI atende este processo?” | `PLANNED` |
| Technical owner/source | `core-api`, authenticated `/solutions` | `PROVEN` |
| Human business owner | Named organizational owner and approval | `TO_INVENTORY` |
| Consumer | DAVI, knowledge-only solution discovery | `PLANNED` |
| Input | `query` (process/solution phrase); not transcript or SQL | `TARGET` |
| Output allowlist | `id,name,description,category,accessible` | `TARGET` |
| Candidate cap | 5; no broad catalog or arbitrary pagination to model | `TARGET` |
| Identity | Existing End-user account; no service account | `TARGET` |
| Cross-context auth | Validate Core audience acceptance and per-user Core AuthN/AuthZ | `TO_INVENTORY` |
| Evidence | Registry fields `OBSERVED`; phrase→app relevance `INFERRED` | `TARGET` |
| Denial | Fail closed; no fallback service identity | `TARGET` |
| No-match | “No match in consulted source”, not “no app exists” | `TARGET` |
| Privacy | Do not expose permission UUIDs, role graph, tokens, private manifests | `TARGET` |
| Rate | Proposed bounded lookup needs approved per-user rate policy | `TO_INVENTORY` |

`accessible=false` is **not the same as 403 from a domain API**. The existence of a registered solution is metadata, not business access to its records. No automatic “click to open” or invoke an app based only on the catalog.

## Ratification gates / implementation boundary

1. Product/business owner ratifies the business use case and output minimization.
2. Core owner confirms public API schema stability, metadata privacy, Core AuthN policy and audience acceptance for DAVI's End-user token; a TÉO working implementation is **not** proof of DAVI's audience/parity.
3. DAVI Coordination approves the cross-context consumer boundary and routing priority (only when existing domain sources cannot answer).
4. Security approves trace/redaction, negative AuthZ, Core failure handling, per-user limits and rate policy.
5. Only then: add a typed `api-delpi` port + an infrastructure HTTP adapter, with a minimum new semantic capability, tested with fake Core provider, real Core integration and second-user denial before provider registration.
6. Provider tool discovery and production deployment are separate final gates.

**NO CODE IS AUTHORIZED** for this Core integration by this document. The machine-readable proposal at `davi-core-solution-catalog-ratification-v1.json` is subject to review and not a runtime source or model allowlist.

## Non-goals

No generic Core API proxy, arbitrary URL/method, service-account user parity, cross-db imports, Core RABC duplication, direct SQL, extra DAVI MCP tool yet, writes or decision engine. If these assumptions change, return to DAVI Architecture / Coordination.
