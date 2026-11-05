# 256 — DÉLIA · Plano consolidado de limpeza de legado, redução arquitetural e convergência Pydantic AI

**TASK_ID:** `DELIA-C3-CROSS-FOLDER-NATIVE-PYDANTIC-AI-CONSOLIDATED-LEGACY-CLEANUP-01`  
**DATA:** 2026-11-05  
**REBASELINE HEAD (documentação):** `681e6d59d33db0763862a6e0dd31c0825710b26e`  
**REFERÊNCIAS:** inventários e decisões 239–255 (incluindo 254 application/ports), autoridades 16→50→17→49→51→52→21→20→25, specs MCP/AI pertinentes, execution ledger.  
**TIPO:** plano coordenador de implementação **PLANNED**; nenhuma remoção de código, teste, deployment ou mudança de fase decorrente deste documento.  
**EXECUTION OWNERS:** GPT = coordenação/review; Cursor/Devin = checkout, menor diff, testes/evals, evidência; GitHub = persistência.  
**PRODUCTION_DEPLOY:** **NOT_AUTHORIZED**. Fase e NEXT devem ser revalidados em `16` + ledger no HEAD de cada etapa.

## 0. Correções obrigatórias de interpretações das auditorias isoladas (sem reconciliação silenciosa)

**DECISION CONFLICT A — C3-T4 Structured Understanding.** O doc255 identificou uma implementação que **não é wired no root_composer** e é exercitada por testes TEST_ONLY. Isso é PROVEN. Porém a autoridade **21 §4D** declara `C3-T4=APPROVED`, `OWNER=delia-api/domain+application/structured_understanding` e `BOUNDARY=ACCEPT`, corroborada por **20 C3-T4** e **25 §27**. **Não está autorizada a exclusão de `application/structured_understanding/` nem `domain/structured_understanding/` por mera falta de wiring.** Até decisão superior explícita, **KEEP** a capability isolada, preserve seu contrato de observação-only, single SourceRef, no FACT, no ACT, no fabricated confidence/eval. Sua adoção de typed Pydantic AI é **REVIEW/EXTEND** apenas quando requerida pela autoridade/consumers, não reimplementação especulativa. Qualquer proposta de DELETE exige `ARCHITECTURE_DECISION_REQUIRED`, com mudança explícita de decisão congelada.

**DECISION CONFLICT B — C3-T5 OpenAPI.** O doc247 encontrou o direct DELPI OpenAPI sem wiring na composição atual (PROVEN). Porém **16 §C3-T5** e **20/25 C3-T5** aprovam a **fundação OpenAPI Action Catalog + Capability Projection**, com prova TEST_FIXTURE; `REAL_DELPI_OPENAPI_COVERAGE=NOT_PROVEN`. **Remoção do adapter direto de DELPI != autorização para eliminar toda a fundação C3-T5.** `infrastructure/openapi/*` e `application/capability_provision/openapi_provider.py` são candidatos à exclusão **somente se** a reancoragem provar um owner/contrato de preservação do foundation por outro caminho aprovado OU houver decisão superior de aposentadoria. Se nenhum equivalente preservar o C3-T5 aprovado, **STOP / ARCHITECTURE_DECISION_REQUIRED** em vez de DELETE. Manter testes de fixture/contratos conforme authority.

**DECISION CONFLICT C — SNAPSHOT_EXPERIMENT.** O doc248/255 encontrou consumer condicional de `snapshot_interop.py` e `mcp/catalog_store.py`, e import direto **Application→Infrastructure**. Isso viola a direção de dependências do 49. Verificar doc216, ledger e decisão da trilha experimental. Se aposentada, remover conjunto completo; se preservada, decidir correção de boundary por mecanismo existente/owner legítimo; sem inventar port especulativo nem silenciosamente conservar violação.

**DOC NUMBER COLLISIONS:** já existem dois docs `241-*` e dois `245-*`, com funções diferentes (plano de remoção Outcome vs relatório de unificação runtime). Referenciar sempre por **basename completo**, não apenas “doc245”. Não renumerar histórico. A convergência Pydantic AI-only/JSON único **já foi executada** segundo ledger/report `245-pydantic-ai-single-runtime-legacy-elimination-and-unified-json-execution-report.md`, incluindo remoção do antigo adapter `openai_compatible_adapter.py` e 1172 testes no SHA histórico. Não reexecutar sua remoção nem degradar a evidência histórica. Os planos `244-paginated-result-semantics-total-removal-and-consumer-remediation.md` e `245-outcome-assessment-full-removal-pydantic-ai-structured-output-consumer-migration.md` continuam **PLANNED / not implemented** no código inspecionado (validar HEAD novamente).

## 1. Escopo físico total e baseline (sem dupla contagem)

**11 pastas lógicas, 66 arquivos analisados, aproximadamente 23.885 linhas extraídas pela API GitHub**. Os valores são baseline de inventários históricos por pasta, não medida sincronizada no novo worktree; conferir HEAD e `wc -l` de todos no executor. `interoperability/mcp` está **incluída** na contagem de `interoperability` (não contar duas vezes). `application/ports` foi auditada no doc254.

| Grupo (doc) | Arquivos | Linhas aprox. | Objetivo |
|---|---:|---:|---|
| `application/capability_provision` (246, 244–245) | 11 | 11.568 | Eliminar assessores/paginação semântica/CRI redundantes; encolher orquestração |
| `infrastructure/openapi` (247) | 3 | 854 | Decisão de retenção do foundation C3-T5 vs eventual retiro de adapter direto órfão |
| `infrastructure/interoperability` + `mcp` (248) | 7 | 1.494 | Preservar MCP/credenciais e revisar snapshot/transport |
| `infrastructure/model_invocation` (249) | 4 | 900 | Typed Pydantic AI, timeout real, STT separado |
| `infrastructure/config` (250) | 4 | 1.554 | JSON único ativo; remover CRI/flags mortas e desacoplar validation |
| `infrastructure/http` (251) | 4 | 1.005 | Preservar timeout absoluto/DNS; integrar STT streaming |
| `application/interaction` (252) | 13 | 4.629 | Reduzir handler e observabilidade sem perder Outcome, PREPARE/ACT, NDJSON |
| `application/model_invocation` (253) | 6 | 800 | Eliminar schema-stage/retries/context assumptions obsoletos |
| `application/ports` (254) | 5 | 178 | Preservar 4 ports legítimos e gap de streaming incremental |
| `application/specialist_interop` (255) | 5 | 642 | Preservar integração MCP; corrigir snapshot layer violation |
| `application/structured_understanding` (255) | 4 | 261 | Preservar C3-T4 aprovado, não apagar por falta de wiring |
| **TOTAL** | **66** | **23.885** | Resultado medido por código/testes, não por redução estética |

