# 255 — DÉLIA: Application Specialist Interop + Structured Understanding — auditoria integral

**TASK_ID:** DELIA-C3-APP-SPECIALIST-INTEROP-AND-STRUCTURED-UNDERSTANDING-INVENTORY-01  
**AUDITED_HEAD:** `5ad90d19e205e08597feb047b0cab89abe6b90db`  
**DATE:** 2026-11-05  
**MODE:** GitHub API full source inventory; no runtime edits, no tests  
**STATUS:** AUDIT PROVEN for source / TO_INVENTORY for authority and all dynamic consumers / TEST_NOT_RUN  
**SCOPE:** `delia-api/app/application/specialist_interop/` (5/5 files) + `delia-api/app/application/structured_understanding/` (4/4 files).  
**RELATED:** audits 245, 246, 248, 249, 252, 253; snapshot experiment doc216, C3-T4/R1 and canonical phase ledger.

## 1. Executive decision

Unlike retired direct DELPI OpenAPI, `specialist_interop` is wired into `root_composer.py` and provides a real active provider-neutral MCP boundary. **Do not remove whole folder.** `structured_understanding` is intentionally absent from `root_composer`; its architecture test explicitly checks that it is **not wired**. This bounded, historical C3-T4 observation extraction is a candidate to retire only if the authorities/ledger do not require it as separate, test-only, planned capability. Do not infer absence from empty search; prove all consumers before deletion.

**EXISTING_EQUIVALENT:** YES for live specialist interop + MCP adapter, Pydantic AI native structured outputs and existing domain evidence/epistemic guards. TO_INVENTORY for intended future Structured Understanding consumer and frozen C3-T4 decision.  
**REUSE_DECISION:** REUSE/SHRINK specialist interop, retire snapshot experiment only if formally approved, prefer DELETE unwired Structured Understanding slice if canonical intent superseded rather than rewrite/move its unused functionality; otherwise retain as bounded eval-only contract. NEW=NO.

Do not implement until locally reanchored HEAD/status/Project Instructions/.cursor/16→50→17→49→51→52→21→20→25/architecture/product/thematic spec/ledger; verify phase and CP/RQ. GitHub code is not a substitute for canonical authority.

## 2. Matrices

### 2.1 specialist_interop — 5/5

| File | Extracted lines | Proven responsibility/consumer | Decision |
|---|---:|---|---|
| `specialist_interop.py` | 382 | `SpecialistInterop.discover_catalog/invoke` via `SpecialistInteropPort`; `root_composer.py`, orchestrated MCP; live list/call, bounds, outcomes | KEEP/SHRINK |
| `snapshot_interop.py` | 110 | `SnapshotDiscoverInterop`, conditional `root_composer.py` snapshot_experiment, snapshot store | EXPERIMENT RETIREMENT DECISION REQUIRED |
| `contracts.py` | 102 | `SpecialistCatalogRequest`, `SpecialistInvocationRequest`, `RemoteToolDescriptor`, `RemoteToolOutcome`, `SpecialistCatalogResult`; MCP adapter and Port | KEEP |
| `errors.py` | 46 | typed specialist/transport/owner errors | KEEP |
| `__init__.py` | 2 | package marker | KEEP |
| TOTAL | 642 | | |

### 2.2 structured_understanding — 4/4

| File | Extracted lines | Proven responsibility/consumer | Decision |
|---|---:|---|---|
| `understand_structured_input.py` | 133 | `UnderstandStructuredInput.execute`, bounded one-SourceRef observational extraction via `InvokeModel`; foundation & architecture tests | CANDIDATE DELETE if C3-T4 retired, otherwise KEEP test-only |
| `contracts.py` | 80 | `StructuredUnderstandingRequest/Result`, non-FACT/non-ACT contract | SAME, coordinated |
| `errors.py` | 18 | bounded typed errors | SAME |
| `__init__.py` | 30 | exports public slice | SAME |
| TOTAL | 261 | | |

