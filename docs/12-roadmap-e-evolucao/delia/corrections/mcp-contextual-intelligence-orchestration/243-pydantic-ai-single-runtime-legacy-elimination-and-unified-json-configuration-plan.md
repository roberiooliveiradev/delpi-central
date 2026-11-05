# 243 — DÉLIA — Único runtime Pydantic AI e configuração unificada JSON

**TASK_ID:** DELIA-C3-PYDANTIC-AI-ONLY-RUNTIME-AND-UNIFIED-INTELLIGENCE-CONFIG-01  
**DATE:** 2026-11-05  
**STATUS:** PLANNED / AUDIT-PENDING-CONTRACT-VALIDATION — nenhuma alteração de runtime realizada nesta documentação  
**CODE HEAD REVIEWED:** df76410c0e5aeb659fbc96ba9b0e209d905a6488  
**PREDECESSORS:** docs 239–242; canonical 16→50→17→49→51→52→21→20→25; ledger  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**SOURCE OF DIRECTION:** pedido explícito do usuário: não manter NENHUM runtime de inteligência legado, remover todas as variáveis obsoletas e centralizar ajustes efetivos do Pydantic AI em UM arquivo JSON versionado e observável.

## 1. Decisão solicitada e seus limites

**TARGET — NO LEGACY INTELLIGENCE:** todos os caminhos de execução semântica de modelo que não usem o runtime Pydantic AI devem ser eliminados, incluindo configuração de seleção de legado, adapters obsoletos, fallbacks, testes exclusivamente de engine removida, documentos de runtime stale e secrets/confusões de defaults, depois de inventariar consumidores, provas de paridade e decisões congeladas. Não haverá seletor de engine oferecendo legacy/delia/langgraph. **Não confundir remoção de modelos legados com eliminação de Core, Domain, Evidence, Policy, Decision, proteção OT, write governance ou integração de voz/STT/embeddings que seja um bounded context real e documentado.**

**TARGET — ONE JSON CONTROL SURFACE:** toda configuração *não secreta e efetivamente consumida* pelo runtime Pydantic AI (model name, provider class, tokens, budgets, retries, tool limits, toolset registration switches, context/window and output policy, telemetry, error handling) estará declarada e explicável num JSON único. Config não substitui runtime facts nem permissões. O JSON é um perfil **operacional** carregado pela Infrastructure, com validação tipada e fail-closed; não é um novo motor ou provider registry. **Credentials/endpoints sensíveis permanecem em env/secret store** como referências, não valores no JSON. Segurança/autorização governada permanece owner/Core; limites de segurança do servidor não podem ser flexibilizados por JSON.

**Precedência:** canonical authorities and approved frozen decisions > compiled security invariants > validated non-secret JSON > secrets/transport bound through environment. Se uma decisão congelada exigir o antigo `DELIA_MODEL_RUNTIME=legacy`, registrar ARCHITECTURE_DECISION_REQUIRED e STOP nesse recorte, sem apagar em silêncio. Pedido do usuário autoriza a mudança de direção de produto mas não cria falsos contratos.

**EXISTING_EQUIVALENT:** YES para Pydantic AI Agent, FunctionToolset, RunContext, UsageLimits, validation/retries, history; YES para Settings/root composition e governed model invocation existentes; TO_INVENTORY para config-loader/schema canônico já existente e demais consumers. **REUSE_DECISION:** REUSE/EXTEND dos mecanismos existentes; REMOVE de caminhos alternativos; NEW só se ausência de loader validado for comprovada.

## 2. Evidence audit on current code (PROVEN from inspected sources)