Aparatos fora desses 66 arquivos que entram **somente quando dependência transitiva provada**: `domain/structured_understanding/{model,rules}.py`, `infrastructure/orchestration/pydantic_ai_investigation.py`, `application/capability_provision/orchestration.py`, `composition/root_composer.py`, `scripts/mcp_catalog_sync.py`, `config/pydantic_ai.runtime.delpi.json`, instruction resources governados, testes de matriz E01–E10, Docker/dev local, docs e ledger. Não mover o inventário de outras pastas inteiro para esta tarefa.

## 2. Arquitetura alvo — ZERO segundo motor de IA

```text
User / event / bounded session
 → Interaction contracts + Core authenticated context (not authority from JWT alone)
 → Pydantic AI Agent (ONE semantic runtime; native tools, typed output, bounded memory/history, UsageLimits)
      → semantic capability toolset (provider-neutral)
           → Application governed gates (live Core AuthZ / Domain authority / read/write / policy / PREPARE-ACT)
                → SpecialistInteropPort + existing MCP adapter/transport/Keycloak
                → Evidence/SourceRef from real owner outcomes
      → typed answer / observations / missing requirements / limitations
 → deterministic Evidence+Policy+Decision acceptance of verified owner data
 → Interaction terminal / safe presentation / NDJSON / observability / authoritative outcome
```

**Pydantic AI nativo é responsável por:** entendimento semântico, seleção semântica de ferramentas, investigação multietapa e saída tipada `Agent(..., output_type=...)` com `output_validator` onde aplicável, `RunContext`, `FunctionToolset`, `UsageLimits`, uso/telemetria real do SDK. Usar capabilities reais da versão instalada (ledger aponta `pydantic-ai 2.50.0` em execução histórica), não inventar interfaces nem passar um `output_type` e um loop extra por conveniência.

**DÉLIA Application/Domain retêm:** identidade e autorização live em owners legítimos; validação independente do schema/argumentos owner; SourceRef/Evidence qualification; real provenance, missing/partial/conflicts, comparação factual, privacy/redaction, owner business Outcome, idempotency, audit, confirmation, PREPARE/ACT, timeouts de turno, continuidades bounded, abstention honesta. `LLM output != FACT`; `HTTP200 != outcome`; `metadata MCP != permission`. Saída tipada significa **schema sintático/semântico governado**, nunca autotestemunho de dados empresariais.

**Não criar:** novo LLM engine, CRI v2, Outcome engine caseira, step planner, heuristic regex intent detector, provider-specific selection branches, catalog mirror, executor paralelo, shared DB/source of truth, novo config JSON, schema registry para compensar código morto, migration para runtime Chat.

## 3. Dependência principal — fechamento do contrato antes das exclusões

Antes da primeira mudança de fonte, mapear para cada símbolo `owner → origin → consumers → response/exception → security → tests → authoritative postcondition`; buscar repo integral via `rg -n`/AST + testes de import, `root_composer` e configurações reais. Definir **um contrato de resposta estruturada** baseado nos tipos de Evidence/SourceRef/Interaction existentes, não um novo engine.

**Proposta de output, a ratificar contra contratos existentes:** final answer, answered_obligations, unanswered_obligations, evidence_source_refs, limitations/uncertainty, incomplete/clarification, schema/version. Pydantic output values são **claims candidatos**. Um acceptor determinístico mapeia refs exclusivamente ao set de outcomes realmente observados e ao escopo Autorizado; status grounded/partial/complete não é declarado autoritativamente pelo modelo. Não guardar chain-of-thought. Observabilidade preserva tokens reais, calls e deadlines, sem inventar telemetry.

**Critical impact map:**
- `outcome_assessment.py` → `orchestration.py`, `conversational_response.py`, `generic_evidence_renderer.py`, `interaction/handle_interactive_turn.py`, **`interaction/argument_validation.py`** (cinco funções importadas) e testes. Doc245 inicial não contém todos os consumidores identificados depois; corrigir antes de excluir.
- `paginated_result_semantics.py` → `outcome_assessment.py`, `orchestration.py`, demais indiretos. Counts/offset/cursor/owner scope devem continuar autoritativos, não inferidos pelo LLM.
- `conversational_response.py`/CRI → `root_composer`, `config/cri_instruction_resource.py`, `interaction/presentation.py`, `instruction.py`, `turn_observability.py`. Não apagar field labels e sanitização que permanecem em uso.
- `model_invocation` Application → Infra `pydantic_ai_adapter.py` → `InvokeModel` → `handle_interactive_turn` e `orchestration`; `structured_understanding` também usa `InvokeModel`, e é C3-T4 aprovado. **Não apagar InvokeModel nem seu port antes de provar consumidores migrados, mantendo C3-T4.**
- `SnapshotDiscoverInterop` → Infra `McpCatalogStore`, `scripts/mcp_catalog_sync.py`, `Settings`, `root_composer` e testes. Decisão cruzada.
- `openapi_provider.py` → `infrastructure/openapi`; decisão de preservar C3-T5 aprovado antes da exclusão.
- STT incremental usa `requests.post` direto e `SpeechTranscriptionPort` cobre principalmente transcrição não-stream; doc254 informa gap contratual. Ajustar sem colocá-lo no JSON de Agent e sem criar abstração especulativa.

## 4. Decisões por arquivo — MASTER MATRIX (TODOS os 66)

Legenda: **DELETE_APPROVED_TARGET** = pedido de remoção documental aprovado pelo usuário, execução não feita; **CANDIDATE** = sem autorização por authority/consumers; **KEEP** = boundary legítima; **SHRINK** = reduzir depois de comprovar duplicação; **DECISION_REQUIRED** = frozen authority gate. Linhas e nomes referem-se às auditorias 246–255.