**Combined source:** 903 lines counted from GitHub extraction; runner must measure wc -l on local HEAD for final baseline.

## 3. Findings — specialist_interop

- `specialist_interop.py` implements real discovery, `operation_class_from_owner`, `invocable_in_interactive_phase`, read-revalidation with `list_remote_tools`, bounded argument JSON size (4000 chars) and total timeout cap (30s), owner error code mapping and typed outcome projection. `toolClass` is owner-declared but **NOT Core/domain permission**; keep upstream write PREPARE/ACT, live Core/Domain authority and idempotency. `RemoteToolOutcome` remains untrusted observation. Not a second LLM planner.
- Owner error handling includes `_owner_error_hint` and special recoverability only when typed ARGUMENT_VALIDATION + recoverable=true; investigate overlap with MCP adapter and duplicate HTTP error normalization, but do not relax fail-closed or leak sensitive details. `_validate_arguments` JSON bounded serialization via `default=str` merits type-bound validation parity review; `str` fallback may hide non-JSON argument types (TO_VERIFY in tests).
- `_policy_invocable` receives specialist_id and remote_name but delegates only operation_class policy. Confirm policy/owner binding is performed at higher gate before invocation; no capability grant from discovery. _Do not_ rewrite to allow name-based permissions from untrusted metadata.
- Snapshot-specific hook `_remote_tools` exists to support `SnapshotDiscoverInterop`; if experiment is retired, consider simplifying hook without changing live `invoke` revalidation.
- **PROVEN CLEAN ARCHITECTURE VIOLATION:** `application/specialist_interop/snapshot_interop.py` imports `app.infrastructure.interoperability.mcp.catalog_store.McpCatalogStore` and `contract_hash`. Application depends on Infrastructure implementation, contra layering. Do not create speculative new port: first verify whether snapshot experiment is authorized. If retired, delete snapshot slice atomically across root wiring, Infrastructure store, script, configuration and experiment tests (related doc248). If retained, architectural decision needed to move responsibility into legitimate Infrastructure or replace dependency with existing approved contract, preserving no fallback and live invoke checks.
- `contracts.py` minimal context delegation correctly omits conversation history, credentials, raw instructions and other specialists' context. Port is `application/ports/specialist_interop_port.py`. **KEEP, provider-neutral**, no SDK import into Application.
- `errors.py` is small and live; preserving errors is important for owner denied, invalid call, timeout and result truth.

## 4. Findings — structured_understanding

- `tests/test_structured_understanding_architecture.py` **explicitly defines** `test_composition_root_does_not_wire_structured_understanding` at ~line118; `root_composer.py` inspected and has no class reference. Thus this use case is not part of the composed interactive runtime at this SHA; **not equivalent to proving no consumers everywhere**. Tests `test_structured_understanding_foundation.py` ~254 lines use `DeterministicTestAdapter` only, and explicitly state this does not prove real-model quality.
- `UnderstandStructuredInput.execute` uses `InvokeModel(ModelInvocationRequest(expected_fields=("observations",)))`, then calls `domain.structured_understanding.rules.build_content_from_structured_output`; this is earlier generic schema/gate approach. It is a candidate for deletion rather than migration if C3-T4 is superseded by the already-planned native Pydantic AI output and no approved bounded consumer requires the capability. Do **not** call it a parallel runtime: same `InvokeModel` boundary, not another LLM framework.
- Request enforces exactly one SourceRef, max16,384 chars, <=30s, fixed schema id/version, observation-only epistemic classification, sensitive/CoT/tool-call guards and lineage. Result `is_fact/is_world_fact/authorizes_act/has_eval_result` always false. If retired, ensure the **same invariants** remain in Domain Evidence/Model Invocation and relevant tests, not silently discarded.
- Related domain files `domain/structured_understanding/model.py` and `domain/structured_understanding/rules.py` remain outside the requested folders, but are likely cleanup candidates **only if no legitimate consumer remains**. Do not leave unused domain slice and tests after deleting only Application folder. Check exports, API/routes, scripts, evals, docs and dynamic imports.
- If canonical doc actually requires this independent educational/foundation slice even without production wiring, KEEP and label explicitly TEST_ONLY/NOT WIRED; avoid making independent Pydantic agent just for the slice.