- `delia-api/app/infrastructure/config/settings.py` **lines 120–135** still admits `DELIA_MODEL_RUNTIME=legacy|pydantic_ai`; line 135 stores `model_runtime`.
- `delia-api/app/composition/root_composer.py` **lines 641–690** still branches on `settings.model_runtime == "legacy"` to construct the alternative model invocation adapter. Its orchestration mode is independently `_SUPPORTED_ORCHESTRATION_ENGINES={"pydantic_ai"}`. **These are two separate selectors**; removing only `DELIA_ORCHESTRATION_ENGINE=delia` did not retire legacy *model invocation*.
- Settings legacy/budget knobs **lines 93–115, 143+, 248–325**: `DELIA_LLM_MAX_OUTPUT_TOKENS`, `DELIA_LLM_CONTEXT_TOKENS`, `DELIA_TURN_BUDGET_SECONDS`, `DELIA_MAX_GOVERNED_ATTEMPTS`, `DELIA_LLM_CALL_MAX_ATTEMPTS`, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS`, `DELIA_ORCHESTRATION_ENGINE`. Whether each is still legitimately used elsewhere = TO_INVENTORY, not assumed dead.
- `delia-api/app/application/model_invocation/governed_retries.py` contains `LLM_CALL_MAX_ATTEMPTS=3` and custom retry classification. **Audit whether non-Pydantic consumers remain** and whether native Pydantic AI retries can replace any subset without changing safety contracts.
- `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py`: **lines 65–66** `_DEFAULT_REQUEST_LIMIT=12`, `_DEFAULT_TOOL_CALL_LIMIT=8`; constructor accepts request/tool limits at **lines 494–504**; `Agent(... retries=1)` near **line 1053**; `UsageLimits(request_limit, tool_calls_limit)` near **1066–1068**. Also local display/serialization limits (`_bounded_json(limit=6000)`) and tool observability. These should be classified as tunable, invariant/security cap or implementation-only; only actual safe tunables go into JSON.
- `delia-api/config/` currently contains `cri_instructions.delpi.json`, `cri_presentation.delpi.json`, and `orchestration_instructions.delpi.json`; **no existing single file with all Pydantic AI runtime knobs was identified by this directory listing**. Reuse the existing config resource loader if feasible; do not claim none exists without full residual search.
- `delia-api/app/infrastructure/model_invocation/` includes `openai_compatible_adapter.py`, `pydantic_ai_adapter.py`, `deterministic_test_adapter.py`, `openai_compatible_transcription_adapter.py`. **DO NOT indiscriminately delete:** model invocation legacy path must be removed or routed to Pydantic AI, while transcription/STT and deterministic testing may serve independent legitimate contexts. Runtime paths and consumers need proof.
- Pydantic AI semantic runtime package's rollback `DELIA_ORCHESTRATION_ENGINE=delia` was already removed in commit `7e0b8df4f7...` (doc242); **remaining legacy model-runtime branch is a distinct open problem**.
- Doc242 reports real E01–E10 as **TEST_NOT_RUN** after migration; tests and live proof are required before production acceptance. The previous removal deleted 77 suites; new work must verify contract coverage rather than relying only on remaining test count.

**Potential drift:** the project's canonical docs may prescribe legacy model invocation fallback independently of orchestration; this source review is not a complete authority read. No code deletion until actor verifies canon in required order. Distinguish observed code from unverified production use.

## 3. Proposed single JSON file and data contract

**Proposed path:** `delia-api/config/pydantic_ai.runtime.delpi.json` — ONE human-reviewable, non-secret runtime tuning artifact. Before creating confirm existing config loader and avoid parallel file format or configs. Strong preference immutable checked-in profiles rather than opaque mutable values.

**Illustrative structure (schema to be finalized after source audit, values are historical baseline and not performance recommendations):**

```json
{
  "schema_version": 1,
  "runtime": "pydantic_ai",
  "model": {
    "provider_kind": "openai_compatible",
    "model_name": "qwen3:4b-instruct-2507-q4_K_M",
    "effective_context_window_tokens": null,
    "max_output_tokens": null
  },
  "agent": {
    "request_limit": 12,
    "tool_calls_limit": 8,
    "tool_retries": 1
  },
  "budgets": {
    "turn_wall_clock_seconds": 300,
    "model_call_timeout_seconds": 30
  },
  "tool_results": {
    "max_projection_chars": 6000
  },
  "observability": {
    "record_model_id": true,
    "record_usage": true,
    "record_config_fingerprint": true
  }
}
```

**IMPORTANT:** The sample model name/limits are copied from recent evaluated/local defaults solely to establish a shape; they are **not validated production values or a new model choice**. Fields `effective_context_window_tokens` and `max_output_tokens` must remain null until provider configuration and billing/context facts verified; do not infer nominal model limit. If product policy requires runtime environment variability, use a single typed JSON with explicit validated environment profiles and no unknown-property tolerance; prefer deployment-selected profile identifier over many independent environment overrides. This is still ONE JSON source of defaults, not secrets.

**Schema/validation requirements:** typed model(s) in Infrastructure only; forbid unknown keys, schema_version checks, explicit safe ranges, cross-field constraints (request vs tool limits, timeout vs global deadline), production failure on invalid/missing config (no silent legacy fallback), deterministic config hash, tests for all schema properties and malformed inputs. Preserve stricter non-configurable security hard caps and mandatory cancel/deadline. Any override must be explicit allowlisted and observable, not ad-hoc os.getenv scattered across agent and model adapters. JSON must not contain secrets, tokens, auth endpoints requiring confidentiality, user identities, RBAC roles, provider capability ACLs or Domain authority.

## 4. Config inventory to perform — every old and new variable

Build a manifest with `symbol/env/json_key/declared_source/consumers/effective_runtime_path/policy_owner/is_secret/is_security_invariant/candidate_action/removal_test`. Mandatory search:
- `DELIA_MODEL_RUNTIME` and `model_runtime == legacy`
- `DELIA_ORCHESTRATION_ENGINE`
- `DELIA_LLM_MAX_OUTPUT_TOKENS`, `DELIA_LLM_CONTEXT_TOKENS`, `DELIA_LLM_MAX_OUTPUT_*`
- `DELIA_LLM_TIMEOUT_SECONDS`, `DELIA_TURN_BUDGET_SECONDS`, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS`
- `DELIA_MAX_GOVERNED_ATTEMPTS`, `DELIA_LLM_CALL_MAX_ATTEMPTS`, `LLM_CALL_MAX_ATTEMPTS`
- `_DEFAULT_REQUEST_LIMIT`, `_DEFAULT_TOOL_CALL_LIMIT`, `retries=1`, `UsageLimits`, `max_tokens`, `num_ctx`
- prompt/context truncation, tool result limit, catalog size, output size, history and provider call budgets in native path
- legacy `openai_compatible_adapter`, `pydantic_ai_adapter`, old deterministic wrappers, configs and docs
- `DELIA_LLM_BASE_URL`, `DELIA_LLM_API_KEY`, token egress/SSO secrets: **ENV/SECRET-ONLY**, JSON uses non-secret provider_kind/model name and refers to secret key names only if needed, not values
- STT/audio-specific limits: separate bounded context; document excluded from Pydantic runtime JSON unless demonstrably a direct Agent knob.

