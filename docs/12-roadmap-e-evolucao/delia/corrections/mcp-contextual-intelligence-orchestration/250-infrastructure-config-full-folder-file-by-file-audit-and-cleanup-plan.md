# 250 — DÉLIA · Auditoria arquivo por arquivo de infrastructure/config

**TASK_ID:** DELIA-C3-INFRASTRUCTURE-CONFIG-FILE-BY-FILE-NATIVE-CLEANUP-AUDIT-01  
**DATE:** 2026-11-05  
**AUDITED HEAD:** `bbfd027ccf832d61faf575c236aa41e2605fe023`  
**STATUS:** AUDIT/PLANNED — no implementation/test executed  
**SCOPE:** `delia-api/app/infrastructure/config/` — all 4/4 files read at same SHA  
**RELATED:** docs 239, 243, 245, 246, 248, 249; canonical authority/ledger and CRI frozen decisions  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## 1. Summary

The folder contains four files: `__init__.py` (4 lines), `cri_instruction_resource.py` (511 lines), `pydantic_ai_runtime_config.py` (643 lines), `settings.py` (396 lines); **1,554 source lines** (GitHub extracted line counting). Unlike the retired OpenAPI package, this folder is **actively used by root_composer and other application/infrastructure consumers**. Deleting it outright would break model configuration, delegated MCP, authorization context and instruction resources.

The most meaningful cleanup is to remove obsolete CRI semantic activation and duplicate model-stage configuration only **after** native structured output implementation docs245/246, and to decouple the JSON schema loader from orchestration engine constants. Existing JSON centralization doc243 has been implemented in code; do not generate another JSON or second settings system.

**EXISTING_EQUIVALENT:** YES for single Pydantic AI runtime JSON, existing settings/process configuration, validated resources, native Pydantic validation tools; TO_INVENTORY for shared resource loader and typed schema reuse, external owners of Core/MCP/STT config.  
**REUSE_DECISION:** KEEP/SHRINK settings + runtime config loader; SHRINK/SPLIT BY REAL CONSUMER, potentially DELETE CRI-only loader functions if removed from runtime after docs245/246; KEEP __init__. No new config framework.

Before changes fully reanchor local HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → architecture/product/spec → ledger → docs239–250. This API-only audit cannot verify local git status or runtime, full transitive consumers, canonical frozen decisions or tests; do not claim them PROVEN.

## 2. Matrix 4/4

| File | Lines | Responsibilities | Proven consumers | Decision |
|---|---:|---|---|---|
| `__init__.py` | 4 | exports `Settings` | package-level import surface | KEEP |
| `cri_instruction_resource.py` | 511 | JSON validation/loader for `CriInstructionClause`, `CriPresentationVocabulary`, `OrchestrationInstructions`; resource hash, version, labels | `root_composer.py` imports all 3 loader functions at ~31–34; calls at ~421/~439/~463 | **PRIORITY SHRINK**; retire CRI clause loader if native output removes CRI, keep required instruction and trusted label loading unless existing equivalent proven |
| `pydantic_ai_runtime_config.py` | 643 | validates `pydantic_ai.runtime.delpi.json` profiles/types/ranges/secret blacklist, fingerprint, cross-field budgets, typed immutable dataclasses | `settings.py` imports `PydanticAiRuntimeConfig`, `load_pydantic_ai_runtime_config`; tested `test_pydantic_ai_runtime_config.py` | **KEEP/SHRINK + DECOUPLE**; schema is legitimate, but imports Application orchestration/retry constants |
| `settings.py` | 396 | app env/config wiring, Core, Keycloak exchange, MCP, Pydantic JSON, CRI feature flag, legacy env rejection, snapshot experiment, STT/dictation | `root_composer.py` creates Settings; interoperability `config.py`; many tests | **KEEP/SHRINK** by retiring obsolete controls; retain real secret/transport/live service settings |

## 3. File-level observations and cleanup

### 3.1 cri_instruction_resource.py (~511 LOC)

**Actual code:** `CriInstructionResourceError`, dataclasses `CriInstructionClause`, `CriPresentationVocabulary`, `OrchestrationInstructions`, loader functions `load_cri_instruction_clause`, `load_cri_presentation_vocabulary`, `load_orchestration_instructions`, and helpers `_load_resource_object`, `_validate_identity`, `_vocabulary_entries`, `_field_label_entries`. Three separate governed resources, all called by root composer; do not mark file orphan.

