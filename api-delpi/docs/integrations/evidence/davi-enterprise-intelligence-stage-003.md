# DAVI — Stage 3 Corporate Intelligence / Acceptance (2026-10-14)

## HEAD and authority
- Source baseline: `2df0d2a45944fb4945f45c7305fe9bcd0c070c44` (Stage 2 approved source + CI evidence in PR #68; still unmerged). Owner: `api-delpi` external READ broker and governed-agent QA.
- Stage 3 scope here: executable, source-constrained E01–E14 acceptance cases and provider operator runbook. **NO cross-context Core consumer, new MCP tool, API adapter, OAuth, RBAC, SQL or agent-side business join**.
- Core authoritative solution catalog owner: `core-api`, `GET /solutions` & `GET /solutions/<plugin_id>`, authenticated; safe `accessible` flag reports current app access but does **not** grant it. This source is `TO_INVENTORY` for DAVI until an approved bearer-forwarded user-parity contract, output allowlist, scope/rate/privacy limits and owner ratification exist.
- Existing proof-of-pattern (NOT reused as runtime evidence for DAVI): TÉO `SolutionCatalogPort` + `CoreSolutionCatalogGateway`; VISTA `SolutionIntelligenceService` only on a TV route miss. Their permissions do not become DAVI permissions.
- `api-delpi` is the source for governed product/stock/production capabilities; Agent Knowledge is only conceptual guidance. Never elevate a route/action search miss to proof of enterprise-wide absence.

## Bounded source readiness matrix
- `EI01–EI07` existing governed API DELPI READ contracts: **CONTRACT_PROVEN_RUNTIME_PENDING**. The raw-material shortage projection `get_product_raw_material_set_shortages` is bounded to a specific product + required branch; it is not a plantwide ranking algorithm.
- `EI08` (MI): conceptual `measurement_units` topic; **GUIDANCE_PROVIDER_PENDING**, no operational API lookup.
- `EI09`: knowledge concept + canonical inventory summary; **MIXED_PROVIDER_PENDING**.
- `EI10`: global shortage risk/impacted OPs over next week: **TO_INVENTORY**. No proven authoritative cross-product candidate universe, time-window semantics, grain/completeness or consolidated owner use case; do not infer from a product-scoped route.
- `EI11`: stock + allocation join across sources **TO_INVENTORY**. Do not reconstruct domain business decisions in Agent.
- `EI12`: Core solution registry for DAVI **TO_INVENTORY**; Core active solution visibility != permission to read/use the app.
- `EI13–EI14`: stock mutation and generic SQL **UNSUPPORTED**.
- `EI01–EI14` fixture is **QA acceptance**: its operation IDs are approved pre-existing mappings for tests, NEVER a runtime allowlist or a replacement for discover→candidate_token→execute.

## Live MCP observation (different source from Git)
Date: 2026-10-14. User-connected DAVI MCP discovery (NOT Agent Studio Preview):
- `agent_directives.version = 2026.10.07.2`, **knowledge_orchestration absent** (current deployed plugin predates staged Stage 1).
- `Onde o produto 10080001 é utilizado?`: 0 candidates.
- `O que significa MI?`: 5 unrelated candidates, including system metadata; confirms conceptual misrouting.
- `Quais matérias-primas estão em maior risco de faltar na próxima semana e quais ordens de produção serão afetadas?`: 0 candidates.
- Eligible broker count: 89. No execute call, no cross-user business AuthZ test.
- Never present staged Git/CI fixes as live or assert provider retrieval. Re-test post authorized deployment.

## Release and E2E acceptance gates
1. Owner PR sequence #63 → #65 → #62 → #67, respecting HTTP consumer smoke/approval and each PR's review gate; do **not** merge integration-only PR #66/#68.
2. Agent Studio operator sync: pinned 15 frozen files + derived topic index + manifest (17), stable Instructions from canonical source, End-user account, app unchanged.
3. Run canonical Knowledge K01–K10 with fresh Preview; compare source provenance, no unrelated operation for concept, no operational facts from files.
4. Run enterprise E01–E14 with actual typed discovery/execute only when approved. Capture actor scope, tool invocation, status, completeness, output projection; redact tokens.
5. Mandatory E2E second DELPI user, own OAuth login, **negative business AuthZ** for an unauthorized canonical backend read; never simulate as proof.
6. Resolve MCP rate-limit owner decision, sharing permission and rollout policy separately. Deployment SHA, provider tool discovery, negative denial, and postcondition/business outcome are separate evidence ladders.

## Decision
- Source/CI acceptance of this test harness: **PENDING_CI** at creation.
- Cross-context Core integration: **IMPLEMENTATION_NOT_AUTHORIZED; TO_INVENTORY**.
- Real Agent Studio Knowledge and E2E acceptance: **TEST_NOT_RUN**.
- Wider go-live: **BLOCKED** pending provider sync, second-user AuthZ and rate owner decision.