**Do not make everything configurable:** separate `TUNABLE`, `FIXED_SECURITY_INVARIANT`, `SECRET`, `BOUNDARY_NOT_PYDANTIC`, `DEAD_LEGACY`, `MEASURED_RUNTIME_FACT`. Only TUNABLE items appear as executable JSON settings. The manifest should record excluded items and why, so the user can review one document plus JSON without overlooking active decisions.

## 5. Implementation sequencing (single bounded task for Devin)

**W0 Reanchor:** HEAD/git status + authorities, docs 239–243 + ledger; prove phase/CP/RQ; preservation of concurrent WIP. Resolve 241 duplicate document numbering via explicit crosslinks/rename plan, never silently rewrite ledger history.
**W1 Comprehensive inventory:** local `rg` and AST of Settings, `root_composer.py`, every adapter/port, CLI, docker compose/env templates/tests, LLM call sites and consumers; identify legacy path actual reachability, current model provider and independent contexts. Verify SDK 2.50.0 behavior with installed signatures, do not assume docs latest.
**W2 Remove all alternate intelligence runtime:** delete `legacy` branch and selectors, unsupported flags/old model invocation adapters where demonstrably obsolete; remove staging fallback/unknown→legacy behavior; preserve independent transcription, tests and explicit authorized deterministic fast path if business-case bounded and not another model runtime. If authority requires rollback, raise ARCHITECTURE_DECISION_REQUIRED, do not keep it quietly.
**W3 Implement one JSON:** choose/reuse canonical config loader, implement typed strict schema and centralize Pydantic AI/LLM runtime knobs. Model factory, `Agent`, `UsageLimits`, budgets, output/context policies all consume same validated snapshot. Config file tracked and fingerprint logged at boot/eval (no secrets). Eliminate duplicates in Python literals and environment. Fail closed for malformed and unknown versions. All actual effective values auditable from the single JSON.
**W4 Native semantics and governance:** verify no second controller (admission/compose must not evolve into hidden semantic planner), keep live Core/Domain AuthZ, owner scope, provenance, typed validation, outcome checking, PREPARE/ACT and no write tool on READ surface.
**W5 RED/GREEN + full suite:** config parse/range/property tests; fail-closed invalid engine/legacy env; no Pydantic bypass; llm context/output correctness (unknown stays unknown); deadline/cancel; candidate/provenance; cross-owner/clarify; tests of independent STT; boot with approved profile; full backend tests and local real E01–E10 on rebuilt SHA (report TEST_NOT_RUN if impossible). Coverage impact of 77 removed suites requires explicit quality review.
**W6 Documentation/evidence:** next numbered execution report, doc239 register update, doc243 actual config manifest + decisions, ledger, residual search; list before/after vars, files, runtime paths, config digest, tests, real outcome, evaluated SHA/runtime SHA, no deployment. Commit/rebase/push main preserving WIP.