**TARGET:** remove CRI-specific answer-requirements/synthesis instructions if doc245 Pydantic structured output fully supersedes them and no canonical consumer remains. `load_cri_instruction_clause` and `DELIA_RESPONSE_INTELLIGENCE_ENABLED` may then become dead. The presentation vocabulary `field_labels` **loads unconditionally** even when CRI is off (~line 421 of root composer): it is used for baseline field naming. It must be preserved, replaced by a proven safe renderer equivalent, or intentionally retired by an authority review. `load_orchestration_instructions` remains live and validates a complete required set; do not delete without auditing `ORCHESTRATION_INSTRUCTION_KEYS` and remaining legitimate native agent/admission instructions.

Candidate cleanup: remove obsolete version allowlists and dead instruction sections **only with updated resource migration**. Validate fail closed, version, size, unknown keys and hash; avoid silently converting bad resource to valid. Avoid moving all 511 lines to a renamed module.

### 3.2 pydantic_ai_runtime_config.py (~643 LOC)

**Actual code:** immutable typed `ModelConfig`, `GenerationConfig`, `AgentConfig`, `ContextConfig`, `BudgetsConfig`, `ToolResultsConfig`, `ObservabilityConfig`, `RuntimeProfile`, `PydanticAiRuntimeConfig`; `load_pydantic_ai_runtime_config` with schema version, keys, types, limits, secret blacklist, profile/selection/fingerprint validation.

**PROVEN COUPLING ISSUE:** imports `MAX_GOVERNED_ATTEMPTS` from `app.application.capability_provision.orchestration` and `LLM_CALL_MAX_ATTEMPTS` from `app.application.model_invocation.governed_retries`, using them as max values in Infrastructure JSON validation. Loading config therefore imports a large orchestration module and couples configuration validation to application implementation constants; potential import/load-cycle risk to verify, not a proven crash. **TARGET:** place safety ceilings in their legitimate owner contract / policy boundary and avoid config loader importing the concrete orchestrator. Preserve immutable safety caps and fail-closed behavior: never use user JSON to override security ceilings. This is not license to create an extra registry/config service. Proven duplication of allowed constants should be eliminated by shared contract or canonical owner, not another hardcoded duplicate.

**Candidate cleanup:** repetitive `_section`, `_int_field`, `_optional_int_field`, `_seconds_field`, `_bool_field`, `_profile` can be reduced via installed Pydantic v2 validation **if** real tests prove exact schema/key/range/error/fingerprint parity; no necessity to rewrite 643 lines for aesthetics. Do not remove checked-in `delia-api/config/pydantic_ai.runtime.delpi.json` or merge Core/MCP/STT secrets into it. Only non-secret intelligence tunables there.

### 3.3 settings.py (~396 LOC)

**PROVEN active:** loads single Pydantic runtime config file from fixed path (lines ~19–23), rejects retired `DELIA_LLM_*` env values, rejects `DELIA_MODEL_RUNTIME=legacy`, configures local egress policy, sets Pydantic runtime and limits, also Core API/Keycloak/MCP/timeouts, flags, snapshot experiment and distinct STT settings.

**Candidates for removal based on existing approved work:**
- `DELIA_RESPONSE_INTELLIGENCE_ENABLED`, `response_intelligence_config_source`, `response_intelligence_config_invalid`: dependent on old CRI composition; verify frozen doc245/246 and renderer consumers, then delete together with CRI-only loader. Do not preserve a fallback mode that reinstates legacy semantic engine.
- `DELIA_ORCHESTRATION_ENGINE`, `orchestration_engine`: selector with only Pydantic AI allowed; remove runtime branch/selector only if fail-closed compatibility is retained or explicitly deprecated in deployment config and tested.
- `DELIA_SUBOBJECTIVE_FANOUT` and `DELIA_CHECKPOINT_DB`: retired LangGraph controls currently retained for fail-closed stale-env rejection. Could replace with one deprecation guard/no runtime feature, then delete once deployment migration proven, not silently ignore an unsafe stale setting.
- `DELIA_MCP_CATALOG_MODE` / `DELIA_MCP_CATALOG_DB`: connected to live optional snapshot experiment in root composer (doc248); remove only on approved retirement of SNAPSHOT_EXPERIMENT, along with catalog store, scripts, tests.
- Hardcoded per-owner endpoint flags `DELIA_MCP_{DAVI,TEO,VISTA,CAIO,CLARA,SURI,EVA}_*`: legitimate interop settings; consider reuse canonical approved specialist identity via config generation, not an additional duplicated allowlist. Do not infer owner from untrusted metadata.
- `DELIA_STT_*`: separate voice/dictation bounded context; maintain nonsecret config/secret separation; investigate duplicated defaults with dictation port, not Pydantic AI JSON.
- `_RETIRED_LLM_ENV_VARS` validates against stale settings: not legacy runtime, but transition guard. Remove only after verifying all deployment envs have migrated and preservation of fail-closed unknown selections.
- `is_local_llm_host` and `llm_egress_blocked_reason` are necessary egress policy guards; do not remove without equivalent.