### 4.1 application/capability_provision (11)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `contracts.py` | KEEP/SHRINK |
| `conversational_response.py` | SHRINK substantial CRI composer; DELETE only when all safe response consumers move to native structured output |
| `generic_evidence_renderer.py` | KEEP or MERGE with existing safe renderer if equivalent; no duplicate formatting owner |
| `governed_stage_gates.py` | KEEP/SHRINK; guarded tool protocol |
| `mcp_provider.py` | KEEP active MCP integration; MOVE only if correct layer and all consumers proven |
| `openapi_provider.py` | CANDIDATE only under C3-T5 authority preservation |
| `orchestration.py` | MAJOR SHRINK; remove residual custom semantic admissions/_propose/answer assembly; KEEP owner binding, evidence gates, write safety |
| `outcome_assessment.py` | **DELETE_APPROVED_TARGET** (doc245-removal); replace semantic assessment with typed Pydantic output but independent deterministic fact protection |
| `paginated_result_semantics.py` | **DELETE_APPROVED_TARGET** (doc244); preserve owner-provided exact counts/scope/cursors |
| `ports.py` | KEEP legitimate bound port |

### 4.2 infrastructure/openapi (3)

| Arquivo | Alvo |
|---|---|
| `capability_catalog_adapter.py` | **DECISION_REQUIRED C3-T5**; don't remove merely because direct DELPI source unwired |
| `http_invoker.py` | CANDIDATE remove if no active approved consumer; C3-T5 fixture/contract tests preserved |
| `source_loader.py` | CANDIDATE remove if no consumer and OpenAPI foundation preserved |
If any component is the sole approved C3-T5 foundation owner, KEEP until authority-approved replacement/direction.

### 4.3 infrastructure/interoperability (+mcp, 7)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `config.py` | KEEP/SHRINK; legitimate approved specialist identity/audience/endpoint settings |
| `delegation.py` | KEEP security critical (Keycloak exchange, validation, revoke/cache) |
| `mcp/__init__.py` | KEEP |
| `mcp/adapter.py` | KEEP active live tool listing/classification + invocations |
| `mcp/catalog_store.py` | DECISION_REQUIRED snapshot experiment; candidate retire with complete cross-folder diff |
| `mcp/transport.py` | KEEP; candidate SDK MCP transport replacement only after full parity (not direct Agent MCPToolset bypassing gates) |

### 4.4 infrastructure/model_invocation (4)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP; fix stale docstring |
| `deterministic_test_adapter.py` | KEEP TEST_ONLY until Pydantic TestModel/FunctionModel parity, then SHRINK/DELETE if consumer removed |
| `openai_compatible_transcription_adapter.py` | KEEP speech STT, fix deadline/reuse; not legacy text runtime |
| `pydantic_ai_adapter.py` | SHRINK and use strict typed output; drop generic `create_model(... Any, extra=allow)` + duplicate JSON prompt after real consumer migration; cancel/deadline audit |

### 4.5 infrastructure/config (4)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `cri_instruction_resource.py` | SHRINK only obsolete CRI clauses; KEEP live field-label vocabulary and orchestration instructions |
| `pydantic_ai_runtime_config.py` | KEEP typed schema and JSON config; decouple direct import of orchestration constants; reduce validator boilerplate only if parity |
| `settings.py` | KEEP Core/MCP/Keycloak/STT/secrets; retire dead CRI toggles, obsolete selectors and snapshot flags only when coordinated; retain stale-env fail-closed as required |

### 4.6 infrastructure/http (4)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `bounded_request.py` | KEEP shared response/total deadline/size cap; SHRINK duplication with proven equivalence |
| `deadline_transport.py` | KEEP hard-proven absolute DNS/TCP/TLS/header/body budget; no naive `requests(timeout=N)` replacement |
| `dns_resolver.py` | KEEP approved bounded DNS; only replace with equivalent owner-approved behavior |

### 4.7 application/interaction (13)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `activity.py` | KEEP/SHRINK truthful progress events + NDJSON |
| `argument_validation.py` | KEEP independent owner schema/security checks; remove `outcome_assessment` helper imports; reuse JSON Schema validator only after parity |
| `capability_attempt.py` | KEEP/SHRINK true governed status/provenance |
| `contracts.py` | KEEP interaction/composite Evidence/terminal DTOs |
| `errors.py` | KEEP |
| `handle_interactive_turn.py` | MAJOR SHRINK: eliminate duplicate semantic response paths; KEEP AuthZ, continuity, PREPARE/ACT, terminal serialization |
| `instruction.py` | REVIEW overlapping native Agent instructions; preserve lineage where used |
| `pending_proposals.py` | KEEP pending write TTL, replay/idempotency boundary |
| `presentation.py` | KEEP safe markdown/UI projection |
| `turn_budget.py` | KEEP absolute turn deadline |
| `turn_observability.py` | SHRINK duplicate model-call metrics/CRI-stage fields, preserve truthful usage |
| `workspace_context.py` | KEEP untrusted Portal context, never authorization |

### 4.8 application/model_invocation (6)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `context_budget.py` | KEEP/SHRINK conservative pre-call budget (estimates != model-measured tokens) |
| `contracts.py` | KEEP neutral ModelInvocation/Eval/lineage contracts |
| `errors.py` | KEEP |
| `governed_retries.py` | REVIEW native retry parity vs outer provider availability; avoid retry multiplication |
| `invoke_model.py` | SHRINK duplicate structure validation when typed output done; preserve legitimate consumers incl C3-T4 and eval lineage |

### 4.9 application/ports (5) — doc254

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `model_invocation_port.py` | KEEP/SHRINK when native semantic stages migrated, respect approved C3-T4 |
| `platform_access_port.py` | KEEP Core AuthZ |
| `specialist_interop_port.py` | KEEP provider-neutral MCP |
| `speech_transcription_port.py` | KEEP/EXTEND smallest existing contract to support incremental streaming only if required and already connected to current API; no new port |