## 5. Concrete consumer evidence

**PROVEN:**
- `root_composer.py` imports `SpecialistInterop` and conditionally `SnapshotDiscoverInterop` + `McpCatalogStore`; it creates real `SpecialistInterop(adapter)` for live mode.
- `test_specialist_interop_usecase.py` (~691 lines), architecture/security/domain test files exercise interop.
- `snapshot_interop.py` directly imports Infrastructure class/function. 
- `test_structured_understanding_architecture.py` explicitly tests absence from root; `test_structured_understanding_foundation.py` uses deterministic TEST_ONLY adapter, not real model.
- Recursive Git tree complete (`truncated=false`) lists all target files and related Domain/Infrastructure tests and scripts.

**TO_INVENTORY:** full symbol consumers across non-obvious files/scripts and dynamic imports via local rg+AST, authorities C3-T4 and snapshot decision, actual test outcomes/evaluated runtime/model, possible replacement output schema, safe error taxonomy and owner-bound authorization coverage.

**TEST_NOT_RUN:** no checkout, imports/build, test/eval or production deployment.

## 6. Execution steps and gates

1. Local reanchor and confirm canons, phase/CP-RQ, C3-T4 and snapshot frozen decisions and all source SHA.
2. Full symbol consumers via ripgrep/AST; include `StructuredUnderstandingRequest/Result`, `UnderstandStructuredInput`, `StructuredObservation`, `build_content_from_structured_output`, `SnapshotDiscoverInterop`, `McpCatalogStore` and dynamic imports.
3. **Priority A:** resolve Application→Infrastructure import in snapshot: retire whole snapshot experiment if no longer approved; if retained require coordinator decision on boundary correction, no speculative abstract port.
4. **Priority B:** choose explicit KEEP_EVAL_ONLY or RETIRE_STANDALONE_SLICE for Structured Understanding by reading authoritative C3-T4 documents. If RETIRE, delete the 4 Application files, related Domain slice and test-only fixtures when no other consumers, preserve generic Evidence safety tests elsewhere, and fix exports/imports. If KEEP, do not prematurely migrate to another framework nor wire into production.
5. **Priority C:** shrink `specialist_interop.py` only where duplication is proved; maintain live tool-class verification, total budgets, minimal delegation, denied/unknown tool behavior, lineage, timeout and partial outcomes.
6. RED/GREEN and regressions: specialist discovery/read/analysis/prep/act gates, live reclassification/revocation, untrusted metadata injection, owner-typed errors, missing vs partial, 4000-character and timeout bounds, snapshot fail closed if kept; structured observation no FACT, single SourceRef, no COT/secrets, malformed output, no ACT; entire backend and native Agent E01–E10 rebuilt SHA/config as applicable.
7. Residual search, LOC before/after, docs 245/246/248/249/252–255 and execution ledger only after factual implementation results, report with exact test evidence and SHA, no production deployment.

## 7. Review

- `specialist_interop`: **KEEP/SHRINK**, active. `snapshot_interop.py`: **ARCHITECTURE_DECISION_REQUIRED** if experiment remains active; otherwise retire coherently.
- `structured_understanding`: **CANDIDATE RETIRE** based on explicit unwired architecture and TEST_ONLY coverage, but **authority/consumer inventory required** before physical deletion.
- **IMPLEMENTATION:** NOT RUN.
- **TESTS:** TEST_NOT_RUN.
- **PRODUCTION DEPLOY:** NOT_AUTHORIZED.
