# DAVI knowledge/documentation recovery — bounded execution evidence

TASK_ID: `DAVI-KNOWLEDGE-INTELLIGENCE-DOCUMENTATION-RECOVERY-AND-PRODUCTION-DEPLOY-01`

## Reanchor and authorities

Base: `ae2e82a4fbf2f7f1c44a8426d4ddec0d73c43143` (origin/main after fetch and fast-forward). The main workspace contained unrelated changes on another branch; execution uses the existing `davi-freeze-wt` worktree and preserves its unrelated untracked script. No DÉLIA implementation is changed.

Authorities: AGENTS.md; centralized-rules-first; evidence-driven-execution; platform architecture, API contracts, security, quality; test-and-commit; local-first-deploy; infra-sequential-container-startup; DAVI integration architecture; freeze, manifest, topic registry and orchestration evidence; DÉLIA coordination document 143.

## Findings, competing hypotheses and reuse decision

EXISTING_EQUIVALENT=YES for corpus/manifest/topic index/builder and bounded agent guidance. REUSE_DECISION=EXTEND existing guidance; REUSE existing builder. No replacement retrieval system is introduced.

1. Corrupt or missing Git corpus: not reproduced. `verify` passes for all 15 documents and 15 topics; deterministic `build` produces the expected 17 files. One deferred vendor source remains excluded.
2. Missing runtime projection: not reproduced. Read-only introspection in the production container returns the governed_knowledge directives.
3. Provider publication/retrieval: TEST_NOT_RUN. Architecture explicitly describes manual Files synchronization; this session has no provider/MCP integration configured (`mcp_list_servers` returns an empty list). No claim about actual provider-side files is possible from this evidence.
4. External MCP document access: NOT_EXPOSED by the selected architecture. Runtime server introspection reports exactly discover_delpi_information and execute_delpi_information, and zero resources. Existing document transport spike is isolated/default-off and is not a production governed-corpus reader. It is not enabled or repurposed.
5. Product search failure: source-confirmed broad prefix matching, not evidence of failed Knowledge loading.

Primary architectural cause of the MCP consumer gap: the approved Files retrieval surface belongs to the Workspace Agent, not to external MCP consumers. No approved document-read contract is wired into the two operational tools. Deployment of the backend cannot synchronize Files or confer that missing consumer contract.

First unverified stage in the Files chain: provider sync. Its operational cause remains INCONCLUSIVE without provider access. Do not describe TEST_NOT_RUN as proof that Files are absent.

## Stage inventory

- Source documents: owner api-delpi/domain authors; pinned Git source, PROVEN/PASS for V1. Normative MP/PI authority ratification remains separate.
- Corpus: owner api-delpi content governance; freeze membership of 15, PROVEN/PASS; no membership mutation.
- Manifest/index: version 1, freeze `d9926cc14a8a4edd1b52775b82cf7353aede75b4`, source `86942f854041be1a516456ec2d6c87fc9d16c250`, manifest SHA-256 `b830a6a979a27bdbf1845d4e7128cc00aaa2fe75d2b095cbdb4af56b79449f49`; PROVEN/PASS via verify.
- Builder: existing provider-neutral, no network; verify/build PASS. Local output is ignored, not a published provider artifact.
- Publish/sync: owner Agent Studio operator; existing manual runbook; TEST_NOT_RUN here.
- Native retrieval: owner provider/agent operator; K01–K10 TEST_NOT_RUN, not replaced by unit tests.
- Intelligence: existing DaviAgentIntelligenceService projection shared by catalog and discovery; bounded, no document body, no authority grant.
- MCP consumer: two tools, zero document resources observed in running container; NOT_EXPOSED. Architecture decision required for a new document-consumption boundary; none is silently created.

## MP/PI source inventory and governance gate

Repository: roberiooliveiradev/delpi-central.

MP source: `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Normas_Tecnicas_DELPI.md`; source introduction commit `63cc77bfe60e157623dd77fd7fd335e37735a4e7`; current blob `aa8ec68879ae73ce83155f291e697e2f88416ebd`.

PI source: `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Understanding DELPI Intermediate Product Codes.md`; same introduction commit; current blob `203a603e1539d386a208560f616c2e961b8e3c26`. It describes itself as a summary of an original engineering PDF; provenance does not by itself ratify current business validity.

Related consumers/projections: global normas-tecnicas-delpi.md, engenharia-codigos-intermediarios-delpi.md, Chat technical-description policies/vocabulary, and existing api-delpi/docs/knowledge/product-vocabulary/normative-product-terms.md. Prompt policies are runtime instructions, not material to migrate.

The API DELPI already contains a controlled READ interpretation extract introduced by `4f49975c98`, with BUSINESS_OWNER=TO_INVENTORY. It is not the full MP standard and is not in frozen V1. cadastro-produto.md describes SB1 semantics, not the full nomenclature standard.

Comparison correction: the global MP projection differs from the source only by its five-line origin header and final newline at the inspected base. No normative content conflict was found in that pair. The old extract's vague divergence warning is corrected; owner ratification is not inferred.

