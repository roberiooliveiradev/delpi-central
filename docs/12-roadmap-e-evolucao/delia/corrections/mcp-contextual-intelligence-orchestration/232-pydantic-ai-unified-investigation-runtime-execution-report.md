# 232 — DÉLIA · Execução da migração Pydantic AI unified investigation (doc 231)

**TASK_ID:** `DELIA-C3-PYDANTIC-AI-UNIFIED-INVESTIGATION-RUNTIME-MIGRATION-01`  
**DATE:** 2026-11-04  
**STATUS:** EXECUTED — local validation; PRODUCTION_DEPLOY NOT_AUTHORIZED  
**PLAN:** [doc 231](231-pydantic-ai-unified-investigation-runtime-migration-and-legacy-removal-plan.md)  
**INVENTORY BASELINE:** [doc 230](230-langgraph-pydantic-ai-runtime-flow-inventory-and-consolidation-decision.md)

## Decision record

**ARCHITECTURE_DECISION:** LangGraph production sequencing is **retired**. The sole production investigation runtime is `PydanticAiInvestigationOrchestrator` (`DELIA_ORCHESTRATION_ENGINE=pydantic_ai`, default). Application `OperationalCapabilityOrchestrator` remains the governed gates owner and the explicit `delia` rollback sequencer.

Historic docs 192–196 remain historical evidence of Engine B; they are superseded for *runtime selection* by this decision and doc 231. Doc 230 recommendations KEEP→updated: LangGraph → **REMOVED**; Pydantic AI → **KEEP (expanded to Agent+tools)**; Application → **KEEP (gates)**.

## What changed

| Area | Change |
|---|---|
| Runtime | New `app/infrastructure/orchestration/pydantic_ai_investigation.py` |
| Composition | Default engine `pydantic_ai`; `langgraph` rejected; fan-out/checkpoint flags fail closed |
| Application gates | `_project_semantic_tool_catalog`, `_governed_semantic_tool_invoke` |
| Model transport | Wall-clock deadline on `PydanticAiModelInvocationAdapter.invoke` (trickle-safe) |
| Removed | `langgraph_engine.py`; langgraph/langchain pins; LG eval scripts; LG-only tests |
| Dependencies | `requirements.txt` keeps `pydantic-ai[openai]==2.50.0` only for AI stack |

## Agent tool surface

1. `list_read_capabilities` — live READ/DISCOVERY/ANALYSIS catalog (metadata only).  
2. `invoke_read_capability` — schema-validated invoke via Application (discovery-first preserved).  
3. `run_governed_investigation` — full owner path for compound/compare (Evidence/RC-A retained).

Write/PREPARE/ACT are **not** exposed as Agent tools. AuthZ/Evidence/confirmation remain Application + Core/Domain.

## Residuals (honest)

- RC-B / RC-C / REF05 functional E4-R6 outcomes remain OPEN (not claimed closed by this migration).  
- Live local E2E against real owners: **EXTERNAL_BLOCKER** — Docker daemon socket absent on the execution host (`/var/run/docker.sock` missing); Ollama/`127.0.0.1:11434` and local API ports unreachable. Classified `NOT_REACHED`, not fabricated PASS.  
- Optional LangGraph durable resume / Send fan-out are **not** ported; unset retired env vars.  
- Semantic-once consolidation (doc 226/229 Option B) is partially advanced (Agent tool choice) but per-sub `_propose` inside `run_governed_investigation` still exists when that tool is used.

## Rollback

1. Set `DELIA_ORCHESTRATION_ENGINE=delia` and rebuild `delia-api`.  
2. Or revert Git to pre-migration SHA and restore prior `requirements.txt` (includes LangGraph).  
No claim of rollback to LangGraph without restoring those packages.

---

## §8 — DÉLIA EXECUTION REPORT — PYDANTIC AI UNIFIED MIGRATION