### 4.10 application/specialist_interop (5)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP |
| `contracts.py` | KEEP minimal delegated context/RemoteTool descriptors |
| `errors.py` | KEEP typed owner errors |
| `snapshot_interop.py` | DECISION_REQUIRED; Application→Infrastructure import violation to resolve via approved experiment retirement or architecture change |
| `specialist_interop.py` | KEEP active bounded discovery/live invoke; SHRINK only duplicate owner-hint/error code parser after parity |

### 4.11 application/structured_understanding (4)

| Arquivo | Alvo |
|---|---|
| `__init__.py` | KEEP C3-T4 accepted |
| `contracts.py` | KEEP request/result SourceRef/observation-only |
| `errors.py` | KEEP |
| `understand_structured_input.py` | KEEP approved bounded C3-T4 use case; review staged schema with Pydantic AI when authorized, not DELETE from unwired root |

## 5. Executable dependency graph and milestones

**No Big Bang.** Every stage has one concrete diff, RED→GREEN, full regression gate, residual search and a stop criterion; current SHA/config captured before next stage. Tasks are ordered so deletion never precedes consumer migration.

```text
G0 Canon+HEAD+decisions (T4/T5/snapshot) + consumer dependency graph
 ↓
G1 Native typed response output + deterministic ground-truth acceptance (no source deletion)
 ↓
G2 DELETE paginated_result_semantics + outcome_assessment; fix ALL imports/consumers
 ↓
G3 Simplify CRI/conversational_response + orchestration + interaction native path
 ↓
G4 Consolidate model_invocation adapter / budget / retries / config + observability
 ↓
G5 Interop MCP, snapshot and C3-T5 OpenAPI decisions (bounded independent diffs)
 ↓
G6 HTTP/STT hardening + ports gap (bounded independent diff)
 ↓
G7 Integrated local real-model generalization, AuthZ/safety/Outcome, residuals
 ↓
G8 Review, final evidence, docs, ledger and handoff
```

### G0 — Baseline and authority gate (MUST PASS before code modifications)

- `git rev-parse HEAD`; `git status --short`; `git fetch origin` as appropriate, confirm `origin/main` and preserve WIP. Read Project Instructions, applicable `.cursor`, authoritative sequence, execution ledger; identify current phase, CP/RQ, model/provider versions and runtime build.
- Inventory **all 66** files at actual HEAD and their **transitive** external consumers; include searches for dynamic imports, config keys, structured domain/contracts, API routes, scripts, tests, CI/deploy. Generate machine-readable CSV/Markdown `file → symbol → consumers → boundary → contract → evidence → disposition`. Not hundreds of ad-hoc rounds: freeze a single dependency map, residual search per diff.
- Freeze/flag **C3-T4 approved KEEP**, **C3-T5 foundation approved** (direct DELPI binding may be retired separately) and **snapshot experiment** decision. If planned DELETE conflicts with authority: STOP only that slice; continue independent approved cleanup.
- Confirm Pydantic runtime version/provider and `pydantic_ai.runtime.delpi.json` fingerprint; secrets only by references, no values. Verify no old inference runtime secretly wired.

**Exit G0:** precise scope, no false deletion authorization, existing equivalent evidence, graph of dependent source changes and acceptance tests. Code edit gate PASS only for unblocked slices.

### G1 — Native structured answer output (nonbreaking first)

**RQ-01**: one Pydantic Agent semantic tool loop governs selection/reasoning and typed answer; no external select/CRI assessor or second “intelligence layer”.  
**RQ-02**: natively typed output model(s), `output_validator` if necessary, no `Any|None extra=allow` stage schema for business answer, no prompt “Respond ONLY JSON” as substitute for types; compatible with actual PydanticAI version.  
**RQ-03**: deterministic authority-bound evidence sanitizer/validator checks every source ref against real verified owner outcome, cannot promote LLM assertion to FACT; partial/missing/conflict/abstention modeled honestly.  
**RQ-04**: preserve source limits/owner pagination truth, privacy redaction, no chain-of-thought leakage, safe markdown, real usage telemetry.  
**AC:** RED tests for missing/wrong schema, fabricated SourceRefs, owner-not-found vs zero, unauthorized source, output pretending AuthZ, incomplete comparative question. GREEN on typed output+independent postcondition, no changed write behavior.

### G2 — Physical deletions requested by PO (bounded coordinated diff)

**RQ-05:** DELETE `capability_provision/paginated_result_semantics.py`, remove all imports, regex/user-intent filters; owner count/page/offset/scope preserved with typed deterministic facts.  
**RQ-06:** DELETE `capability_provision/outcome_assessment.py`, remove every import including newly found `interaction/argument_validation.py`, handler, renderer, conversational response, orchestration; do not transplant the 1806 lines into another file.  
**RQ-07:** semantic fulfillment/answer completeness produced by native output with independently verified evidence; source refs from actual owner only. Preserve numerical comparisons/ordering if owner data proves them, otherwise honest limitations.  
**AC:** both paths physically absent, residual `rg` 0 imports excluding historical docs, focused tests + full backend suite PASS, real-model case outcomes nonfalse-grounded.

### G3 — Remove remaining CRI and reduce orchestrator/interaction

**RQ-08:** reduce `capability_provision/orchestration.py` and `conversational_response.py` by removing duplicated semantic admission/answer requirement/classifiers, not by relocating same code; preserve tool registration, binding, Domain authority, limits and SourceRef projection.
**RQ-09:** `handle_interactive_turn.py` becomes thinner, focused on interaction lifecycle, AuthZ, continuation, pending writes, NDJSON terminal, honest outcomes. `presentation.py` remains deterministic, sanitized. `cri_instruction_resource.py` drops only obsolete CRI-semantic resources, retaining required vocabulary/legitimate native instructions.  
**RQ-10:** OBSERVE→CONTEXTUALIZE→DECIDE→PREPARE/ACT→VERIFY provenance with one Agent path and no provider hardcoded branches.  
**AC:** E01–E10 baseline behavior preserved/improved, no false grounded, no fake comparison/guide answer, partial completion explicit; no illegal ACT, no missing terminal message.

### G4 — Model Invocation, retries, budget, JSON settings and observability