TRANSFER_STATUS=BLOCKED_BY_OWNER_RATIFICATION; GOVERNANCE_STATUS=NOT_PUBLISHED. Complete norms are located, not fabricated. No Chat runtime, prompt, service, table or migration is imported. Do not add them silently to V1 or treat old document authorship as a current approval. Required next decision: content owner validates currency, original PI source/provenance and intended audience, then approves a separately versioned corpus revision using the existing builder/governance process.

## Search_products diagnosis

Owner: ProductRepository.search_products; adapter: external_capabilities.product_search_service; canonical SearchProductsUseCase, existing backend AuthZ and minimized projection.

SQL behavior confirmed in source:

- split description on whitespace, preserving punctuation;
- each term matches B1_DESC with case/accent-insensitive prefix LIKE term%;
- terms are combined by OR, not AND/substring token matching;
- exact full-description prefix adds 100 relevance points; individual term prefixes add 20;
- default ordering is relevance DESC, description, code; explicit sort overrides this;
- count uses the same predicate; results are paginated.

Therefore TERMINAL BALA can select descriptions beginning BALA (including BALANCA), and TERM. BALA can select all descriptions beginning TERM. This explains broad totals and mixed matches without hardcoding a lexical exception. No search behavior is changed here: narrowing OR to AND would be a separate behavioral contract change affecting existing consumers, not a fix for Files publication. Returned totals are not counts of semantically verified terminal-bala products. The sample product codes in the task are not embedded in runtime or claimed as freshly read data.

## Minimal implementation and RED/GREEN

Additive guidance metadata distinguishes corpus_status=PROVEN, retrieval_surface=WORKSPACE_AGENT_FILES, mcp_document_access=NOT_EXPOSED and consumer_contract_status=ARCHITECTURE_DECISION_REQUIRED, preserving legacy status and provider_status. The existing KNOWLEDGE_GATE now requires retrieval in the consumer's own surface and rejects interpreting agent_directives as retrieved content/AuthZ. No endpoint/tool, allowlist permission, business data or document body is added.

RED: test_knowledge_availability_is_explicit_for_external_mcp_consumers fails with KeyError corpus_status, while 11 existing orchestration tests pass.

GREEN: 85 focused tests pass, covering orchestration, corpus/bundle, topic index, intelligence, offline broker, two-tool invariant and MCP auth. This is offline evidence using a local dependency image, network disabled, read-only repo mounts; fake broker reads are not business evidence.

Full suite in corrected local environment: 6013 PASS, 30 SKIP, 2 FAIL. Both failures reproduce on a clean detached worktree at the base SHA: test_restore_plan_revision_applies_snapshot_and_records_restore and test_product_sales_open_orders_returns_meta require PLUGINS_DB_HOST/backend DB access despite their test doubles. Classification: PREEXISTENTE_CONFIRMADA / environment-dependent, not caused by this diff. No DAVI/MCP test failed in the corrected full run. Initial 23 failures included missing git and read-only storage; installing git only in an ephemeral local validation image and using tmpfs fixed 21 environment failures without test/production changes. The initial broader DAVI selection had 1395 PASS and 3 missing-git failures; those three passed on rerun.

Architecture Phase 3 and platform guardrails: zero findings; their 34 self-tests pass. OpenAPI and FastAPI AuthZ auditors: zero findings. git diff --check: PASS. All production authenticated/provider outcomes remain separate from these offline results.

Concurrent origin/main fast-forward to 8ecce3f836d9963fa7485089200afdf8edd32f43 changed no api-delpi/shared/infra sources; unrelated work is preserved. Release scope is the additive availability signal only, not a claim of documentary recovery.

## Production baseline and release gate

SSH operator: operador@192.168.1.237; hostname srv-api. Repository ~/projetos/delpi-central is clean at `664eec398cd5a75819dc36da2061bedda0a49e15` at inspection.

Running delpi-api-delpi image ID: `sha256:290587973779f5c6388736851b880a2ec31f1769d03c4cf020716c6f451b0b02`; started `2026-10-24T01:36:19.35938205Z`, healthy. Host/runtime clock differs from session date; retain exact observed timestamp, do not invent a common timeline. Image ID is not a registry RepoDigest or proof of full baked Git SHA.

Runtime content SHA-256: davi_agent_intelligence.json `e5523b23c95ea997754806e70016bd58674ef64cdd5f183115e9355ae07ff6a2`; service `692ccbbb554d711e48af9a9c1845ca695ce8250b5456cb30a2e4487ab6019a1d`.

Deployment authorization exists in this task, but promotion remains conditioned on gates. Canonical release: pushed exact SHA, clean server Git, git pull --ff-only, infra/scripts/up-prod-sequential.sh --build api-delpi. No rsync/scp, container patching, migrations or other service rebuilds. Retain the previous image and verify rollback readiness before promotion. Provider publication is separate and remains blocked on official access; no admin credentials/impersonation are used.

## Outstanding acceptance

- Provider Files visibility, manifest identity and K01–K10 require official operator access; no tokens should be sent in chat.
- Authenticated production discover/execute and TERM. BALA comparison require sanctioned end-user session; second-user live denial remains TEST_NOT_RUN.
- MP/PI publication needs current content-owner ratification and versioned membership decision.
- External MCP documentary content requires an explicit architecture decision; Files do not satisfy that boundary.
- Full business outcome is NOT_PROVEN even if metadata deployment succeeds. Coordination review required; no DÉLIA R4–R7 work is undertaken.
