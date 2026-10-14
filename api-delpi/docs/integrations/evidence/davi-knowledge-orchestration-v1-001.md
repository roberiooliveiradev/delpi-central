# DAVI-KNOWLEDGE-ORCHESTRATION-V1-001 — P0 Implementation Evidence

> Baseline: `8dc1fcc57a792788b3e7cfb5dd7023733b29d891` (2026-10-13). Source changes on `feat/davi-knowledge-orchestration-v1-001`.
> Local git fetch/status/pytest: **TEST_NOT_RUN** — container DNS could not resolve github.com; GitHub connector used to read HEAD, sources, create branch/commit.
> GitHub Actions / deployed Agent Studio: **PENDING_VERIFICATION** at commit creation.

## Owner and authority

- Owner: `api-delpi` existing semantic external-capability presentation. Canonical domain read use cases stay source of truth; final business AuthZ stays in the backend.
- Consumers: MCP discover and legacy GPT catalog expose the SAME `DaviAgentIntelligenceService.agent_directives`.
- No new MCP tools, APIs, identity, RBAC, writes, SQL or newly eligible operations.
- Source-Git 15-doc Knowledge is NOT proof of native Agent Studio retrieval. Core solutions remain `TO_INVENTORY`.
- New `knowledge_orchestration` is declarative routing, not a database-backed knowledge engine nor authority.

## Changes

1. `davi_agent_intelligence.json`: map of owners/source statuses, intent routes, gates, precedence, sufficient context, provenance labels and stop conditions.
2. `davi_agent_intelligence_service.py`: explicit governed projection. Same consumer producer.
3. `davi_external_read_allowlist.json`: limited to where-used semantic aliases and negative reverse-BOM phrases on direct-structure action. All 89 operations and outputs remain unchanged.
4. `test_davi_knowledge_orchestration.py` plus existing CI test selection: routing, status honesty, directive parity/budget, paraphrases and negative write/SQL.

## Historical decision discrepancy — DO NOT CHANGE DOMAIN CLASSIFIER

Nested historical `coverageDecision.previousDecision.reason` in allowlist v21 reverses `RE0`/`DE0` classification — **STALE_EVIDENCE**. Canonical owner logic for `D3_DOC='INVENT'`: `DE0/TM499=surplus`; `RE0/TM999=shortage`. The historical record is intentionally not rewritten; agent routes must trust backend-adjustment summary/nature and not recompute TM/CF.

## Acceptance

- No schema/allowlist/tool/permission expansion: **SOURCE_REVIEW_REQUIRED**.
- Python pytest/local full regression: **TEST_NOT_RUN** without local repository.
- GitHub Actions api-delpi console targeted DAVI tests: **PENDING** until checked.
- Deployed MCP / Agent Studio / K01-K10 / negative second-user AuthZ: **PENDING**, not claims for this P0.
- P1: verify/build frozen native Knowledge bundle and obtain provider sync and K01-K10 evidence. No unapproved RAG or new MCP tool.