**RQ-11:** `pydantic_ai_adapter.py`, `InvokeModel`, `ModelInvocationPort` remain only as much as consumers (incl approved C3-T4) require; no second semantic stage engine, no manually permissive response schema.  
**RQ-12:** merge/constrain retries only when `Agent.retries` parity proven; provider failures vs output-validation retries and total attempts measured; no retry storm or repeated owner ACT.  
**RQ-13:** context budget pre-call estimates are explicitly estimates, revised for current Agent schema and history; actual tokens from real SDK usage, never guessed; model timeout governed by total-turn deadline, no unbounded lingering thread work.  
**RQ-14:** single non-secret JSON `config/pydantic_ai.runtime.delpi.json` remains authoritative for effective Agent tuning; config loader decoupled from implementation constants in `orchestration.py`; hard security ceilings live at approved policy/contract boundary; Core/Keycloak/MCP/STT/secrets remain separate. Retired config flags removed only with deployment migration evidence.  
**RQ-15:** Activity/ModelCallLedger/usage and NDJSON consolidated without duplicating measurements or losing per-stage provenance.  
**AC:** measured token exactness when model exposes usage, bounded retries/cancel, config fingerprints, invalid config fail-closed, STT unchanged.

### G5 — MCP interop, C3-T5 OpenAPI and snapshots (independent authority gates)

**RQ-16:** `SpecialistInterop`/ports/MCP adapter/credential delegation remain active, live owner class rechecked before invocations, zero MCP result as FACT, zero metadata as permission. SDK transport swap only with parity in HTTP/SSE/session/auth/token/timeouts/size/errors, not as native Agent MCP tool bypass.
**RQ-17:** snapshot decision resolved: if retired, delete `application/specialist_interop/snapshot_interop.py` + `infrastructure/interoperability/mcp/catalog_store.py` + sync script + flags/tests, preserving live invocation; if retained, fix Application→Infrastructure violation by approved mechanism/owner without new authority.  
**RQ-18:** C3-T5 foundation preserved per 16/20/25; direct DELPI OpenAPI source may be removed only if no contract/consumer needs it and preserving approved foundation is shown. If not demonstrable, STOP slice with formal decision request.  
**RQ-19:** C3-T4 Structured Understanding survives with invariants; no deprecation by convenience.

### G6 — HTTP + STT bounded correction

**RQ-20:** HTTP absolute deadline across DNS, TCP, TLS, headers and body retained with network-test parity; `bounded_request`, `deadline_transport`, `dns_resolver` not ripped out for cosmetic savings.  
**RQ-21:** STT incremental streaming gets bounded total deadline and unified approved transport, retaining progressive SSE/NDJSON, audio security and voice port contract. Smallest extension only after proving existing `SpeechTranscriptionPort` consumer and streamed error semantics.

### G7 — Integrated verification and quality gates

**RQ-22** backend focused tests, complete `pytest tests/ --ignore=tests/live` and separate explicit live e2e as authorized, architecture boundary tests, key security negatives, isolated SDK TestModel/FunctionModel.  
**RQ-23** REAL local rebuilt Agent eval E01–E10: simple READ, multistep comparison, guide+structure, pagination/cross-owner, missing evidence, demonstratives/continuation, write denial, NDJSON, repeated-research goals, false grounded rate=0; quality/task completion by outcome, not just HTTP200.  
**RQ-24** security: live Core RBAC, Domain authority, unknown/malformed/expired token, tool metadata injection, resource bound, secrets/CoT absent; PREPARE≠ACT, no implicit C6 autonomous actions, no OT AI control.  
**RQ-25** end-to-end deadline (LLM/owner HTTP/STT), cancellations and limits under slow/flaky owner, no zombie new remote writes after deadline; correct cause-code and limitation.  
**RQ-26** tooling: imports/AST/rg residuals, LOC diff with functions removed, no cosmetic file split, no duplicate configs, no alternate runtime, SHA model/profile/ledger ledger-backed, reversible/rollback path.

### G8 — Implementation report + independent review

**RQ-27:** Each diff results in task-bounded `DÉLIA EXECUTION REPORT`: BASE_HEAD, FINAL_HEAD, changed/removed, test matrix PASS/FAIL/TEST_NOT_RUN, runtime model/config hash, CP/RQ completeness, Evidence/Outcome, logs redacted, residual searches, open gaps, production deploy status, next step, commit SHA.  
**RQ-28:** docs/ledger updated after execution factual, not by this planning commit. Distinct review `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`; phase unchanged absent accepted authoritative evidence. Production deploy explicitly NOT_AUTHORIZED.

## 6. RQ/AC traceability (task-level proposal, not fabricated CP)

| Stage | RQ range | Acceptance test focus |
|---|---|---|
| G0 | prerequisite | authoritative evidence/contract/consumer graph |
| G1 | RQ-01..04 | native strict schema + real owner SourceRefs + honest completeness |
| G2 | RQ-05..07 | two files gone; 0 runtime imports; outcome tests |
| G3 | RQ-08..10 | single semantic path; lifecycle, NDJSON, write gates |
| G4 | RQ-11..15 | retries/budget/usage/config/test fidelity |
| G5 | RQ-16..19 | MCP AuthZ, snapshot decision, C3-T5 preserved, C3-T4 preserved |
| G6 | RQ-20..21 | total deadline HTTP/STT, streaming |
| G7 | RQ-22..26 | full tests/evals, security/grounding/generalization/outcome |
| G8 | RQ-27..28 | evidence/ledger/handoff/independent review |

Each RQ in execution report: IMPLEMENTED / PARTIAL / NOT_IMPLEMENTED / BLOCKED / NOT_APPLICABLE. Count `IMPLEMENTED / APPLICABLE` for verified completeness; PARTIAL counts 0. Do not invent CP links: resolve CP-055/056/093/094/304 and relevant C3/MCP/OpenAPI/voice CPs from 25 at execution start.

## 7. Preventing infinite inventory/rework

Only **one dependency freeze in G0**, then specific bounded diff. Do not repeat full inventories already in docs246–255 unless HEAD changes materially in relevant paths. Focus each work package on executable source removal/refactor + tests + outcome, not another audit-only commit. Use existing SDK and contracts; avoid migration by “copying helper logic to utilities”. The first implementation G1+G2 is allowed to be a coordinated task with multiple commits but has one measurable objective: **typed native output works and the two legacy assessor files are physically gone**. G3 and G4 consume the same output contract, no second design pass. Resolve authority conflicts only where identified (T4/T5/snapshot).