```text
DÉLIA EXECUTION REPORT — PYDANTIC AI UNIFIED MIGRATION
TASK_ID: DELIA-C3-PYDANTIC-AI-UNIFIED-INVESTIGATION-RUNTIME-MIGRATION-01
BASE_HEAD: (pre-migration working tree on main; planning OBSERVED_HEAD bfa270939c)
FINAL_HEAD: (filled after commit/push)
ORIGIN_MAIN: (filled after push verify)
PUSH_VERIFIED: PENDING_AT_REPORT_DRAFT
GIT_STATUS: path-scoped delia-api + docs 231/232 + ledger + compose engine defaults; concurrent WIP (controllership-finance, tv-dashboard-presentation, engineering-api) preserved unstaged
AUTHORITIES_READ: docs 16/50/17/49/51/52/21/20/25 + 192–196, 220, 226, 228–231; delia-execution-protocol; platform-* material to orchestration/security/contracts
CP_RQ: C3 orchestration runtime migration; Evidence/AuthZ/Policy contracts preserved; no CP phase advance claimed
DECISION_RECORD: LangGraph retired; pydantic_ai default investigation; delia = gates + rollback sequencer
EXECUTION_DRIFT: none material vs doc 231 authorization; LIVE_E2E blocked by host Docker/LLM absence
EXISTING_EQUIVALENT: YES — SupportsGovernedStageGates / OCO catalog+invoke / ModelInvocationPort / Evidence
REUSE_DECISION: EXTEND (Pydantic AI Agent+tools) + REUSE (Application gates, Evidence, AuthZ)
PRODUCT_RUNTIME_BEFORE: DELIA_ORCHESTRATION_ENGINE=langgraph (StateGraph sequencer)
PRODUCT_RUNTIME_AFTER: DELIA_ORCHESTRATION_ENGINE=pydantic_ai (PydanticAiInvestigationOrchestrator)
PYDANTIC_AI_VERSION: pydantic-ai[openai]==2.50.0
AGENT_TOOLSET_INTERFACE: list_read_capabilities | invoke_read_capability | run_governed_investigation
EXISTING_PORTS_REUSED: SupportsGovernedCapabilityAttempt, SupportsGovernedStageGates, ModelInvocationPort, InvokeModel, VerifiedCompositeEvidence, GovernedCapabilityAttempt
REMOVED_LANGGRAPH_FILES:
  - delia-api/app/infrastructure/orchestration/langgraph_engine.py
  - delia-api/scripts/_s4_fanout_benchmark.py
  - delia-api/scripts/_s5_resume_probe.py
  - delia-api/scripts/engine_ab_eval.py
  - delia-api/scripts/engine_ab_real_model_eval.py
  - delia-api/tests/test_engine_b_architecture_isolation.py
  - delia-api/tests/test_integrated_investigation.py
  - delia-api/tests/test_subobjective_fanout.py
  - delia-api/tests/test_subobjective_resume.py
  - delia-api/tests/test_subobjective_evidence.py (S6 suite tightly coupled to LG fan-out/resume surface)
REMOVED_LANGGRAPH_DEPENDENCIES: langgraph, langgraph-checkpoint, langgraph-prebuilt, langgraph-sdk, langchain-*, langsmith (product + eval pins)
REMOVED_LEGACY_ORCHESTRATION: dual A/B LG selector; LG fan-out/checkpoint composition paths (flags fail-closed)
PRESERVED_APPLICATION_AUTHORITIES: OperationalCapabilityOrchestrator gates; Evidence/VerifiedCompositeEvidence; Core/Domain AuthZ; PREPARE/ACT confirmation; ModelInvocationPort; native_assessment fail-closed; recovery premise fingerprint
RETAINED_LEGACY_WITH_REASON:
  - OperationalCapabilityOrchestrator._attempt as DELIA_ORCHESTRATION_ENGINE=delia rollback
  - _propose stages inside run_governed_investigation (Evidence parity / compound goals)
  - pydantic_arggen path if still referenced by settings (not claimed removed)
CONTRACT_CHANGES: composition default engine; Settings.for_testing forces delia (no live LLM keys); env.example OpenAPI DELPI comment sanitized
LLM_CALLS_BEFORE_AFTER: NOT_MEASURED on live stack (EXTERNAL_BLOCKER); unit/TestModel paths green
TOKENS_BEFORE_AFTER: NOT_MEASURED (no live provider)
LATENCY_BEFORE_AFTER: NOT_MEASURED (no live provider)
TIME_TO_FIRST_OWNER_READ: NOT_MEASURED (no live owner)
MODEL_CONFIG: local intended qwen/openai-compatible via DELIA_LLM_*; not reachable this host
EVALUATED_SHA: (post-commit)
LOCAL_DEPLOY_SHA: N/A — PRODUCTION_DEPLOY NOT_AUTHORIZED; local Docker unavailable
LIVE_E2E_SCENARIOS: NOT_REACHED — docker.sock absent; no Ollama/API listeners
REAL_OWNER_READS: NOT_REACHED
DISCOVERY_FIRST_RESULT: covered by unit/contract (invoke_read_capability / gates); live NOT_REACHED
RC_A_SAFETY: PRESERVED in Application Evidence path (not re-proven live)
RC_B_OWNER_SELECTION: OPEN (pre-existing)
RC_C_CANDIDATE_PROTOCOL: OPEN (pre-existing)
REF05_TARGET_ORACLE: OPEN (pre-existing)
FALSE_GROUNDED_COUNT: NOT_MEASURED live
AUTHZ_SECURITY_EVALS: isolation AST + engine selection fail-closed + native_assessment status fail-closed restored/adapted PASS
GENERALIZATION_EVALS: recovery reuse/hardening + governed attempt contract PASS under pydantic_ai + delia
FULL_BACKEND_REGRESSION: delia-api pytest tests/ GREEN (timeout=60); ceiling trickle + OpenAI ChatCompletion fixture fixed
CONSUMER_INTEGRATION_TESTS: composer isolation (no top-level pydantic_ai/langgraph); requirements pin scan PASS
BOOT_WITHOUT_LANGGRAPH: composition rejects langgraph*; requirements pins absent
NDJSON_TERMINAL: unchanged contract; not re-probed live
DOCUMENTS_UPDATED: 231 STATUS→EXECUTED; 232 report; execution-ledger entry
LEDGER_UPDATED: YES
RESIDUAL_SEARCH: no product import of langgraph_engine / from langgraph; commentary-only mentions remain in historical docs/tests narratives
UNRESOLVED:
  - LIVE_E2E EXTERNAL_BLOCKER (Docker daemon / local LLM stack down)
  - RC-B / RC-C / REF05 remain OPEN
  - semantic-once residual inside run_governed_investigation
ROLLBACK_SHA_AND_PROCEDURE: revert migration commit(s) OR set DELIA_ORCHESTRATION_ENGINE=delia (+ restore langgraph pins only if LG required again)
VERDICT: ACCEPT_WITH_RESIDUAL — migration + LG removal + regression PASS; live owner E2E NOT_REACHED
FUNCTIONAL_ACCEPTANCE_CANDIDATE: NO (live real-owner matrix missing)
PRODUCTION_DEPLOY: NOT_AUTHORIZED
```