**Risk/TO_VERIFY:** settings currently reads `os.getenv` for many tunables and uses `int()/float()` without uniform typed/range constraints. Validate malformed/out-of-range MCP/Keycloak/STT settings and fail-closed startup, preserving legitimate optional/safe defaults. Centralize only concerns with actual owner; do not create second Pydantic runtime profile source of truth. `Settings.for_testing` creates Settings first and changes environment afterwards; verify external LLM egress is never unintentionally enabled through test-specific mutation (and explicit injection policy applies). No secrets in logs/repr.

### 3.4 __init__.py (~4 LOC)

Re-exports `Settings`. KEEP, no useful deletion.

## 4. Consumer graph and implementation boundaries

```text
root_composer
 ├─ Settings
 │   ├─ pydantic_ai_runtime_config.py
 │   │   ├─ config/pydantic_ai.runtime.delpi.json
 │   │   ├─ orchestration.MAX_GOVERNED_ATTEMPTS  <-- candidate coupling
 │   │   └─ governed_retries.LLM_CALL_MAX_ATTEMPTS
 │   └─ Core, Keycloak, MCP, STT secrets/endpoint runtime env
 ├─ cri_instruction_resource.load_cri_presentation_vocabulary [always]
 ├─ cri_instruction_resource.load_cri_instruction_clause [CRI flag]
 └─ cri_instruction_resource.load_orchestration_instructions [always]
```

The instruction/resource configs are **not themselves authority or permission**; user/provider/tool input cannot override these resources. Reuse existing contract loaders and fail-closed provenance.

Other consumer paths: `app/infrastructure/interoperability/config.py` imports `Settings`; tests `test_pydantic_ai_runtime_config.py` and CRI/evidence/presentation tests must be identified through full `rg`+AST. GitHub API call graph is incomplete. Run local status, proper authority read and full tests before implementation.

## 5. Implementation plan and gates

1. Reanchor HEAD/status/authorities/ledger and check docs245/246 execution status first. Inventory actual config consumers, JSON resources and envs across Docker/scripts/test/deployment; avoid inactive toggles masquerading as real features.
2. RED tests for native structured output with/without CRI, validated instruction/presentation resources, source fingerprint, secret redaction, AuthZ/Keycloak, malformed settings, local LLM egress; ensure bad values fail closed.
3. Remove CRI-only resources and flags only after native Agent takes over semantic response and contract; preserve trusted presentation labels and instruction resources with still-live consumers.
4. Decouple Pydantic JSON loader from orchestration implementation constants, without weakening safety ceilings. Consider Pydantic v2 typed schemas only if reduces duplication and preserves exact validation; no second JSON/framework.
5. Simplify Settings by removing genuinely dead toggles/branches and duplicate owner defaults, classify each key as RETAIN/REMOVE/CONFIG_JSON/SECRET/SECURITY_INVARIANT/INDEPENDENT_CONTEXT. Verify Core/Keycloak/MCP/STT are not incorrectly moved into intelligence config.
6. Full backend + RED/GREEN + typed schema + runtime native E01–E10 local reconstructed when possible; config fingerprint must match evaluated SHA; privacy/secret/egress negatives.
7. Residual search `DELIA_RESPONSE_INTELLIGENCE_ENABLED`, `DELIA_ORCHESTRATION_ENGINE`, `DELIA_MODEL_RUNTIME`, `DELIA_SUBOBJECTIVE_FANOUT`, `DELIA_CHECKPOINT_DB`, `DELIA_MCP_CATALOG_MODE`, obsolete `CRI` symbols and default constants; distinguish historical docs from live code.
8. Update docs 239/243/245/246/248/249/250 and ledger with factual diff, tests and consumer map; next numbered report; commit/push main preserving WIP. Production deploy NOT_AUTHORIZED.

**Acceptance:** config remains fail-closed, with one authoritative nonsecret JSON for Pydantic AI, live Core/MCP/Keycloak and STT ownership intact, no obsolete CRI semantic toggles/stages, no duplicate hardcoded agent budgets, no import of full orchestrator for config, no implicit legacy, all tests and real owner outcomes proved.

## 6. Evidence status

**PROVEN:** 4 files read on HEAD; root composer imports all three CRI resource loaders and runtime Settings; JSON loader imports orchestration constants and retry constants; Settings has legacy-env rejection, live MCP and STT configuration; actual `pydantic_ai.runtime.delpi.json` is checked in.

**TO_INVENTORY:** canon/ledger conflicts, complete dynamic consumers, deployment env values, tests and actual runtime behavior, source reducer equivalence, unknown configs.  

**TEST_NOT_RUN:** no code edits, no local tests, no production deploy in this audit.