**STOP conditions:** canonical C3-T4/T5 conflicts; missing AuthZ/owner contract; product quality deterioration; false grounded FACT; material write bypass; unbounded provider invocation; duplicate runtime; no reproducible source SHA/model/config; failure of mandatory test. Stop affected slice, report drift, do not silently redescribe the architecture.

## 8. Explicit status at this documentation commit

**PROVEN FROM REPO:** Pydantic AI-only runtime and unified config previously implemented (ledger and code audits); active MCP/Keycloak/Core/HTTP paths; 66 source files inventoried in docs246–255; C3-T4 and C3-T5 approved in 21/16 respectively; `snapshot_interop` import-layer violation; doc244/doc245 physical removal still pending at inspected code HEAD.

**PLANNED/TARGET:** G1–G8, physical deletion, smaller orchestration, native typed output generalized, normalized retry/accounting, optional OpenAPI/snapshot retirements after gates.

**TO_INVENTORY:** live status/current code SHA at execution, full consumer graph/AST, exact approved phase and CP mapping at new HEAD, authority for snapshot removal, proof of foundation C3-T5 if files removed, actual real-model generalization quality.

**TEST_NOT_RUN:** No code/tests/evals/deploy were performed as part of doc256. This plan does not grant production authorization.

---

## 9. Execução parcial registrada (2026-11-05, commit `88a7c4e5`)

**G2 concluído** (exclusão física dos dois módulos legados, decisão PO):

- Deletados `capability_provision/outcome_assessment.py` (1805 linhas) e `paginated_result_semantics.py` (801 linhas). Ausentes de `git ls-files`; zero imports de produção.
- Maquinaria semântica sem consumidor vivo removida: `assess_outcome`, `outcome_facts`, `OutcomeVerdict`, `EvidenceFacts`, `AnswerRequirements`, `GoalEvidenceJudgment`, `parse_goal_evidence_judgment`, `apply_verdict_limitation`, `OUTCOME_*`; classificadores regex (`classify_result_intent`, `classify_personal_ticket_scope`, `is_ticket_domain_inquiry`, `personal_scope_response`, `schema_supports_ticket_list_action`, `unique_structural_ticket_list_capability`, `arguments_include_*`); composer CRI (`compose_cri_response`, `ordering_presentation`, `_render_synthesis`, `_compose_answer`, `_proven/_selected_proven_differences`, `_insufficiency_content`, `CriComposition`, `_prior_supports_typed_attribute_compare`, `ordering_proof_fields`, `verified_ordering_event`, `distinct_delivered_count`, `_synthesis_selections`, `_wording_leaks_technical`).
- Helpers determinísticos de projeção de payload do owner consolidados em `capability_provision/generic_evidence_renderer.py` (352→1929 linhas): bounds `MAX_*`, `extract_pagination_envelope`, `aggregate_paginated_pages`, `resolve_count_semantics`, `PaginationEnvelope`/`PageAggregationResult`/`CountResolution`/`CountResolutionKind`, mensagens de contagem, control-plane stripping, sanitização/redaction, entity-schema helpers, `_comparison_records`, temporal/ordering parse, contract/evidence rows, resolver/unwrap.
- Consumidores corrigidos: `orchestration.py` (imports + `_project_paginated_personal_or_count` e call site + `_TurnGoal.answer_requirements` removidos), `conversational_response.py` (1330→689 — só render helpers), `handle_interactive_turn.py`, `interaction/argument_validation.py` — todos importando de `generic_evidence_renderer`.
- Testes: removidos `test_c3_evidence_to_answer_isolation`, `test_cri_unified_presentation`, `test_q02c_b2_typed_comparison_outcome` (acoplados ao maquinário morto); `test_r45_pagination_integrity_rework`, `test_r4_presentation_parity`, `test_render_specialist_outcome_fidelity`, `test_c3_self_awareness_ptbr_labels` reescritos para o novo owner. 7 eval scripts obsoletos (CRI/judgment) removidos.
- **Suíte `delia-api`: PASS (exit 0)** no SHA avaliado; `capability_provision` 11.207→9.802 linhas líquidas (−1.405; diff total −10.238/+1.591).
- RQ-05, RQ-06 = IMPLEMENTED (deleção física + consumidores). RQ-07 = PARTIAL (cobertura factual de outcome já era determinística no finalize; typed output RQ-01..04 ainda pendente em G1).

**Pendentes:** G1 (output_type nativo + acceptor), resto de G3 (orchestration/handler shrink), G4, G5, G6, G7, G8 — ver relatório de execução.

## 10. G2 bounded rework — review 257 (execução)

- **Correção numérica do relatório G2**: IMPLEMENTED=2 (RQ-05, RQ-06), PARTIAL=4 (RQ-01, RQ-03, RQ-04, RQ-07), NOT_IMPLEMENTED=22. Cobertura verificada canônica = **2/28 = 7,14%** (parcial tem crédito zero).
- **Testes negativos de invariantes** restaurados em `tests/test_g2_evidence_contract_regression.py` (15 casos): DISCOVERY metadata nunca vira evidência de negócio (`discovery_metadata_observation` → gate `_is_business_evidence_attempt`); página parcial (`has_more=True`) nunca resolve total (`PARTIAL_UNKNOWN`); agregação incompleta/falha → `total=None`; total só autoritativo quando declarado pelo owner; mensagem de contagem nunca afirma total não provado; valores sensíveis redigidos (`_sanitize_renderable`, `_redact_text`, `REDACTION_MARKER`); bearer tokens redigidos; chaves de control-plane (`agentdirectives`/`capabilitysurface`) excluídas; conteúdo/proveniência/outcome incompletos nunca promovidos; itens de página nunca promovidos a total.
- **Prune do consolidado**: helpers sem consumidor removidos de `generic_evidence_renderer.py` (1929→1679 linhas): `_comparable_scalar`, `_bound_owner_evidence`, `_candidate_contract_rows`, `_missing_inputs`, `_explicit_empty_business_collection`, `_bounded_subject_node`, `_result_contract_context`, `list_header_for_envelope`, `count_message_for_visible_query`, `_TECHNICAL_LEAK_MARKERS`, `_SNAKE_CASE_TOKEN_RE`, `GLPI_LINK_NO_COUNT`, `DEFAULT_PAGE_SIZE_CAP`. Mantidos os símbolos com consumidor vivo (test_r45: envelope/count contract) ou uso interno (`item_stable_id`, `_is_first_page`, `PageAggregationResult`, `aggregate_paginated_pages`, `resolve_count_semantics`).
- Suíte `delia-api` completa: **PASS (exit 0)** no SHA avaliado. Residual menor: constantes `PRESENTATION_*`/`OMISSION_*` pré-existentes não inspecionadas (fora do escopo das ~1579 linhas movidas).
- G1 (output_type nativo) prossegue como etapa independente.