**Acceptance gates:**
AC1 No executable legacy model runtime, no `DELIA_MODEL_RUNTIME=legacy`, no `DELIA_ORCHESTRATION_ENGINE=delia`, no hidden fallback.
AC2 One and only one checked-in JSON for **non-secret Pydantic intelligence runtime tuning**; every live tunable has a typed key, documented units, defaults and consumers.
AC3 No duplicate hardcoded agent token/tool/retry/budget tunables in Python/env; deliberate fixed safety invariants documented outside the JSON.
AC4 No credentials/user data/permissions in JSON; Core/Domain and Policy enforce independently; fail-closed boot and authorization.
AC5 SDK boundary isolation, single Agent/tool loop, actual owner READ, evidence/Outcome/stream contracts preserved.
AC6 full backend suite AFTER final diff, security, regression, infrastructure and tested config profile green.
AC7 E01–E10 local rebuilt runtime, task Outcome judged separately from evidence grounding; partial/inconclusive honest.
AC8 Docs/ledger/report/push verified; production deploy NOT_AUTHORIZED.

**Mandatory report:** TASK_ID; BASE_HEAD; FINAL_SHA; ORIGIN_MAIN; PUSH_VERIFIED; AUTHORITIES_READ; PHASE_CP_RQ; LEGACY_PATHS_REMOVED; CONFIG_JSON_PATH; CONFIG_SCHEMA_VERSION; CONFIG_EFFECTIVE_FINGERPRINT; MODEL_PROVIDER; MODEL_ID; TOKENS_INPUT_WINDOW; MAX_OUTPUT_TOKENS; REQUEST_LIMIT; TOOL_CALLS_LIMIT; RETRIES; TURN_BUDGET; SECRET_BINDINGS; VARIABLES_REMOVED; VARIABLES_KEPT_WITH_REASON; JSON_KEYS_CONSUMERS; FIXED_INVARIANTS; OWNERSHIP_GATES; FULL_SUITE; SECURITY; E01_E10; EVALUATED_SHA; LOCAL_RUNTIME_SHA; FALSE_GROUNDED; DOCS_LEDGER; EXECUTION_DRIFT; RESIDUAL; VERDICT; PRODUCTION_DEPLOY=NOT_AUTHORIZED.

**Plan only. No implementation completed by this documentation change.**


---

## 6. EXECUTION-READY ADDENDUM — DEVIN (2026-11-05)

**BASELINE CONFIRMED:** `79a0b60e73306a6b352033d831c42f4e95575ced` at the start of this addendum. Git status is NOT observable through GitHub API; Devin must read local status before any file write. The plan remains **PLANNED**, not implemented.

### 6.1 Scope / explicit removal policy

- **DELETE the alternate model inference runtime:** `settings.py` currently accepts `DELIA_MODEL_RUNTIME=legacy`; `root_composer.py` branches to `OpenAICompatibleModelInvocationAdapter` on that value. Remove executable legacy branch, configuration and fallback; choose Pydantic AI only. Verify actual consumers of `openai_compatible_adapter.py` before physical deletion; if no legitimate independent consumer, delete the file and its tests/flags. Do not confuse OpenAI-compatible protocol/endpoint with the obsolete OpenAICompatible *legacy adapter*: Pydantic AI may still speak that protocol.
- `DELIA_ORCHESTRATION_ENGINE` can be retired as a selector if the one allowed value is `pydantic_ai`; startup must reject explicitly supplied obsolete choices. Eliminate duplicate source-of-truth for this runtime decision. Where a canonical decision requires a strict whitelist or setting for compatibility, keep only validation with no alternative execution path and document the exception.
- Audit every direct and indirect model invocation consumer: admission, evidence composition, generic interaction, agent tool loop, dictation/STT and tests. **The model invocation adapter based on Pydantic AI is not itself legacy** if it serves legitimate separately governed model-call ports; do not delete it reflexively or reroute calls around governance.
- **No runtime fallback to deterministic TestModel in production**; local/test-only substitution explicitly guarded. Remove obsolete alternate model implementations and config, not deterministic business validation.

### 6.2 One configuration file — effective-value and secrets separation

Implement **one canonical JSON artifact** at `delia-api/config/pydantic_ai.runtime.delpi.json` unless documented existing authoritative config path supersedes it. The JSON must carry all **non-secret, user-tunable intelligence values**, with strict typed validation in Infrastructure. Prefer a clear section for `model`, `generation`, `agent`, `context`, `budgets`, `tool_results`, `observability`, `schema_version`. All *active* runtime knobs must be represented and consumed exactly once.