## 11. G1 — output estruturado nativo (execução)

- `Agent(output_type=InvestigationAnswer)` — dataclass estrito em `capability_provision/contracts.py` (schema_version, status COMPLETE/PARTIAL/INSUFFICIENT/EMPTY/NO_EVIDENCE/NEEDS_CLARIFICATION, answer bounded, evidence_refs posicionais, unmet_obligations, limitations, clarification_question). Sem `extra`, sem `Any`, sem prompt-only JSON.
- `output_validator` apenas de forma — nunca promove declaração a FACT nem autorização.
- `_apply_declared_answer` (acceptor determinístico pós-finalize): refs ligam só a attempts de evidência de negócio reais (`_is_business_evidence_attempt`); COMPLETE só honrado com refs válidos + obrigações satisfeitas (`_evaluate_material_obligations`) + terminal SUCCESS; clarificação usa o path bounded existente; limitações/obrigações declaradas mergeam bounded; refs fabricadas reportadas `evidence_ref_unbound:N`.
- RQ-01..RQ-04: IMPLEMENTED ao nível do gate — a resposta tipada nativa existe, é validada deterministicamente e nunca promove claims do modelo a FACT. Cobertura verificada plano: **4/28 = 14,3%** (RQ-01,02,03,05,06 impl; RQ-04,07 parcial).
- Mocks migrados para a output tool `final_result`. Suíte PASS (exit 0).

## 12. G1 grounding rework — review 258 (execução)

- `_apply_declared_answer` reescrito fail-closed: prosa do modelo **nunca** substitui o conteúdo determinístico verificado — SourceRef válido comprova proveniência da observação, não a verdade de frases geradas.
- `schema_version != "1"` → `declared_schema_rejected`, terminal inalterado.
- `NEEDS_CLARIFICATION` declarado ignorado quando o terminal já carrega evidência de negócio verificada (`declared_clarification_ignored`); caso contrário, path bounded existente.
- Refs: qualquer ref inválido/não-evidência → `evidence_ref_unbound:N` + COMPLETE rebaixado (`declared_status_overridden`); `plan=None` ou `evidence_needed` vazio → cobertura desconhecida → COMPLETE nunca provado (`coverage_unknown`).
- COMPLETE consistente mantém conteúdo determinístico — a declaração só afina status/limitações honestamente.
- Testes: 14 casos em `test_g1_native_structured_output.py` (prosa alucinada + ref válido, evidência irrelevante plan=None, refs mistas, schema inválido, clarificação indevida, ref não-evidência, bound de resposta).
- Suíte `delia-api` completa: PASS (exit 0).
- RQ-03: gate factual fechado → IMPLEMENTED; RQ-04, RQ-07 = PARTIAL. Cobertura verificada: 5/28 = 17,9%.
- G1_REAL_MODEL_EVAL=TEST_NOT_RUN (E01–E10 pendente em G7).

## 13. G3 — orchestration & interaction legacy shrink + residual G1 (execução)

- **Residual G1 (doc 259 §25)**: `_apply_declared_answer` — NEEDS_CLARIFICATION declarado agora é honrado quando há evidência parcial + obrigações materiais não cumpridas → CLARIFICATION_REQUIRED com `verified_evidence_preserved` e outcome/provenance preservados; ignorado apenas quando não há necessidade provada (`declared_clarification_ignored`).
- **orchestration.py**: 9 funções mortas removidas (_single_free_text_argument_from_input, _elide_unproven_optional_args, _drop_orchestration_field_args, _drop_null_literal_args, _deterministic_arguments_from_schema, _resolve_live_group_key, _truncate_text_field, _drop_block_fields, _omit_tail_entries) — ~114 linhas, zero consumidores.
- **CRI aposentado removido**: `cri_clause`/`cri_version`/`cri_vocabulary` loading morto em root_composer; `DELIA_RESPONSE_INTELLIGENCE_ENABLED` env + `response_intelligence_*` fields em settings; `response_intelligence_enabled`/`_response_mode`/COMPOSITION_CRI label em handle_interactive_turn + turn_observability; `load_cri_instruction_clause`/`CriInstructionClause` em cri_instruction_resource; `cri_instructions.delpi.json` órfão; `test_cri_e1_response_intelligence_toggle.py` + 3 eval scripts CRI mortos.
- Diff líquido: −856/+95 linhas; `orchestration.py` 6483→6369; `cri_instruction_resource.py` −51.
- Suíte `delia-api` completa: PASS (exit 0). RQ-08..11 (G3) = PARTIAL → cobertura ~18%.
- E01–E10: TEST_NOT_RUN (G7).

## 14. G4 — resíduos G3 fechados (R1-R3, doc 260); G4 scope iniciado

- **R1**: restaurada cobertura negativa de privacidade/observabilidade
  não-CRI em `test_turn_observability.py` — `test_projection_is_bounded_
  and_never_carries_payload` (sem prompt/secret na wire, bounds de
  model-id) + `test_composition_elapsed_accumulates_honestly` (split
  model/operational/composition/other honesto).
- **R2**: `test_clarification_applies_with_partial_evidence_and_unmet_
  obligations` agora usa terminal com outcome+provenance/SourceRef
  REAIS e asserta preservação dos campos — não apenas o marker.
- **R3**: comentário stale CRI em `orchestration.py` ~260 removido.
- **R5**: RQ-08/09/10 = G3 (PARTIAL); RQ-11 mantido em G4.
- Suíte completa PASS (exit 0). Escopo G4 principal em análise.

## 15. G4 — retries/config/observability (execução, fatia principal)

- **M1 retries**: `Agent.run_sync` executa UMA vez por attempt
  (pydantic_ai_investigation:1136) — `call_retry_eligible` NÃO envolve o
  Agent path → zero multiplicação. `governed_retries`
  (llm_call_max_attempts, clamp≤3, códigos recoverable) permanece para
  os paths separados: call conversacional (handle_interactive_turn:1592)
  e model-stage (orchestration:5006). Retries nativos do Agent
  (tool retries + ModelRetry output) bounded por UsageLimits.
  Teste: 1 call site run_sync + zero call_retry_eligible no módulo.
- **M3 dead config/args**: `_recovery_reuse_enabled` (ctor arg órfão —
  "retained; ledger removed") e `last_agent_usage` (estado set, sem
  leitor) removidos de pydantic_ai_investigation + root_composer.
- **M2 tokens**: `_map_usage` lê usage do provider
  (input_tokens/request_tokens, output_tokens/response_tokens) —
  `estimated_input_tokens` permanece rotulado ESTIMATIVA na
  ModelCallObservation; separação provada em testes existentes.
- **KEEP**: ModelInvocationPort/InvokeModel (C3-T4 + conversacional),
  governed_retries (paths não-Agent), context_budget (proteção
  pre-call), JSON único (perfis completos, zero campos mortos),
  last_node_trace (consumido em testes de observabilidade).
- Suíte completa PASS (exit 0).

## 16. G4 rework — telemetria + prova comportamental de retries (doc 262)

- **last_agent_usage**: remoção completada — o `else:` órfão (atribuição
  dinâmica no sucesso do run_sync) e `started` removidos; zero leitores
  confirmado por grep. Tokens do Agent path não tinham consumidor de
  observabilidade (campo nunca lido) — `ModelCallObservation` continua
  sendo o ledger autoritativo dos paths InvokeModel.
- **M1 prova comportamental**: 3 testes instrumentados com
  FunctionModel — 1 chamada física por run; ModelRetry → +1 retry
  nativo bounded; UsageLimits(request_limit=1) → UsageLimitExceeded
  sem 2ª chamada. Não-inspeção-textual: mede chamadas reais.
- Suíte completa PASS (exit 0).
- RQ-11=PARTIAL (consolidation bounded), RQ-12=PARTIAL (runtime único
  provado), RQ-13=PARTIAL (JSON único KEEP, zero campos mortos),
  RQ-14/15=NOT_IMPLEMENTED (G5+).

## 17. G5 — MCP/OpenAPI/snapshot boundary (execução)

- **Snapshot**: experimento APROVADO e deployado
  (DELIA_MCP_CATALOG_MODE=snapshot_experiment no srv-api +
  /data/delia/mcp_catalog.db) — NÃO aposentado. Boundary violation
  corrigida: `snapshot_interop.py` (application) não importa mais
  `infrastructure/mcp/catalog_store` — `_SnapshotCatalogStore`
  Protocol estrutural + `contract_hash` injetado via construtor;
  composition (root_composer) constrói o adapter infra e injeta.
  9/9 testes snapshot PASS.
- **OpenAPI C3-T5**: foundation aprovada intacta
  (`openapi_provider.py` + `infrastructure/openapi/` — capability
  catalog adapter + http invoker + source loader; 46 testes PASS).
  Direct DELPI adapter já aposentado anteriormente
  (DELIA_OPENAPI_TIMEOUT_SECONDS removida — comentário em settings).
  KEEP — não excluído por ausência de wiring em produção.
- **MCP live**: zero dead symbols em specialist_interop.py,
  specialist_interop_port.py, mcp/adapter.py, mcp/transport.py,
  delegation.py — todos consumidos. KEEP integral; discovery!=FACT,
  AuthZ/gates preservados.
- Suíte completa PASS (exit 0).

## 18. G6 — streaming STT governado (execução)

- `stream_transcribe` (openai_compatible_transcription_adapter.py) usava
  `requests.post` cru — sem `deadline_scope`: DNS/connect/TLS e reads
  SSE não governados; stall mid-stream só limitado por inactivity
  timeout, nunca pelo deadline absoluto. Corrigido: `self._http_post`
  (deadline_http_post governado) dentro de `with deadline_scope(deadline)`
  cobrindo post + iteração SSE — trickling provider não estica o
  deadline; erros mapeados (BoundedHttpTimeout/Timeout→PROVIDER_TIMEOUT,
  Transport/RequestException→PROVIDER_UNAVAILABLE).
- Testes: 4 casos SSE migrados para injeção `http_post` (design do
  adapter) — sem patch de requests.post; +2 testes novos
  (governed transport + timeout→PROVIDER_TIMEOUT).
- Preservado: deadline total, size limits, cancelamento, SSE parcial,
  auth/privacy, byte-line UTF-8, port de transcrição, bounded_request
  no path não-streaming. Zero segundo transporte.
- Suíte completa PASS (exit 0).

## 19. G7 — verificação integrada (execução, fatia executável)

- **G6 residual (doc 265 §1-2)**: 4 testes REAIS com servidor HTTP local
  (trickle, stall mid-stream, UTF-8 split, lifecycle pós-fechamento) —
  DEFEITO REAL encontrado: stall mid-stream disparava erro de transporte
  mapeado como `provider_unavailable`; corrigido para `provider_timeout`
  quando a falha ocorre no/após o deadline (timeout honesto). Response
  streaming lê normalmente após fechamento da Session (prova).
- **G4 engine real**: 2 testes instrumentados no
  PydanticAiInvestigationOrchestrator + gates reais — 2 requests físicos
  por attempt (tool call + final_result), 1 invocação governada por
  capability, zero multiplicação externa.
- **E01–E10**: TEST_NOT_RUN — requer delpi-delia-api + Keycloak +
  owners MCP no ambiente autorizado (harness doc243_e_matrix_probe.py
  existe, env ausente). Sem mock apresentado como avaliação real.
- **Segurança**: G2 negatives (15) + MCP fail-closed + snapshot (9) +
  OpenAPI C3-T5 (46) + STT streaming (4 reais) — preservados.
- Suíte completa PASS (exit 0).