Mandatory fields to inventory and either (a) move to JSON, (b) retain as invariant, (c) classify independent concern, or (d) delete:
`DELIA_LLM_PROVIDER`, `DELIA_LLM_MODEL`, `DELIA_LLM_MAX_OUTPUT_TOKENS`, `DELIA_LLM_CONTEXT_TOKENS`, `DELIA_LLM_TIMEOUT_SECONDS`, `DELIA_MODEL_STAGE_TIMEOUT_SECONDS`, `DELIA_LLM_CALL_MAX_ATTEMPTS`, `DELIA_TURN_BUDGET_SECONDS`, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS`, `DELIA_MAX_GOVERNED_ATTEMPTS`, `DELIA_MODEL_RUNTIME`, `DELIA_ORCHESTRATION_ENGINE`, `_DEFAULT_REQUEST_LIMIT`, `_DEFAULT_TOOL_CALL_LIMIT`, `retries=1`, `_bounded_json(limit=6000)` and all related model history/truncation/output/ctx budgets, native SDK call settings and Docker envs. Retain **credentials, API keys and sensitive endpoints** in deployment secrets/environment, never JSON plaintext. If model name is environment-dependent, define explicit profiles in the same JSON with one validated selection and clear resolved profile hash (no second independent env value overriding JSON silently).

`null` output/context limits are **UNKNOWN / UNCONFIGURED**, not "unlimited" and not evidence of provider real capacity. Do not turn a 4B local model's nominal context into a claimed effective context window. Distinguish `max_output_tokens` from actual measured output tokens, request budget from tool calls, and per-model-call timeout from entire turn deadline. Enforce production-safe ceilings and coupling constraints; JSON cannot weaken irrevocable security/authorization caps.

Startup validation must be strict (unknown keys/version, bad ranges, incompatible budgets, deleted legacy env values, missing profile, malformed JSON → fail closed). JSON must not contain instructions to grant permissions, provider tool allowlists as authority, token material, user-specific secrets or MCP discovery responses. One immutable effective config snapshot per process/session; log non-secret fingerprint and selected profile, including evaluated SHA/config in test/eval output. Inspect whether resource packages/working directory reliably locate JSON in Docker and test.

### 6.3 Execution proof instead of cosmetic centralization

Produce table `variable | old owner/file/env | consumers | effective value | new json key or invariant/exclusion | default | tests | deletion evidence`. Include runtime grep after changes for *all* old env names and literal limits; any residual string in live code needs justified classification. Tests must demonstrate altering JSON **actually changes** `Agent`, `UsageLimits`, provider request params, output cap, budgets and telemetry where applicable, not merely updates a parsed dictionary.

Verify independently that `delia-api/app/infrastructure/model_invocation/pydantic_ai_adapter.py` shares the same resolved typed config and never reads alternate scattered runtime defaults. No new planner, semantic dispatcher, config registry or duplicate config service.

### 6.4 Required verification / acceptance

RED tests (before changes): legacy selection reachable, distributed limits; GREEN tests: unknown/legacy engine fails closed, only Pydantic AI, JSON valid/invalid/schema version, secrets excluded, full source-of-truth effect, typed caps, provider and local SDK signatures; owner READ E02/E03/E05, evidence E04/E06/E10 honest, clarification E07, denial E08, NDJSON E09; independent STT remains stable; complete backend tests **after last diff**, runtime rebuild and E01–E10 **on evaluated SHA**. No production deploy. If cannot run true E2E, mark `TEST_NOT_RUN` and verdict `ACCEPT_WITH_RESIDUAL` or `INCONCLUSIVE`, never `ACCEPT`.

Critical condition: **Do not delete tests merely because they expose behavior still promised by product contracts**. Replace obsolete implementation-coupled tests with real native-path behavioral equivalents, including residual coverage of the 77 tests deleted in doc242.

No stage phase advance by documentation. Document end-state, removed settings, all effective JSON settings, explicitly excluded security/secret/STT settings, file changes, tests, runtime SHA, commit/push, unresolved decisions. Update doc239 + ledger and publish next available numbered report after doc243. Avoid duplicated historical doc241 names by precise filename/links rather than silent renumbering.

**EXECUTION ACCEPTANCE:** zero executable legacy intelligence runtime, exactly one canonical non-secret tuning JSON, native Pydantic AI using all effective tunables, no scattered duplicate defaults, no regressions in authority/evidence/Outcome, and independently verified local runtime results. Production deploy NOT_AUTHORIZED.
