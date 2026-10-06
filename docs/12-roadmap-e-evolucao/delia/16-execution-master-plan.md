# DÉLIA — Plano Mestre Executável

**Status:** planejamento executável canônico  
**Autoridade de ordem:** **este documento é a única fonte de verdade para a sequência de implementação**  
**Produto:** **DÉLIA**, aplicação standalone nova  
**Próxima etapa:** `ARCH-DRIFT-DELIA-GENERIC-MCP-MULTISTEP-ORCHESTRATION-R1` = `IN_EXECUTION` (§6.140) — correção dos gaps genéricos provados por `ARCH-DIAG-DELIA-GENERIC-MCP-RUNTIME-WSL-SSH-01` (`ANALYSIS_GENERIC=PARTIAL`, `ANALYSIS_TO_PREPARE_GENERIC=FAIL`, `WRITE_POLICY_GENERIC=PARTIAL`): `SpecialistOperationClass.ANALYSIS` first-class (sem collapse para READ; outcome permanece OBSERVATION), step RESOLVER genérico same-owner (DISCOVERY|READ|ANALYSIS resolve input faltante do target — nome→id; ambiguidade → `CLARIFICATION_REQUIRED` com candidatos bounded; id não presente na evidência owner = fail-closed), continuação bounded `ANALYSIS→PREPARE` (nunca ACT direto; máx. 3 steps: `DISCOVERY→TARGET|RESOLVER→TARGET|DISCOVERY→RESOLVER→TARGET|ANALYSIS→PREPARE|DISCOVERY→ANALYSIS→PREPARE`), política de escrita 100% estrutural (`confirmation_requirement.explicit_user_confirmation` selado no PREPARE do owner = única autoridade; branch `ops[]`/catálogo VISTA removido; ausente/malformado/contraditório → `WRITE_REJECTED owner_policy_invalid`), proposal handle opaco backend-only (confirmação renderiza só a projeção determinística do preview). Sem branches por nome de owner/tool; sem catálogo local; zero mudança owner-side. `ARCH-DRIFT-MCP-OWNER-FULL-CAPABILITY-INTELLIGENCE-SURFACE-01` = `IN_EXECUTION` (§6.133, owner-side) — VISTA como primeiro reference owner completo: superfície MCP 9 tools (5 READ + 1 DISCOVERY + 1 ANALYSIS `preview_data_block` + PREPARE + ACT), owner quality loop dentro do candidato PREPARE (correções determinísticas seguras sobre issues introduzidas; op canônica `apply_safe_layout_fixes` para correção explícita; low_contrast context-aware via `safe_contrast_color`/`minContrastPairs` — nunca `#ffffff` fixo), `safeFixesApplied` como evidência. `ARCH-DRIFT-DELIA-WRITE-CONFIRMATION-AND-OWNER-VOCABULARY-01` = CLOSED (§6.132, live prod PASS). `ARCH-DRIFT-MCP-FULL-CAPABILITY-ORCHESTRATION-03` = `IN_EXECUTION` — implementação deployada e verificada em produção: catálogo vivo + leg de leitura PROVEN (§6.127); DEFECT-1/2 (argumentos JSON-string/aninhados) e DEFECT-3 (seleção VISTA) corrigidos em §6.128 — PREPARE lifecycle PROVEN end-to-end no wire real, VISTA list GROUNDED 2/2; defeito de contrato owner TÉO (`commit_now` alcançável via MCP PREPARE) corrigido owner-side em `ARCH-DRIFT-TEO-MCP-PREPARE-ACT-CONTRACT-01` (§6.129) — MCP PREPARE puro, `PREPARE != ACT` enforced no adapter boundary. Próximo passo: revisão independente `ARCHITECTURE_REVIEW_ARCH_DRIFT_MCP_FULL_CAPABILITY_ORCHESTRATION_03` — implementação pronta para revisão. `ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02` = `ACCEPT_CURRENT_READ_SCOPE` — `ARCHITECTURE_REVIEW_..._02R3` = `ACCEPT` e `ARCHITECTURE_REVIEW_DELIA_GROUNDED_BUSINESS_PRESENTATION_01` = `ACCEPT` (§6.124; evidência §§6.118–6.123, implementation SHA `ff27cfaf47`). Canonical current state: `SPECIALIST_CAPABILITY_CATALOG_OWNER=SPECIALIST` (live authenticated `tools/list` = primary capability surface; no DÉLIA-local tool mirror); `APPROVED_SPECIALISTS=DAVI|TEO|VISTA`; `MCP_READ_FEDERATION=ACCEPTED_CURRENT_SCOPE`; `LIVE_HUMAN_VERIFICATION_DAVI/TEO/VISTA=PASS` (VISTA corrigido em §6.128; `FAIL_SELECTION` histórico §6.127 DEFECT-3); `PRODUCTION_MCP_RUNTIME=READ_PREPARE_SLICE_PROVEN_ON_CURRENT_SHA`; `DEPLOYED_DELIA_SHA=9f859adb71ddbef8fcaaffe5c0a81510e086626f` (§6.128); `DEPLOYED_TEO_SHA=2d25a0f9e0bfa4b2b20f0fe53032fa711aa22772` (§6.129); `TEO_MCP_PREPARE_CONTRACT=PURE_PREPARE_PROVEN`; `TEO_MCP_PREPARE_MATERIAL_WRITE=NONE`; `TEO_MCP_ACT=commit_proposal`; `PREPARE_ACT_SEPARATION=PASS`; `DELIA_ROLE=OPERATIONAL_CAPABILITY_ORCHESTRATOR; MCP=CAPABILITY_PROVIDER_FAMILY (provider-neutral per ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-ORCHESTRATION-01/R1); `DELIA_LOCAL_MCP_CAPABILITY_CATALOG=FORBIDDEN` (`DELIA_LOCAL_READ_CAPABILITY_LIST=NONE`, `DELIA_LOCAL_WRITE_CAPABILITY_LIST=NONE`, `DELIA_LOCAL_PREPARE_ACT_PAIR_REGISTRY=NONE`, `PER_CAPABILITY_ENABLE_FLAGS=FORBIDDEN`); target invocable classes `DISCOVERY|READ|ANALYSIS|PREPARE|ACT` (ANALYSIS first-class desde §6.140 — non-mutating, outcome = OBSERVATION, pode alimentar PREPARE via continuação bounded; nunca ACT direto) (`MCP_PREPARE`/`MCP_ACT` = `GOVERNED_INVOKABLE_CURRENT_SCOPE` política — `MCP_PREPARE_LIVE=PROVEN` (§6.128 lifecycle completo); `MCP_ACT_LIVE=CONFIRM_POSITIVE_NOT_PROVEN_BY_DESIGN` (mutação real não autorizada para teste); `UNREACHABLE_DEFECT_1_2` histórico §6.127; `NON_MCP_C5_WRITE_FAMILIES=NOT_AUTHORIZED`); `GOVERNED_WRITE_BINDINGS`/`write_binding_for`/`GovernedWriteBinding` static binding model = SUPERSEDED_AS_TARGET (C5 governance concepts reusable — §6.126); `ARCHITECTURE_REVIEW_C5_GOVERNED_WRITE_FOUNDATION_01` SUPERSEDED (foundation review target replaced by the full-orchestration decision); `REAL_PRODUCTION_APPLY=PASS_FOR_CURRENT_MCP_READ_SCOPE`; `NON_MCP_PREPARE=BLOCKED`; `NON_MCP_ACT=BLOCKED`; `UNKNOWN=discoverable_never_invocable`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO` at phase level (bounded MCP read federation slice only — Graph/Semantic/Sandbox/Predictive families remain unopened); `C5_AUTHORIZED=NO`; `PRODUCTION_READINESS=NOT_PROVEN`. SUPERSEDED as current status (historical evidence preserved): `C4-MCP-GOVERNED-READS-01/02` bounded per-tool slices (§6.104/§6.106), `THIRD_MCP_GOVERNED_READ=NOT_AUTHORIZED`, `DELIA_C4_*_ENABLED` per-capability flags — all superseded by `ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02`. Earlier states `PRODUCTION_MCP_RUNTIME=NOT_PROVEN` and `REAL_PRODUCTION_APPLY=TEST_NOT_RUN` were true at their record dates and remain historical. Review pendente independente: `ARCHITECTURE_REVIEW_ARCH_DRIFT_MCP_FULL_CAPABILITY_ORCHESTRATION_03` — evidência de implementação registrada em §6.126–§6.129; DEFECT-1/2/3 corrigidos (§6.128) e defeito de contrato owner corrigido (§6.129); implementação pronta para revisão. `ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01=ACCEPT_WITH_RESIDUAL` (§6.112). `GROUNDED_BUSINESS_PRESENTATION=PASS` — deterministic business-payload projection proven live on production SHA `ff27cfaf47` (§6.123). `PROD-MCP-RUNTIME-ALIGNMENT-01` KC24 binding decision preserved (§6.116: prod stays on Keycloak 24.x, `PROD_TOKEN_EXCHANGE_MODE=KC24_LEGACY_V1`, KC26 migration deferred).
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Bootstrap:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Thematic architecture:** `53–66`  
**DoD:** [`14-definition-of-done.md`](./14-definition-of-done.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Decisão de execução

A DÉLIA será construída do zero como aplicação independente.

```text
PROIBIDO
→ evoluir minha-delpi-ai-api para virar DÉLIA
→ evoluir plugins/minha-delpi-chat para virar DÉLIA
→ esperar correções/refactors do Chat para continuar DÉLIA
→ compartilhar tabelas/runtime do Chat como foundation

OBRIGATÓRIO
→ nova API da DÉLIA
→ novo MFE da DÉLIA
→ migrations próprias
→ manifesto próprio
→ Gateway/Compose próprios
→ deploy/rollback próprios
→ integração normal com Portal/Core/Keycloak/APIs
```

Freeze C0.S1 aceito (`PLANNED / FROZEN_ACCEPTED`; `ARCHITECTURE_REVIEW_C0_S1`, `REVIEWED_HEAD=c822f0e72495256c3459a4b36b9c37a3bba95cbb`; ver `68`): `delia-api/`, `plugins/delia/`, containers `delpi-delia-api` / `delpi-delia`, paths `/apps/delia-api/` e `/apps/delia`. Tokens `minha-delpi-copilot*` são `SUPERSEDED`/`HISTORICAL` como target ativo; “Copilot” não é o nome de produto.

O Chat é apenas sistema vizinho/referência durante inventário.

## 2. North Star de execução

A DÉLIA deixa de ser apenas request/response e deve evoluir de forma foundation-first para:

```text
PERCEBER
→ ENTENDER
→ PESQUISAR
→ ANALISAR
→ PREVER/SIMULAR
→ DECIDIR
→ PREPARAR/EXECUTAR
→ VERIFICAR OUTCOME
→ COMUNICAR
→ APRENDER SOB GOVERNANÇA
```

E deve operar sobre:

```text
pessoas / Portal / Meeting / Frontline
+ Domain APIs / ERP / MES / qualidade / manutenção
+ Internet / External Connectors / Teams
+ Events / Watches / Process Intelligence
+ Semantic Business Layer / Business Graph
+ Analysis Sandbox / Artifact Workspace
+ Predictive/Prescriptive Intelligence / Operational Twin
+ Automation & Execution Hub
+ Edge/Offline runtime governado
+ MCP/A2A integrations
+ Personal Memory
+ AI Control Tower / Model Lifecycle / Marketplace
```

## 3. Authorities documentais

```text
16 = ordem/dependências
17 = ownership/contracts
20 = tests/gates
21 = state/persistence
25 = CP requirements
49 = code architecture/design patterns
50 = standalone product boundary
51 = factual platform baseline
52 = repository/bootstrap target
53 = multimodal/Meeting/Frontline/industrial
54 = biometric identity/Human Observation
55 = Internet Research/external connectors
56 = Microsoft Teams
57 = event-driven autonomous operations/Automation Hub
58 = Process Intelligence/Process Mining
59 = AI Control Tower
60 = MCP/A2A/tool interoperability
61 = Personal Memory/Personalization
62 = Semantic Business Layer
63 = Analysis Sandbox/Artifact Workspace
64 = Predictive/Prescriptive Intelligence/Operational Twin
65 = Edge/Offline Industrial DÉLIA
66 = AI Model Lifecycle/Capability Marketplace
ledger = execution evidence/status
```

Nenhuma spec temática cria ordem, permission authority ou runtime paralelo.

## 4. Invariantes

1. API/MFE/persistence/deploy da DÉLIA são próprios e independentes do Chat.
2. Core/Keycloak/Portal/Domain APIs mantêm suas authorities atuais.
3. Business Actions são OpenAPI-first; planner não hardcoda endpoint/provider/executor.
4. `EntityRef/SourceRef/EvidenceRef/OutcomeRef/EventEnvelope/Workflow/Decision` são foundations compartilhadas antes de feature-specific types.
5. Graph referencia relações; Semantic Layer define significados/métricas; nenhum deles substitui systems of record.
6. Conversation history, Personal Memory, Organizational Knowledge e WorkspaceContext são estados distintos.
7. Internet/external/tool/agent/media content é untrusted data.
8. Provider/tool/agent/model/package metadata nunca concede RBAC/domain/provider authority.
9. Read != write; draft != send; recommendation != authorization; simulate != apply; PREPARE != ACT.
10. Technical executor success != verified business Outcome.
11. Event payload nunca concede autorização nem side effect por si só.
12. Autonomia é capability/context/risk scoped; L5 OFF por default.
13. API autoritativa é preferida a RPA/computer-use quando existir contrato suportado.
14. RPA/computer-use são executors; business rules/decisions não moram no bot.
15. Nem todo evento chama LLM; FAST/OPERATIONAL/REASONING são paths diferentes.
16. Readiness material usa fatos/regras determinísticas quando disponíveis.
17. Process Mining mede processo; não vira worker-surveillance/profile engine.
18. Human Observation não infere personalidade, honestidade, emoção como verdade, saúde ou valor profissional global.
19. Biometria não autentica/autoriza por si só.
20. Personal Memory é user-owned/private por default e não vira Organizational Knowledge automaticamente.
21. Semantic metric possui owner/version/formula/grain/freshness; LLM não inventa KPI material.
22. Sandbox é isolado, bounded e read-only por default.
23. Artifact possui provenance/version/ACL e não sobrescreve silenciosamente edição humana.
24. Prediction != FACT; model output sozinho não autoriza ACT.
25. Operational Twin/scenario state != production state.
26. Edge/offline nunca amplia authority por perda de conectividade.
27. MCP/A2A server/agent é integração aprovada; não um novo core de inteligência.
28. Control Tower governa assets/risco/health/cost/kill switches; não concede business permission.
29. Model/Marketplace lifecycle é versionado/revogável; instalação não concede permission.
30. Edge/model/package deployment exige version/health/rollback/revoke.
31. DÉLIA não é safety controller; autonomia empresarial não implica OT actuation.
32. Chain-of-thought não é persistida/exposta.
33. Specs `31/45/46/47` permanecem reference-only/superseded.
34. `schedule != permission`; timer/recurrence nunca substitui live Core/domain AuthZ, Policy ou Decision.
35. Recurring Governed Work temporal é distinto de Watch; C5 L4 bounded não implica Watch autonomous ACT/C7 L5.

## 5. Grafo canônico C0–C7

```text
C0 — Platform + Architecture + Privacy/Security/Data/Automation/AI Foundations Freeze
↓
C1 — Standalone Application Bootstrap
↓
C2 — Portal + Operational Context + Platform Commands
↓
C3 — Intelligence Core + Capability Foundations
↓
C4 — Governed Reads + Graph/Semantics/Analysis/Predictive Discovery
↓
C5 — Governed Writes + Executors + Durable Work + Artifacts/Prescriptive Prepare
↓
C6 — Product Work + Process Intelligence + Control Tower + Meeting/Frontline + Ecosystem
↓
C7 — Advanced Autonomy + Operational Twin/Edge/Marketplace/Optimization + Scale/Rollout
```

---

# C0 — Foundation Freeze

## C0.S0 — Rebaseline factual do monorepo e infraestrutura

Antes de qualquer runtime diff:

```text
git status
git rev-parse HEAD
```

Inventariar com arquivo/símbolo/contrato/owner/consumer/evidence.

### Portal / Core / Gateway / Infra / MFEs / APIs

Revalidar todo o baseline já descrito em `51`: auth/Keycloak/Core `/me*`, AppHost/Module Federation/plugin-ui, manifests, routing, Gateway/Compose dev-prod, storage/secrets/network, API/OpenAPI/auth/errors/idempotency/events, notifications/rooms/requests/workers/schedulers, media/device/shared-terminal patterns e Chat reference-only.

### Media / Biometric / Meeting / Frontline

Seguir `53/54`: providers, capture/storage/retention, devices, corporate photo/voice sources, enrollment/templates/liveness, participant/presence, Human Observation owner e OT safety boundaries.

### Internet / External / Teams

Seguir `55/56`: egress/search/safe fetch, OAuth/vault, Microsoft/Google/WhatsApp/Slack/GitHub, webhook/subscription/reconciliation, attachments, Entra/Graph/Teams scopes/artifacts/apps/events/meeting privacy.

### Automation / Event-Driven Operations

Seguir `57` e mapear:

```text
RPA products/licenses/orchestrators/bots/packages
scripts/functions/jobs
queues/workers/heartbeats/leases
schedulers/timers/cron/polling/event sources/brokers/topics
recurring job/work definitions and their owners
timezone/DST/calendar semantics
misfire/missed-run/reconciliation behavior
overlap/concurrency semantics
service accounts/background identities
credential injection/storage
VDI/desktop/session infrastructure
existing rule/decision/process engines
postcondition/outcome verification sources
notification/escalation channels
kill switches/emergency stop
support/SLA/ownership
```

O inventário deve separar explicitamente **RecurringWorkDefinition/Work ownership** do **timer/scheduler físico**. A existência de scheduler na plataforma não transfere Work/Policy authority para ele; a ausência de scheduler provado não autoriza criar um novo antes do Abstraction Gate.

### Process Intelligence

Seguir `58` e mapear:

```text
event logs/audit trails
case/business keys
activity/timestamps/statuses
existing BPMN/process docs
process owners
process KPIs
historical completeness/quality
task-mining/desktop telemetry tools/policies
```

### AI Control Tower / Model Governance

Seguir `59/66` e mapear:

```text
AI/model/automation inventories
provider accounts/contracts
model registries/MLOps
prompt/policy/asset registries
eval suites/datasets
cost/usage telemetry
feature flags/kill switches
incidents/change management
package/catalog/signing/supply-chain controls
```

### MCP / A2A / Tool Interoperability

Seguir `60` e mapear MCP clients/servers, agent frameworks/protocols, tool registries, delegation identities/tokens, approved external agents, network boundaries e protocol/security versions.

### Personal Memory / Personalization

Seguir `61` e mapear Core/user profile fields, favorites/recent usage/preferences, notification settings, memory-like stores, privacy/retention/export/delete owners e shared-device constraints.

### Semantic Business Layer

Seguir `62` e mapear KPI formulas, BI semantic models, business glossary, Power BI/warehouse/lake/SQL definitions quando existirem, owners, dimensions/grain/freshness e conflicting definitions.

### Analysis Sandbox / Artifact Workspace

Seguir `63` e mapear Python/Jupyter/code execution, containers/sandbox, BI/query engines, file scanning/object storage, document/spreadsheet/presentation generation, collaboration/versioning/export/share policies.

### Predictive / Prescriptive / Operational Twin

Seguir `64` e mapear forecasting/anomaly/optimization models, datasets/ground truth, simulation/twin tools, MES/IoT/historian, planning/capacity models, solvers e current manual what-if models.

### Edge / Offline Industrial

Seguir `65` e mapear factory network reliability, Edge platforms/gateways, devices/MDM, GPU/NPU/CPU, local storage/inference, procedure/drawing distribution, time sync, offline continuity, OT segmentation.

### C0.S0 classification

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
COPILOT_IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE
```

`COPILOT_IMPLEMENT_NEW` permanece como `LEGACY_TOKEN` de planejamento; não representa o nome do produto nem o path físico ativo (`delia-api` / `plugins/delia`).

Nenhuma capability/fornecedor/ferramenta é considerada existente sem evidence.

### Saídas obrigatórias C0.S0

- factual platform/API/MFE/infra inventory;
- ownership/contracts map;
- media/biometric/device/privacy inventory;
- external/Teams/OAuth/egress inventory;
- automation/RPA/event/workers/service-identity inventory;
- recurring Work/scheduler inventory com owner físico, timezone/DST, misfire/overlap, background identity e revoke semantics;
- process event-log/process-owner inventory;
- AI/model/tool/agent/Control-Tower inventory;
- memory/personalization inventory;
- semantic metric/glossary inventory;
- sandbox/artifact infrastructure inventory;
- predictive/twin/Edge inventory;
- OT safety inventory;
- `51` revalidated;
- ledger HEAD/evidence.

**Sem runtime diff da DÉLIA.**

## C0.S1 — Product boundary / nomes / physical ownership

Congelar API/MFE/service/container/path/manifest/DB ownership, admin/callback/webhook paths e decidir, por evidence/ADR, se Automation Hub, Control Tower, Process Intelligence, Sandbox, Semantic Layer e Edge são módulos da API da DÉLIA, neutral shared services ou adapters — **sem criar microservice por nome de feature**.

**C0.S1-T1 (histórico):** freeze candidato persistido nas authorities (`68`/`50`/`17`/`52`/`21`/`25`/ledger), então `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Esse estado foi superseded pelo review abaixo; não apagar história.

**C0.S1-T2 — PERSIST_ARCHITECTURE_REVIEW_DECISION:** `ARCHITECTURE_REVIEW_C0_S1` sobre `REVIEWED_HEAD=c822f0e72495256c3459a4b36b9c37a3bba95cbb`, `VERDICT=ACCEPT_WITH_RESIDUAL`, `C0.S1=APPROVED`, `C0.S2_AUTHORIZED=YES`, `BLOCKERS=NONE`. `FOUNDATION_FREEZE=NOT APPROVED`, `PROGRAM=PLANNED / NOT_STARTED`, `C0=NOT_STARTED`, `DÉLIA_RUNTIME_DIFF=NONE`. Residual de naming/evidence de HEAD é não bloqueante; labels semânticos “Copilot” residuais em `25` são cleanup terminológico não bloqueante. **Nenhuma execução C0.S2 ocorre nesta tarefa.**

```text
C0.S0 = APPROVED
C0.S1 = APPROVED
C0.S2 = APPROVED
C0.S3 = APPROVED
C0.S4 = APPROVED
C0.S5 = APPROVED
C0.S6 = APPROVED
C0.S7 = APPROVED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED
FOUNDATION_FREEZE = APPROVED
C1_AUTHORIZED = YES
C1_STARTED = YES
C1_EXECUTED = NO
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
RUNTIME_READINESS = NOT_PROVEN
PRODUCTION_READINESS = NOT_PROVEN
NEW_BEHAVIORAL_TESTS = TEST_NOT_RUN
FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED = YES
DÉLIA_RUNTIME_DIFF = delia-api + plugins/delia MFE + delpi.manifest.json
NEW_RUNTIME_ABSTRACTIONS = PlatformAccessPort / CorePlatformAccessAdapter / PlatformAccessContext
JWT_VALIDATION = PASS
CORE_CONTEXT = PASS (contract/adapter; live Core TEST_NOT_RUN)
MFE_FOLDER_INDEPENDENT = PASS
FEDERATED_MOUNT = PASS
PLUGIN_UI = PASS
OWN_MANIFEST = PASS (C1-T4/T4D1)
BOOTSTRAP_VISIBILITY_PERMISSION = delia.access
BOOTSTRAP_VISIBILITY_PERMISSION_DECISION = APPROVED
CORE_REGISTRATION = PASS (C1-T6)
DELIA_ACCESS_EFFECTIVE_RBAC = PASS (C1-T6 positive+negative)
ME_APPS_DISCOVERY = PASS (C1-T6)
PORTAL_LIVE_MOUNT = PASS (C1-T6)
OWN_MIGRATION_CHAIN = NOT_APPLICABLE_AT_C1 (C1-T6D1 Product Master; no DÉLIA-owned persisted state)
ARCHITECTURE_DECISION_REQUIRED = NONE (migration applicability resolved)
C1_EXECUTED = YES
C1_BOOTSTRAP_ACCEPTANCE = ACCEPT_WITH_RESIDUAL (C1-FINAL)
C1_BOOTSTRAP_RUNTIME_READINESS = PROVEN (bootstrap scope)
RUNTIME_READINESS = PROVEN (C1 standalone bootstrap only)
PRODUCTION_READINESS = NOT_PROVEN
C2_AUTHORIZED = YES
TYPESCRIPT_ISOLATED = INCONCLUSIVE (NON_BLOCKING_RESIDUAL)
CORE_CONTEXT_LIVE_NETWORK = TEST_NOT_RUN (NON_BLOCKING; formal CORE_CONTEXT=PASS; T6 proved live Core governance path)
C2_T1 = INVENTORY_FREEZE_READY_FOR_REVIEW
C2_T2 = VERIFICATION_EVIDENCE_READY_FOR_REVIEW
C2_T3 = DEPENDENCY_FREEZE_READY_FOR_REVIEW
C2_T4 = OPERATIONAL_CONTEXT_INVENTORY_READY_FOR_REVIEW
C2_T4R1 = STATUS_NORMALIZATION_READY_FOR_REVIEW
C2_T5 = IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
C2_T5R1 = IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
C2_T5R2 = LIVE_GLOBAL_SURFACE_FAIL_BUNDLE_CONTAINS_T5
C2_T5R3 = IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
C2_T5R3R1 = ACCEPTED_CURRENT_SCOPE
C2_T6 = ACCEPTED_WITH_OWNER_SECURITY_FOLLOWUP
C2_T6R1 = ACCEPTED_WITH_RESIDUAL
C2_PREFINAL_R1 = ACCEPT
C2_FINAL = ACCEPT_WITH_RESIDUAL
C2_STARTED = YES
C2_IMPLEMENTATION_STARTED = YES
C2_EXECUTED = YES
C2_PORTAL_SURFACE_READINESS = PROVEN_CURRENT_SCOPE
C3_AUTHORIZED = YES
C3_STARTED = YES
C3_EXECUTED = NO
C3_T1 = APPROVED
EVIDENCE_EPISTEMIC_SEMANTICS = FROZEN_ACCEPTED
SOURCE_LINKAGE_SEMANTICS = FROZEN_ACCEPTED
C3_T2_AUTHORIZED = YES
C3_T2 = APPROVED
C3_T3 = APPROVED
C3_T4 = APPROVED
C3_T5_AUTHORIZED = YES
C3_T5_EXECUTED = NO
PRODUCTION_READINESS = NOT_PROVEN
PORTAL_HOST_CONTRACT = FROZEN_ACCEPTED (current AppHost props; ≠ business AuthZ)
OPERATIONAL_CONTEXT = TO_INVENTORY
OP = PROVEN
PRODUCT = PROVEN
OPERATION = PROVEN
MACHINE = TO_INVENTORY
POSTO = TO_INVENTORY
WORK_CENTER = PROVEN
WORK_CENTER_ROLE = RELATED_CONCEPT_NOT_CP159_IDENTITY
WORKSPACE_CONTEXT_RUNTIME_STATUS = DEFER
BROWSER_STATE_RESIDENCY_POLICY = APPROVED (C2-T1D1)
BROWSER_RETAINED_STATE_CURRENTLY_REQUIRED = NO
CENTRALIZED_BROWSER_STATE_BOUNDARY = REQUIRED_ON_FIRST_RETAINED_STATE
SHARED_DEVICE_ISOLATION_INVARIANT = FROZEN_ACCEPTED
NEXT = ARCHITECTURE_REVIEW_C3_T7
```

C3 initial bounded DAG (Coordination-approved dependency order; not the numbered foundation inventory):

```text
C3-T1 Evidence / epistemic semantics + source linkage = APPROVED (21 §4B; ARCHITECTURE_REVIEW_C3_T1 ACCEPT_WITH_RESIDUAL)
→ C3-T2 Evidence epistemic domain model + conformance = REWORK (ARCHITECTURE_REVIEW_C3_T2; historical)
→ C3-T2R1 rework = APPROVED (ARCHITECTURE_REVIEW_C3_T2R1 ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=d444e75f7)
→ C3-T3 Minimal Model Invocation + Eval/Lineage Foundation = APPROVED (ARCHITECTURE_REVIEW_C3_T3R1 ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=2ba28950e)
→ C3-T4 Structured Understanding Vertical Slice = APPROVED (ARCHITECTURE_REVIEW_C3_T4R1 ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=89bb5ad352)
→ C3-T5 OpenAPI Action Catalog + Capability Projection = APPROVED (ARCHITECTURE_REVIEW_C3_T5 ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=84c249bee0)
→ C3-T6 Expertise / Knowledge Governance + Retrieval Contracts = APPROVED (ARCHITECTURE_REVIEW_C3_T6R1 ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=1a49e501fb)
→ C3-T7R1 rework: duplicate capability_id fail-closed + evidence rebind = APPROVED (ARCHITECTURE_REVIEW_C3_T7R1 ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=d49f77c966cd03387dd3e8e268cb9be5e2098ab6)
→ C3-T8 Conversation / Session Interaction Foundation (APPROVED; ARCHITECTURE_REVIEW_C3_T8=REWORK closed by C3-T8R1; ARCHITECTURE_REVIEW_C3_T8R1=ACCEPT_WITH_RESIDUAL; IMPLEMENTATION_HEAD=22b4aef60626cbf4f0f822a0972053f113f2ab71)
→ C3-T8 Conversation / Session Interaction Foundation
EVIDENCE_BEFORE_MODEL = YES
EVIDENCE_BEFORE_PLANNER = YES
EVIDENCE_BEFORE_INTELLIGENT_CONVERSATION = YES
EVIDENCE_BEFORE_RAG_KNOWLEDGE_RUNTIME = YES
EVIDENCE_EPISTEMIC_SEMANTICS = FROZEN_ACCEPTED
SOURCE_LINKAGE_SEMANTICS = FROZEN_ACCEPTED
C3_STARTED = YES
C3_EXECUTED = NO
C3_T2 = APPROVED
C3_T3 = APPROVED
C3_T3_AUTHORIZED = YES
C3_T3_EXECUTED = NO
C3_T4 = APPROVED
C3_T4_AUTHORIZED = YES
C3_T4_EXECUTED = NO
C3_T5 = APPROVED
C3_T5_AUTHORIZED = YES
C3_T5_EXECUTED = NO
C3_T6_AUTHORIZED = YES
C3_T6 = APPROVED
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
C3_T7 = APPROVED
```

## C0.S2 — Authorities / bounded contexts

Congelar owners para:

```text
identity/RBAC
business/domain data
conversation/intelligence
Knowledge/Memory
Evidence
Graph/Semantics
Media/Biometric
External/Teams
Process Intelligence
Decision/Autonomy
Durable Work
Recurring Governed Work / scheduling definition
Automation/Executors
Analysis/Artifacts
Predictive/Twin
Edge
MCP/A2A interoperability
Model Lifecycle/Marketplace
Control Tower
OT safety
```

Timer/scheduler físico é boundary de infraestrutura/execution a ser atribuído ao owner provado; não vira owner do Work da DÉLIA nem permission authority.

**C0.S2-T1 (histórico):** freeze candidato persistido em `17` §§2.3–2.6 + ledger §6.24, então `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Esse estado foi superseded pelo review abaixo; não apagar história.

**C0.S2-T2 — PERSIST_ARCHITECTURE_REVIEW_DECISION:** `ARCHITECTURE_REVIEW_C0_S2` sobre `REVIEWED_HEAD=8bae12a250f2362603211a93c65bb098b8b1e9aa`, `VERDICT=ACCEPT_WITH_RESIDUAL`, `C0.S2=APPROVED`, `AUTHORITY_MAP=FROZEN_ACCEPTED`, `BOUNDED_CONTEXT_MAP=FROZEN_ACCEPTED`, `C0.S3_AUTHORIZED=YES`, `BLOCKERS=NONE`, `EXECUTION_DRIFT=NONE`, `NEW_RUNTIME_ABSTRACTIONS=NONE`. `FOUNDATION_FREEZE=NOT APPROVED`, `PROGRAM=PLANNED / NOT_STARTED`, `C0=NOT_STARTED`, `DÉLIA_RUNTIME_DIFF=NONE`. **Nenhum design de shared primitive e nenhuma execução C0.S3 ocorre nesta tarefa.**

## C0.S3 — Shared primitives

Decidir/reutilizar foundations antes de types específicos.

**C0.S3-T2 (histórico):** decisões persistidas em `21` §4 + `17` §3 + `25` §17 + ledger §6.26 como `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Esse estado foi superseded pelo review abaixo; não apagar história.

**C0.S3-T3 — PERSIST_ARCHITECTURE_REVIEW_DECISION:** `ARCHITECTURE_REVIEW_C0_S3` sobre `REVIEWED_HEAD=641ffc07284b98ffbdb5e13217ce214c4ad8ebb0`, `VERDICT=ACCEPT_WITH_RESIDUAL`, `C0.S3=APPROVED`, `SHARED_REFERENCE_SEMANTICS=FROZEN_ACCEPTED`, `AUTHORITY_MAP=FROZEN_ACCEPTED`, `BOUNDED_CONTEXT_MAP=FROZEN_ACCEPTED`, `C0.S4_AUTHORIZED=YES`, `BLOCKERS=NONE`, `EXECUTION_DRIFT=NONE`, `NEW_RUNTIME_ABSTRACTIONS=NONE`. `FOUNDATION_FREEZE=NOT APPROVED`, `PROGRAM=PLANNED / NOT_STARTED`, `C0=NOT_STARTED`, `DÉLIA_RUNTIME_DIFF=NONE`. **Nenhuma execução C0.S4 ocorre nesta tarefa.**

```text
REUSED: CorrelationContext, EntityRef, UserRef, ServiceActorRef, DeviceRef,
        SourceRef, EvidenceRef, OutcomeRef, EventEnvelope
CapabilityProjection = PROJECTION_ONLY
ACCEPTED_SHARED: MetricDefinitionRef, ArtifactRef, PredictionRef, ScenarioRef,
                 AutomationExecutionRef, RecurringWorkRef, WorkOccurrenceRef, ModelRef
NOT_PROMOTED: ProcessTraceRef=REFERENCE_ONLY; MemoryItemRef=DOMAIN_LOCAL_ONLY;
              AnalysisRunRef=REJECT; ExecutorRef=DEFER_C0_S5; AIAssetRef=PROJECTION_ONLY;
              EdgeDeviceRef=REUSE DeviceRef
REJECTED_META: UniversalRef / Generic*Ref catalogs
WorkspaceContext = DEFER_TO_CONTRACT C0.S5
```

Timezone/DST/misfire/overlap/retry/background AuthZ/scheduler implementation **não** são C0.S3 — permanecem C0.S4/C0.S5.

## C0.S4 — Architecture / persistence / privacy / safety freeze

Além de `49`, congelar:

- event trust/dedupe/order;
- recurring Work recurrence/timezone/DST/misfire/overlap/idempotency/background-identity/revoke semantics;
- decision-path routing;
- deterministic readiness;
- automation executor selection/idempotency/outcome verification;
- process-log privacy/task mining;
- memory ownership/retention/user control;
- metric semantics/versioning;
- sandbox isolation/egress/quotas;
- artifact lineage/ACL;
- prediction/twin scenario isolation;
- MCP/A2A allowlist/identity/data minimization;
- model registry/eval/deployment/supply chain;
- Edge package/device/offline authority;
- Control Tower risk/assets/kill switches;
- OT no-actuation default.

**C0.S4-T2 (histórico):** decisões persistidas em `21` §4A (+ linkage `25` §18 + ledger §6.28) como `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Esse estado foi superseded pelo review abaixo; não apagar história.

**C0.S4-T3 — PERSIST_ARCHITECTURE_REVIEW_DECISION:** `ARCHITECTURE_REVIEW_C0_S4` sobre `REVIEWED_HEAD=7ac1fb930017bbabb05d8b1654941518f315c6a7`, `VERDICT=ACCEPT_WITH_RESIDUAL`, `C0.S4=APPROVED`, `ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY=FROZEN_ACCEPTED`, `C0.S5_AUTHORIZED=YES`, `BLOCKERS=NONE`, `EXECUTION_DRIFT=NONE`, `NEW_RUNTIME_ABSTRACTIONS=NONE`. `FOUNDATION_FREEZE=NOT APPROVED`, `PROGRAM=PLANNED / NOT_STARTED`, `C0=NOT_STARTED`, `DÉLIA_RUNTIME_DIFF=NONE`. **Nenhuma execução C0.S5 ocorre nesta tarefa.**

## C0.S5 — Integration contracts

Congelar typed contracts para platform/domain/external/event/automation/**recurring-work trigger**/process/model/sandbox/edge boundaries. O contrato deve separar DÉLIA-owned recurring definition/occurrence correlation do scheduler físico. Nenhum provider SDK/tool protocol/scheduler-specific type vaza para Domain/Application canônicos.

**C0.S5-T2 (histórico):** contratos persistidos em `17` §22 (+ linkage `25` §19 + ledger §6.30) como `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Esse estado foi superseded pelo review abaixo; não apagar história.

**C0.S5-T3 — PERSIST_ARCHITECTURE_REVIEW_DECISION:** `ARCHITECTURE_REVIEW_C0_S5` sobre `REVIEWED_HEAD=8d83383e9a9ff019132e7156d56e41643b168851`, `VERDICT=ACCEPT_WITH_RESIDUAL`, `C0.S5=APPROVED`, `INTEGRATION_CONTRACTS=FROZEN_ACCEPTED`, `C0.S6_AUTHORIZED=YES`, `BLOCKERS=NONE`, `EXECUTION_DRIFT=NONE`, `NEW_RUNTIME_ABSTRACTIONS=NONE`. Residual: `DOCUMENTATION_CONTRACT_TAXONOMY_RESIDUAL` (docs-only). `FOUNDATION_FREEZE=NOT APPROVED`, `PROGRAM=PLANNED / NOT_STARTED`, `C0=NOT_STARTED`, `DÉLIA_RUNTIME_DIFF=NONE`. **Nenhuma execução C0.S6 ocorre nesta tarefa.**

## C0.S6 — RED contract/conformance/privacy/security harness

**C0.S6-T2 (histórico):** harness RED canônico persistido em `20` (seção C0.S6) (+ linkage `25` §20 + ledger §6.32) como `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Esse estado foi superseded pelo review abaixo; não apagar história.

**C0.S6-T3 — PERSIST_ARCHITECTURE_REVIEW_DECISION:** `ARCHITECTURE_REVIEW_C0_S6` sobre `REVIEWED_HEAD=331e92d8fa3f0f3fff3926a58b983b7d05701c3e`, `VERDICT=ACCEPT_WITH_RESIDUAL`, `C0.S6=APPROVED`, `RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS=FROZEN_ACCEPTED`, `C0.S7_AUTHORIZED=YES`, `BLOCKERS=NONE`, `EXECUTION_DRIFT=NONE`, `NEW_RUNTIME_ABSTRACTIONS=NONE`. Evidence: `CONTRACT_FAMILY_COVERAGE=27/27`; `TEST_ID_COUNT=250`; `TEST_ID_UNIQUENESS=PASS` (STATIC_DOCUMENTATION_VALIDATION_ONLY); `AUTHZNEG-001..012 COMPLETE`; `FFB-001..018 PRESENT`. Residuals: runtime absence / external-owner / fixture binding / TO_INVENTORY (não bloqueantes para aceite do harness). `FOUNDATION_FREEZE=NOT APPROVED`, `PROGRAM=PLANNED / NOT_STARTED`, `C0=NOT_STARTED`, `DÉLIA_RUNTIME_DIFF=NONE`. New behavioral tests remain `TEST_NOT_RUN`. **Nenhuma execução C0.S7 / FOUNDATION_FREEZE ocorre nesta tarefa.** Historical T3 current-state (`FOUNDATION_FREEZE=NOT APPROVED`; next=C0.S7) is superseded by C0.S7-T2.

Required negatives incluem (cobertura detalhada e TEST_IDs estáveis em `20`):

```text
Chat dependency
RBAC/domain authority duplication
unsafe egress/token leak
hidden capture/biometric elevation
forged event→write
duplicate event/execution
schedule/timer tick treated as permission
stale creator authorization reused by scheduled occurrence
duplicate timer tick creates duplicate side effect
cancelled/paused recurring Work still fires
misfire/restart silently replays material ACT
PREPARE→ACT implicit
executor technical success treated as business success
process mining worker profiling
MCP/tool prompt poisoning policy change
A2A agent gets unrelated sensitive context
personal memory cross-user leak
memory overrides live business fact
semantic metric formula invented by LLM
sandbox host/network/secret escape
sandbox read connector performs write
artifact loses provenance/human edits
prediction presented as fact
scenario mutates production state
Edge offline widens authority
revoked model/package/server still executes
Marketplace install grants permission
Control Tower admin grants business permission
free-form LLM→OT command
```

## C0.S7 — FOUNDATION_FREEZE

C1 somente desbloqueia com todos os gates REQUIRED `PASS`, incluindo:

```text
PLATFORM_INVENTORY
STANDALONE_BOUNDARY
AUTHORITIES
SHARED_PRIMITIVES
ARCHITECTURE_PATTERNS
PERSISTENCE/PRIVACY
MEDIA/BIOMETRIC/EXTERNAL
EVENT/AUTOMATION/OUTCOME
RECURRING_WORK_BOUNDARY
PROCESS_INTELLIGENCE_BOUNDARY
AI_ASSET_GOVERNANCE_BOUNDARY
MCP_A2A_TRUST_BOUNDARY
PERSONAL_MEMORY_BOUNDARY
SEMANTIC_LAYER_BOUNDARY
SANDBOX_ARTIFACT_BOUNDARY
PREDICTIVE_TWIN_BOUNDARY
EDGE_OFFLINE_BOUNDARY
MODEL_MARKETPLACE_BOUNDARY
OT_SAFETY_BOUNDARY
CONFORMANCE_HARNESS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

**C0.S7-T2 — PERSIST_FOUNDATION_FREEZE_REVIEW_DECISION:** `FOUNDATION_FREEZE_REVIEW` sobre `REVIEWED_HEAD=6e10029bcc281c4e0c3575448a1414a157cc3c44`, `VERDICT=APPROVE_WITH_NON_BLOCKING_RESIDUALS`, `C0.S7=APPROVED`, `FOUNDATION_FREEZE=APPROVED`, `C1_AUTHORIZED=YES`, `C1_STARTED=NO`, `C1_EXECUTED=NO`, `BLOCKERS=NONE`, `EXECUTION_DRIFT=NONE`, `NEW_RUNTIME_ABSTRACTIONS=NONE`. Post-review commits `b5de5122f` and `0f55fd19b` = `OUTSIDE_TASK` (DAVI economic-wave freeze/correction; no DÉLIA authority/contract/harness change). `PROGRAM=PLANNED / NOT_STARTED`. `C0=NOT_STARTED` because this document does not define `COMPLETED` as an accepted phase-state token. `RUNTIME_READINESS=NOT_PROVEN`, `PRODUCTION_READINESS=NOT_PROVEN`, `NEW_BEHAVIORAL_TESTS=TEST_NOT_RUN`, `FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED=YES`, `DÉLIA_RUNTIME_DIFF=NONE`. Residuals remain `NON_BLOCKING_IMPLEMENTATION_RESIDUAL`. **Nenhuma implementação C1 ocorre nesta tarefa.**

```text
FOUNDATION_FREEZE = APPROVED means only:
  product/topology baseline frozen
  authority ownership frozen
  bounded contexts frozen
  shared reference semantics frozen
  persistence/privacy/safety architecture frozen
  integration contracts frozen
  RED acceptance harness frozen
  foundation acceptance gates defined
  architecture is sufficiently testable
  implementation may begin against frozen constraints

FOUNDATION_FREEZE = APPROVED does NOT mean:
  DÉLIA runtime exists or works
  security/privacy/integration runtime PASS
  future C1–C7 behavior PASS
  all external systems exist
  production or operational readiness
```

---

# C1 — Standalone Application Bootstrap

**C1-T1 — STANDALONE_API_SKELETON_HEALTH_TEST_FOUNDATION:** physical `delia-api/` Flask skeleton, `/health` liveness, config/logging mínimos e test foundation. `C1_STARTED=YES`. `C1_EXECUTED=NO`. JWT/Core/MFE/manifest/Gateway/Compose **não** entram nesta tarefa.

**C1-T1R1 — RUNTIME_SMOKE_AND_SHUTDOWN_VISIBILITY:** real-process TCP/HTTP `GET /health` smoke + `delia_api_stopped` shutdown visibility. Não redesenha skeleton/health contract. `C1_EXECUTED=NO`. C1-T2 permanece bloqueado até review de T1R1.

**C1-T2 — JWT_CORE_EFFECTIVE_ACCESS_INTEGRATION:** shared `jwt_validator` + Core `GET /me` effective access; JWT≠permission authority; fail-closed. `C1_EXECUTED=NO`. MFE/Gateway/Compose deferred.

**C1-T2R1 — REMOVE_PRODUCTION_ACCESS_CONTEXT_PROBE:** remove production `GET /access-context`; preserve JWT/Core contract tests via test-only probe. Architecture T2 preserved. `C1_EXECUTED=NO`.

**C1-T3 — STANDALONE_FEDERATED_MFE_FOUNDATION:** physical `plugins/delia/` federated MFE; `./App` expose; plugin-ui remote; mount/unmount; a11y/responsive baseline; no Chat/media auto-start. Manifest/Gateway/Compose deferred. `C1_EXECUTED=NO`.

**C1-T4 — MANIFEST_AND_PUBLICATION_CONTRACT:** `plugins/delia/delpi.manifest.json`; Core schema/validator; registration path proven; Core live register deferred. Gateway/Compose deferred. `C1_EXECUTED=NO`.

**C1-T4D1 — PERSIST_DELIA_ACCESS_PRODUCT_MASTER_DECISION:** Product Master APPROVED `delia.access` as bootstrap/platform-access permission (visibility/shell/root route only; ≠ business/Domain/ACT AuthZ). Core register + RBAC assignment still PENDING. `C1_EXECUTED=NO`.

**C1-T5 — GATEWAY_AND_COMPOSE_PUBLICATION_FOUNDATION:** `delpi-delia` + `delpi-delia-api` Compose/Gateway publication; `/apps/delia` + `/apps/delia-api`; Chat-independent. `C1_EXECUTED=NO`.

**C1-T6 — CORE_REGISTRATION_RBAC_AND_PORTAL_DISCOVERY_VERIFICATION:** Core register + positive/negative `delia.access` → `/me/apps` + Portal discovery without hardcode + live mount evidence. `OWN_MIGRATION_CHAIN` still PENDING (`ARCHITECTURE_DECISION_REQUIRED` vs Bootstrap Done). `C1_EXECUTED=NO`.

**C1-T6D1 — RESOLVE_OWN_MIGRATION_CHAIN_APPLICABILITY_AT_C1:** Product Master `OWN_MIGRATION_CHAIN=NOT_APPLICABLE_AT_C1` (no DÉLIA-owned persisted state). `52`§4+§17 aligned. Empty migration scaffolding forbidden. Future first owned persistence → REQUIRED→PASS. `C1_EXECUTED=YES`. `RUNTIME_READINESS=PROVEN` (bootstrap scope). `PRODUCTION_READINESS=NOT_PROVEN`. Next: `C1-FINAL` review only.

**C1-FINAL — STANDALONE_BOOTSTRAP_ACCEPTANCE_REVIEW:** Consolidated T1–T6D1 evidence; freshness reruns PASS; `C1_BOOTSTRAP_ACCEPTANCE=ACCEPT_WITH_RESIDUAL`; `C2_AUTHORIZED=YES`. Residuals: `TYPESCRIPT_ISOLATED=INCONCLUSIVE`, `CORE_CONTEXT_LIVE_NETWORK=TEST_NOT_RUN` (both NON_BLOCKING). Do not start C2 automatically.

- own Flask API skeleton/layers/config/logging/health/tests;
- JWT/Core integration;
- own federated React/Vite MFE with plugin-ui/mount/unmount/accessibility;
- own manifest/Gateway/Compose dev-prod;
- Portal full-page mount + global host contract;
- independent deploy/rollback/shutdown;
- no AI/media/external/automation/process/sandbox/Edge runtime feature enabled implicitly;
- Chat-offline independence gate.

---

# C2 — Portal + Operational Context + Platform Commands

- WorkspaceContext + EntityRefs/SourceRefs bounded;
- typed PlatformCommands;
- global panel/full-page parity;
- iframe bridge/security;
- shared-device/session cleanup under `BROWSER_STATE_RESIDENCY_POLICY` (C2-T1D1): verify host lifecycle first; introduce a browser-state boundary only when retained state is proven;
- operational context OP/machine/product/operation/posto;
- no memory/Edge/device/tool/provider state as permission authority.

C2-T3 freeze (documentation only; `LOCKED` in `25` is not runtime evidence):

```text
CLOSED_FOR_CURRENT_SCOPE: host props, route projection, mount/updateRoute/unmount, transient remount, browser-state policy, no DÉLIA logout, no storage framework
DEFER: WorkspaceContext runtime until operational owners/sources exist
DEFER: PlatformCommand bus; Portal location remains the navigation mechanism
DEFER: iframe bridge until DÉLIA has a real iframe consumer
IMPLEMENTATION_EVIDENCE: C2-T5R3 companion dock reuses federated remote `delia` / `./App`; V1 modal surface is SUPERSEDED_UX; visibility = `/me/apps` id=delia plus eligible split; no special sidebar launcher
DEFER: CP-012 intelligence to C3
C2-T4: OP/PRODUCT/OPERATION public via api-delpi (TOTVS); MACHINE/POSTO TO_INVENTORY; aggregate OPERATIONAL_CONTEXT remains TO_INVENTORY
C2-T4R1: formal status OPERATIONAL_CONTEXT = TO_INVENTORY (MIXED is not a canonical factual status)
WORKSPACE_CONTEXT_RUNTIME = DEFER
C2_IMPLEMENTATION_STARTED = YES
C2_EXECUTED = YES
C2_FINAL = ACCEPT_WITH_RESIDUAL
C2-T6R1: ACCEPTED_WITH_RESIDUAL; iframe CP Status restored; C2_SECURITY_BLOCKER=NO; Portal and Transformômetro security review remains required
C2-PREFINAL-R1: CP-001/CP-149/CP-156 restored to LOCKED; CP-149 live note corrected; CANONICAL_STATUS ≠ implementation evidence
C3_AUTHORIZED = YES
C3_STARTED = YES
C3_EXECUTED = NO
C3_T1 = APPROVED
EVIDENCE_EPISTEMIC_SEMANTICS = FROZEN_ACCEPTED
SOURCE_LINKAGE_SEMANTICS = FROZEN_ACCEPTED
C3_T2 = APPROVED
C3_T2_AUTHORIZED = YES
C3_T3_AUTHORIZED = YES
C3_T3_EXECUTED = NO
PRODUCTION_READINESS = NOT_PROVEN
NEXT = ARCHITECTURE_REVIEW_C3_T7
C3_T3 = APPROVED
C3_T4 = APPROVED
C3_T4_AUTHORIZED = YES
C3_T4_EXECUTED = NO
C3_T5 = APPROVED
C3_T5_AUTHORIZED = YES
C3_T5_EXECUTED = NO
C3_T6_AUTHORIZED = YES
C3_T6 = APPROVED
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
C3_T7 = APPROVED
ARCHITECTURE_REVIEW_C3_T7 = REWORK (verdict on REVIEW_TARGET_SHA da5e57db4c)
ARCHITECTURE_REVIEW_C3_T7R1 = ACCEPT_WITH_RESIDUAL (REVIEWED_IMPLEMENTATION_HEAD d49f77c966; §6.80)
C3_T8_AUTHORIZED = YES
C3_T8_EXECUTED = NO
C3_T8 = APPROVED
ARCHITECTURE_REVIEW_C3_T8 = REWORK (verdict on REVIEW_TARGET impl 0e39953e83)
ARCHITECTURE_REVIEW_C3_T8R1 = ACCEPT_WITH_RESIDUAL (REVIEWED_IMPLEMENTATION_HEAD 22b4aef606; §6.83)
REAL_DELPI_OPENAPI_COVERAGE = NOT_PROVEN
C2-FINAL accepted with residual; C3-T1..T8 APPROVED (`ARCHITECTURE_REVIEW_C3_T8R1` ACCEPT_WITH_RESIDUAL; §6.83); authorization != execution
ARCHITECTURE_COORDINATION_C3_NEXT_STEP_DECISION = ANOTHER_BOUNDED_C3_SLICE_REQUIRED (§6.84)
C3_MEDIA_FOUNDATION_01 = APPROVED (ARCHITECTURE_REVIEW_C3_MEDIA_FOUNDATION_01
 = ACCEPT_WITH_RESIDUAL; §6.86)
C3-INTERACTION-RUNTIME-01 = APPROVED
   (ARCHITECTURE_REVIEW_C3_INTERACTION_RUNTIME_01R2_FINAL
    = ACCEPT_WITH_RESIDUAL §6.91; R1 fail-closed rework at 4a57e70a46;
    R2 real OpenAI-compatible provider at c2f85834c5 — real eval PASS;
    REAL_PROVIDER_GATE=PROVEN_FOR_CURRENT_CONFIG;
    DELIA_RUNTIME_VOCABULARY=DELIA_LLM_* ONLY;
    COMPOSE_KIMI_DEPENDENCY=NONE)
NEXT_TASK_AUTHORIZED = NO
C3-INTERACTION-CONTINUITY-01 = APPROVED
   (ARCHITECTURE_REVIEW_C3_INTERACTION_CONTINUITY_01
    = ACCEPT_WITH_RESIDUAL §6.91; bounded transient multi-turn context;
    IMPLEMENTATION_HEAD fdca215029a09dee862633460e7bc17bf1fa5639;
    real eval PASS §6.90; CONTEXT_STORAGE=MFE_MEMORY_ONLY;
    SESSION_PERSISTENCE=NONE; CONVERSATION_HISTORY_AUTHORITY=NONE)
C3-MCP-INTEROP-01 = CANDIDATE_FOR_ARCHITECTURE_REVIEW
   (§6.92; EXISTING_SPECIALIST_MCP_FEDERATION over DAVI/TÉO/VISTA;
    IMPLEMENTATION_HEAD=783cc13578fe281425ae7793ccf5e3b97e3be362;
    provider-neutral SpecialistInteropPort + MCP adapter; registry
    allowlist DISCOVERY-only in C3; PREPARE/ACT never exposed;
    transport PROVEN 3/3 fail-closed 401; authenticated connectivity
    BLOCKED — no user-delegated token mechanism/owner clients yet;
    BUSINESS_READ_EXECUTION=PHASE_GATED while C4_AUTHORIZED=NO)
ARCHITECTURE_REVIEW_C3_MCP_INTEROP_01 = REWORK (§6.93)
   STATIC_GLOBAL_USER_TOKEN=REJECTED_FOR_PRODUCT_RUNTIME;
   IDENTITY_DIRECTION=SINGLE_DELIA_INTERNAL_CLIENT+TOKEN_EXCHANGE;
   CUSTOM_MCP_TRANSPORT=ACCEPTED_FOR_CURRENT_C3_SLICE
C3-MCP-INTEROP-01R1A = ACCEPT_WITH_RESIDUAL (§6.95;
   ARCHITECTURE_REVIEW_C3_MCP_INTEROP_01R1A on
   IMPLEMENTATION_HEAD=a5512c0b5d18f728f15cf0c652ffb0e8417e8e9d;
   residuals R1B-R1/R2/R3 close inside R1B)
C3-MCP-INTEROP-01R1B = ACCEPT_WITH_RESIDUAL (§6.97;
   ARCHITECTURE_REVIEW_C3_MCP_INTEROP_01R1B on
   IMPLEMENTATION_HEAD=cc65cc6388371224d955f266257d6aa3ca4967ce;
   authenticated initialize+tools/list PASS for DAVI/TEO/VISTA;
   residuals R1C-A..F close inside R1C)
C3-MCP-INTEROP-01R1C = ACCEPT_WITH_RESIDUAL (§6.99;
   ARCHITECTURE_REVIEW_C3_MCP_INTEROP_01R1C on
   IMPLEMENTATION_HEAD=78c87e12b079817de623adc7d4108ad3329a5364;
   security matrix + live 3/3 DEV eval PASS §6.98;
   C3_MCP_FEDERATION=APPROVED_CURRENT_SCOPE)
C3-FINAL-READINESS-01 = EXECUTED (§6.100):
   FULL_C3 = C3_NOT_COMPLETE (open foundation families inventoried);
   C4_BOUNDED_MCP_READ_CAN_BE_AUTHORIZED — dependencies proven,
   missing links task-scoped; C4_AUTHORIZED stays NO at phase level
C4-MCP-GOVERNED-READS-01 = REWORK (ARCHITECTURE_REVIEW §6.102;
   IMPLEMENTATION_HEAD=58a2d018d1ef28081e82e18148caa192d9d0b735;
   BIND_HEAD=f1d3ea2c9bfdcb7a6bfa5ad8b6c9b2924e709cf0;
   blocker: SPECIALIST_NOT_CONFIGURED/DISABLED silently degraded to
   undisclosed model fallback instead of SOURCE_UNAVAILABLE +
   delpi_source_unverified; everything else accepted unchanged)
C4-MCP-GOVERNED-READS-01R1 = ACCEPT_WITH_RESIDUAL (§6.104;
   ARCHITECTURE_REVIEW on IMPLEMENTATION_HEAD=
   8ea1e4b53835478138452e9004654d99b511b65c, BIND_HEAD=
   051687ff8957ee8fa1584a8ef655ae193a273d1c; blocker CLOSED — no R2)
C4-MCP-GOVERNED-READS-01 = APPROVED_CURRENT_BOUNDED_VERTICAL_SLICE
   (DAVI execute_delpi_information -> search_products -> Product
   Master/API DELPI only; negative surface unchanged; phase-level
   C4_AUTHORIZED=NO; C5=NO; PRODUCTION_READINESS=NOT_PROVEN)
C4-MCP-GOVERNED-READS-02 = APPROVED_CURRENT_BOUNDED_VERTICAL_SLICE
   (ARCHITECTURE_REVIEW_C4_MCP_GOVERNED_READS_02=ACCEPT_WITH_RESIDUAL
   §6.106 on IMPLEMENTATION_HEAD=0161c77d260907ca573735c5dbc066776c2c2234;
   prior candidate record §6.105:
   IMPLEMENTATION_HEAD=0161c77d260907ca573735c5dbc066776c2c2234; TÉO analyze → gpt_analyze,
   view=summary only, per-binding gate DELIA_C4_TEO_DASHBOARD_ANALYZE_
   ENABLED; shared capability-neutral governed_read.py semantic layer;
   live PASS grounded Transformômetro KPIs + provenance; DAVI
   regression PASS; other TÉO reads/PREPARE/ACT blocked))
THIRD_MCP_GOVERNED_READ = NOT_AUTHORIZED (§6.106 — two consumers
   suffice for the abstraction proof) — SUPERSEDED_BY
   ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02 (§6.118): capability
   existence/availability is specialist-owned via live tools/list;
   per-capability DÉLIA gates no longer bound READ availability
ARCH-DRIFT-MCP-CAPABILITY-AUTHORITY-02 = DECIDED / IN_EXECUTION
   (§6.118; specialist-owned live capability discovery for davi|teo|
   vista; DISCOVERY|READ|ANALYSIS invocable under current interactive
   policy; PREPARE/ACT blocked; per-capability env flags and
   local tool-name allowlists SUPERSEDED)
C5-GOVERNED-WRITE-FOUNDATION-01 = CANDIDATE_FOR_ARCHITECTURE_REVIEW
   (§6.108; IMPLEMENTATION_HEAD=c258a839bac117316e1105e9aa15acf8c29892ce; contracts only —
   GOVERNED_WRITE_BINDINGS EMPTY, no wire write)
ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01 =
   ACCEPT_WITH_RESIDUAL (ARCHITECTURE_REVIEW_ARCH_DRIFT_MCP_
   FEDERATION_CATALOG_OWNER_01R1=ACCEPT_WITH_RESIDUAL, §6.112;
   prior REWORK §6.111 closed by doc-only reconciliation;
   §6.109 decision, §6.110 evidence; IMPLEMENTATION_HEAD=
   fe434cdaf3713c9cb0d8e752f49690ed4bd81cee; specialist-owned
   catalog + owner-typed delpi/toolClass; DELIA mirror removed;
   discovery 3/3 + governed reads live PASS; PREPARE/ACT blocked;
   residual: PRODUCTION_MCP_RUNTIME=NOT_PROVEN)
NEXT =
   1) ARCHITECTURE_REVIEW_C5_GOVERNED_WRITE_FOUNDATION_01 (§6.108)
      — pending independently
   2) PROD-MCP-RUNTIME-ALIGNMENT-01 — production compose/env
      alignment + prod-safe Keycloak provisioner + runbook;
      NO real production apply
Workspace binding remains unscheduled
```

---

# C3 — Intelligence Core + Capability Foundations

Construir foundations only after C0:

1. provider/model abstraction;
2. conversation runtime;
3. structured understanding;
4. OpenAPI Action Catalog/Capability Projection;
5. Expertise/Playbooks/Knowledge;
6. multimodal/biometric/media;
7. Internet Research/ExternalConnection/Teams foundation;
8. Event/Decision path `FAST|OPERATIONAL|REASONING`;
9. Process Intelligence event-log contracts;
10. AI Asset Registry projection;
11. MCP/A2A ports/adapters/allowlists;
12. Personal Memory lifecycle/policy foundation;
13. Semantic Metric/Glossary registry foundation;
14. Sandbox isolation/execution foundation;
15. Prediction/Prescription/Twin contracts/model adapters;
16. Edge device/package/model/cache contracts;
17. Model Registry/eval lineage;
18. Evidence/epistemic synthesis + structured planner;
19. positive/sibling/negative/unknown/metamorphic/injection/security gates.

C3 ainda não libera material autonomous ACT.

---

# C4 — Governed Reads + Graph/Semantics/Analysis/Predictive Discovery

- generic Domain/API reads;
- authorized external/Teams reads;
- Business Graph;
- Semantic Query using governed MetricDefinition;
- Process Mining/discovery/conformance read-only pilots;
- Analysis Sandbox read-only reproducible analysis;
- Predictive read-only pilots;
- Edge cached read-only knowledge/telemetry pilots;
- MCP/A2A read-only tools/agent tasks;
- Personalization of relevance/presentation using live facts;
- model lineage/evidence;
- no material side effect.

---

# C5 — Governed Writes + Executors + Durable Work

- Decision Gate/revalidation/idempotency;
- business/external/Teams writes;
- Automation Capability Registry;
- API/Function/RPA/Computer-Use executors only as justified;
- AutomationExecution lifecycle;
- RPA workers/queues only if prioritized;
- postcondition/Outcome verification;
- Durable Workflow/checkpoints/waits/resume;
- **Recurring Governed Work runtime**: persisted recurring definition + deterministic occurrence materialization/correlation, independent of chat session;
- create/inspect/list/pause/resume/cancel recurring Work with versioned recurrence, IANA timezone and bounded start/end;
- per-occurrence live identity/Core/domain AuthZ + Policy/Decision revalidation; `schedule != permission`;
- per-occurrence idempotency across duplicate timer/retry/restart/reconciliation; explicit misfire/overlap policy;
- recurring report→artifact→external send anchor using current authorized data and verified Outcome;
- Process Intelligence automation opportunity → candidate/PREPARE only;
- MCP/A2A write-capable delegation under same gates;
- semantic definition TOCTOU handling;
- Artifact lifecycle/version/provenance/ACL;
- Prescriptive output → PREPARE/Decision; no implicit Apply.

C5 pode liberar `ACT` material somente para capabilities explicitamente autorizadas, sob Decision Gate, policy, identidade, idempotência, auditabilidade e verificação de Outcome. Isso não equivale a autonomia avançada nem a L5. Uma ocorrência temporal bounded de Recurring Governed Work é C5-capable quando esses gates passam; ela não é Watch autonomous ACT.

---

# C6 — Product Work + Process/Control/Experience Ecosystem

- Tasks/Cases/Rooms/Inbox/Watch `OBSERVE|ADVISE|PREPARE`;
- recurring Work product/admin UX: inspect/list/status/recurrence-timezone/next occurrence quando derivável/last outcome/pause/resume/cancel/history;
- provider/Teams events and reconciliation;
- Meeting/Frontline;
- Automation Hub admin/execution/worker/exception views;
- notifications/escalations;
- Process Intelligence product UX + before/after metrics;
- AI Control Tower inventory/health/risk/eval/cost/value/incidents;
- MCP/A2A server/agent lifecycle/health;
- Personal Memory user controls + personalized briefing;
- Semantic Layer catalog/lineage/conflict UX;
- Artifact Workspace collaboration/templates;
- Operational Twin scenario workspace (simulation only);
- Edge offline Frontline pilots/event buffering/sync;
- Model lifecycle drift views;
- Capability Marketplace draft/review/catalog;
- Organizational Knowledge/Governed Learning/Expertise Studio;
- governed `ACT` continua sujeito aos gates de C5; **autonomous ACT avançado** permanece bloqueado até os gates de C7.

Recurring Governed Work não altera a regra de Watch: em C6, Watch continua sem autonomous ACT. O schedule é um trigger temporal previamente definido para Work bounded; a ocorrência material continua revalidando gates de C5.

---

# C7 — Advanced Autonomy + Twin/Edge/Marketplace + Optimization

- autonomy L0–L5 with L5 OFF default;
- selected Watch ACT and autonomous workflows;
- autonomous invoicing anchor when in declared scope;
- closed-loop Process Intelligence only under explicit policy and before/after measurement;
- cross-runtime Control Tower budgets/cohorts/kill switches/incident containment;
- autonomous A2A delegation under approved capability/context/budget;
- advanced personalization under privacy controls;
- scaled semantic federation/materialization;
- scaled Analysis Sandbox/Artifact generation;
- Predictive/Prescriptive ACT only under policy/verified Outcome;
- advanced Operational Twin; `SIMULATE != APPLY` remains invariant;
- Edge rollout by device/cohort/package/model + rollback/revoke;
- bounded offline actions only if explicitly approved and expiring/reconcilable;
- production model deployment/drift/rollback/kill switch;
- Marketplace publish/enable + AI supply-chain controls;
- Model Router/Compute Policy;
- advanced realtime/media/Teams only with evidence/ADR;
- computer-use advanced only sandboxed/allowlisted;
- OT actuation remains separate industrial safety initiative;
- scale/performance/cost/canary/rollback/final CP coverage.

Recurring governed schedules não precisam de L5/C7 para executar L4 bounded já autorizado em C5. C7 só amplia autonomia selecionada; não transforma schedule em permission authority.

---

## 6. Fora do default scope

```text
Chat→DÉLIA migration
open-world biometric surveillance
psychological/worker scoring
unrestricted web/browser/sandbox/desktop access
provider/tool/model secrets in prompts/MFE/logs
personal source/memory auto-sharing
implicit send/write/ACT
schedule/timer as permission authority
planner with raw RPA clicks/selectors
one global L5 switch
process mining as employee ranking
MCP/A2A discovery as auto-trust
semantic KPI formula invented ad hoc
prediction as fact
twin simulation writing production automatically
offline mode widening authority
Marketplace package granting RBAC
free-form LLM→PLC/CNC/robot
DÉLIA replacing safety interlocks
```

## 7. Protocolo por subetapa

```text
REVALIDATE HEAD/WORKTREE
→ READ AUTHORITIES + thematic spec
→ DEPENDENCY GATE
→ BASELINE
→ MINIMAL CORRECT OWNER-LEVEL DIFF
→ PRODUCER/CONSUMER WIRING
→ UNIT/CONTRACT/INTEGRATION
→ POSITIVE/SIBLING/NEGATIVE
→ SECURITY/RBAC/PRIVACY/SAFETY
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT STEP
```

## 8. Regra anti-refatoração

Antes de criar qualquer novo service/schema/table/framework/registry/engine/agent/server/sandbox/twin/edge runtime/marketplace, provar:

1. owner real e source of truth;
2. neutral shared capability existente;
3. boundary justificável;
4. shared primitive já não resolve;
5. persistence realmente necessária;
6. permission/data authority não está sendo duplicada;
7. provider/tool/executor pode ser trocado por adapter;
8. data/secret/identity stays bounded;
9. read/write/PREPARE/ACT/simulate/apply continuam separados;
10. next phase não exigirá redesign óbvio;
11. test/eval/rollback/kill-switch path existe;
12. implementation does not depend on Chat.

Se falhar materialmente: **não implementar** até corrigir o desenho.

## 9. Primeira ordem efetiva

```text
C0.S0
→ C0.S1
→ C0.S2
→ C0.S3
→ C0.S4
→ C0.S5
→ C0.S6
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1
```

Nenhuma capability temática `53–66` precede o Foundation Freeze.

### C3-T5 — OpenAPI Action Catalog + Capability Projection (APPROVED)

```text
REVIEW = ARCHITECTURE_REVIEW_C3_T5
REVIEWED_HEAD = 1663aee66a7ce8574107967cf3ed88360824a0b6
IMPLEMENTATION_HEAD = 84c249bee0182ebf514142a24cb8bbea4090ca26
VERDICT = ACCEPT_WITH_RESIDUAL
C3-T5 = APPROVED
OPENAPI_ACTION_CATALOG_FOUNDATION = IMPLEMENTED (bounded TEST_FIXTURE proof)
CAPABILITY_PROJECTION = IMPLEMENTED
CAPABILITY_DISCOVERY_AUTHORIZATION_SEPARATION = PASS (fixture/conformance)
OPERATION_CHARACTER_SEMANTICS = IMPLEMENTED
SOURCE_CONTRACT = TEST_FIXTURE
REAL_DELPI_OPENAPI_COVERAGE = NOT_PROVEN
SOURCE_SEMANTIC_DECLARATION_FOR_REAL_CONTRACTS = NOT_PROVEN
MODEL_CALL = NONE
RAG = NONE
VECTOR_STORE = NONE
PLANNER = NONE
CONVERSATION_RUNTIME = NONE
TOOL_EXECUTION = NONE
PREPARE = NONE
ACT = NONE
AUTOMATION_HUB_EXECUTION = NONE
PERSISTENCE = NONE
MIGRATION = NONE
FULL_DELIA_API_SUITE = TEST_NOT_RUN
C3_T1_T4_FULL_REGRESSION_ON_FINAL_HEAD = TEST_NOT_RUN
ARCHITECTURE_ENFORCEMENT = FAIL / OUTSIDE_TASK_BASELINE
CURSOR_RULES_GOVERNANCE = pre-existing red
C3_T6_AUTHORIZED = YES
C3_T6 = APPROVED
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
C3_T7 = APPROVED
C3_EXECUTED = NO
PRODUCTION_READINESS = NOT_PROVEN
NEXT = ARCHITECTURE_REVIEW_C3_T7
NOTE_SUPERSEDED_CANDIDATE: historical C3-T5 candidate markers live in ledger candidate block / §6.73 review
```

C3-T5 does not classify operation character from HTTP verb. Semantic projection requires an explicit governed declaration; missing/duplicate identity or missing semantic declaration fails closed as non-projectable. OpenAPI security metadata is descriptive only and never becomes current-user permission, Core RBAC, Domain AuthZ or ACT authorization. The GitHub Architecture Enforcement run for the implementation SHA failed in a pre-existing Transformômetro GPT Actions repository check outside this task; no C3-T5 file was identified by that failing test. Real DELPI OpenAPI coverage remains `NOT_PROVEN`.

### C3-T6 — Expertise / Knowledge Governance + Retrieval Contracts (historical candidate)

NOTE_SUPERSEDED_BY: C3-T6R1 Knowledge Contract Rework

```text
TASK = C3-T6 — Expertise / Knowledge Governance + Retrieval Contracts
STATE = HISTORICAL_CANDIDATE
IMPLEMENTATION_HEAD = 537cf476646964f0866484c009043c261cf8f725
BASE_HEAD = 86729dc5ba1aa21463271989feb3e4cc215ea218
```

### C3-T6R1 — Knowledge Contract Rework (APPROVED)

```text
REVIEW = ARCHITECTURE_REVIEW_C3_T6R1
REVIEWED_IMPLEMENTATION_HEAD = 1a49e501fb8e2d900081572de83d2226cc09fb68
PRIOR_C3_T6_IMPLEMENTATION_HEAD = 537cf476646964f0866484c009043c261cf8f725
REVIEW_REANCHOR_HEAD = 446d93564a2219430c8afac3b283881f41c4d9ae
VERDICT = ACCEPT_WITH_RESIDUAL
C3_T6 = APPROVED
PRIOR_BLOCKER_EVIDENCE_REF_TYPING = RESOLVED
PRIOR_BLOCKER_KNOWLEDGE_SCOPE = RESOLVED
PRIOR_BLOCKER_UNSUPPORTED_INCLUDE_FLAGS = RESOLVED
PRIOR_BLOCKER_REVOKED_DEPRECATED_NORMAL_RETRIEVAL = RESOLVED
BLOCKERS = NONE
C3_T6_BOUNDARY = ACCEPT
EXPERTISE_CONTRACT = ACCEPT
EXPERTISE_EVIDENCE_REF_TYPING = PASS / EvidenceRef
EXPERTISE_STATUS_DECISION = ACCEPT_WITH_RESIDUAL
PLAYBOOK_CONTRACT = ACCEPT
PLAYBOOK_STATUS_DECISION = ACCEPT_WITH_RESIDUAL
KNOWLEDGE_CANDIDATE_MODEL = ACCEPT
ORGANIZATIONAL_KNOWLEDGE_MODEL = ACCEPT
KNOWLEDGE_LIFECYCLE = ACCEPT
PUBLICATION_ELIGIBILITY = PASS_WITH_RESIDUAL
KNOWLEDGE_EVAL_SEMANTICS = KNOWLEDGE_GOVERNANCE_STATE != MODEL_EVAL_RESULT
NORMAL_RETRIEVAL_SCOPE = PUBLISHED_ORGANIZATIONAL_KNOWLEDGE_ONLY
REVOKED_DEPRECATED_RETRIEVAL_SEMANTICS = EXCLUDED_FROM_NORMAL_RETRIEVAL
KNOWLEDGE_SCOPE = REMOVED
RETRIEVAL_INCLUDE_FLAGS = REMOVED
RETRIEVAL_PORT_DECISION = DEFER / PASS
PHYSICAL_KNOWLEDGE_STORAGE = TO_INVENTORY / DEFERRED
NEW_RUNTIME_ABSTRACTIONS = NONE
RAG = NONE
VECTOR_STORE = NONE
PLANNER = NONE
CONVERSATION_RUNTIME = NONE
TOOL_EXECUTION = NONE
PREPARE = NONE
ACT = NONE
PERSISTENCE = NONE
MIGRATION = NONE
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
C3_T7 = CANDIDATE_FOR_ARCHITECTURE_REVIEW
C3_EXECUTED = NO
PRODUCTION_READINESS = NOT_PROVEN
NEXT = ARCHITECTURE_REVIEW_C3_T7
NOTE_SUPERSEDED_CANDIDATE: historical C3-T6 / C3-T6R1 candidate markers live in ledger §6.74–§6.75; review persistence §6.76
```

C3-T6R1 is accepted with residual. Expertise `evidence_refs` are canonical `EvidenceRef`. Retrieval has no caller-selectable scope/include flags; normal retrieval is published organizational Knowledge only. RetrievalPort/store/RAG remain deferred. Expertise/Playbook status strings remain descriptive non-authoritative metadata. Publication completion flags are lifecycle-state assertions, not proof of executed review/eval operations.

### C3-T7 — Decision Path + Structured Planner Foundation (candidate — superseded)

NOTE_SUPERSEDED_BY = C3-T7R1 section below; `ARCHITECTURE_REVIEW_C3_T7=REWORK`
(REVIEW_TARGET_SHA=da5e57db4c; blockers: duplicate `capability_id` ambiguity
via lossy dict collapse + evidence bound to local-only SHAs;
abstraction-count wording corrected in C3-T7R1).

```text
TASK = C3-T7 — FAST | OPERATIONAL | REASONING + STRUCTURED_PLANNER_FOUNDATION
STATE = CANDIDATE_FOR_ARCHITECTURE_REVIEW
IMPLEMENTATION_HEAD = 0fc2cba747ccae27e6980c7335b055529081c9e7 (rebased da5e57db4c1f07040b7a703272df39a1f2550349)
BASE_HEAD = 86f54483e7bacde1c9c5fa8510affe70ddc2e2db
OWNER = delia-api/app/domain/decision_path/ + app/domain/planning/
MODEL = DecisionPath{FAST,OPERATIONAL,REASONING} + DecisionPathInput +
        DecisionPathResult{SELECTED|INCONCLUSIVE|BLOCKED} +
        PlanCandidate + ordered PlanStep + PlanValidationResult
RULES = select_decision_path (fail-closed; authoritative-rule priority;
        smallest sufficient path) + validate_plan_candidate (fail-closed
        unknown_capability / operation_character_mismatch /
        missing_required_evidence / duplicate_step_id)
REUSE = CapabilityProjection + OperationCharacter (C3-T5);
        EvidenceRef + SourceRef (C3-T2R1)
INVARIANTS = routing != authorization; plan != execution; not every event
        calls LLM; OPERATIONAL requires no model; REASONING is routing
        classification only; planned PREPARE/ACT/VERIFY are descriptive
        future requirements
NONE = model router, planner engine/runtime, ports, use cases, retrieval
       port, RAG/vector/embedding, conversation, tool execution, PREPARE,
       ACT, Automation Hub, persistence, migration
EVIDENCE = ledger §6.78 (HISTORICAL); 20 C3-T7 section (HISTORICAL);
           TARGETED_C3_T7 PASS 41/41; FULL_DELIA_API PASS 205/205 at
           PRIOR_IMPLEMENTATION_HEAD — PRIOR_LOCAL_EVIDENCE
NEXT = ARCHITECTURE_REVIEW_C3_T7 (verdict recorded: REWORK)
```

### C3-T7R1 — Duplicate Capability Fail-Closed + Evidence Rebind (approved)

```text
TASK = C3-T7R1 — DUPLICATE_CAPABILITY_FAIL_CLOSED_AND_EVIDENCE_REBIND
STATE = APPROVED (ARCHITECTURE_REVIEW_C3_T7R1 = ACCEPT_WITH_RESIDUAL; §6.80)
BASE_HEAD = c50fd2e5b0d963c2b9730a1bb8b0166ded71150b
IMPLEMENTATION_HEAD = d49f77c966cd03387dd3e8e268cb9be5e2098ab6
OWNER = delia-api/app/domain/planning/ (bounded rework; decision_path unchanged)
RULES = validate_plan_candidate — duplicate capability_id in
        available_capabilities detected BEFORE lossy lookup; any duplicate
        (identical or divergent, any order) -> PlanValidationResult.valid=False
        with PlanValidationCode.DUPLICATE_CAPABILITY_ID
INVARIANTS = no FIRST/LAST/SORT-order/operation-character/owner/
        source-contract wins; unknown capability and operation-character
        mismatch behavior unchanged; routing model/policy unchanged
ABSTRACTION_REPORT = NEW_DOMAIN_VALUE_TYPES=9 (ENUMS=4: DecisionPath,
        DecisionPathStatus, RoutingReasonCode, PlanValidationCode;
        DATACLASSES=5: DecisionPathInput, DecisionPathResult, PlanStep,
        PlanCandidate, PlanValidationResult);
        NEW_INFRASTRUCTURE_OR_RUNTIME_ABSTRACTIONS=NONE
NONE = registry/resolver/conflict-engine/dedup-service; planner/routing/
       model engines; ports; RAG/vector/embedding; conversation; tool
       execution; PREPARE; ACT; persistence; migration
EVIDENCE = ledger §6.79/§6.80; 20 C3-T7R1 section; TARGETED_C3_T7 PASS 46/46;
           FULL_DELIA_API PASS 210/210 at IMPLEMENTATION_HEAD
TEST_SHA_BINDING = d49f77c966cd03387dd3e8e268cb9be5e2098ab6
REVIEWED_IMPLEMENTATION_HEAD = d49f77c966cd03387dd3e8e268cb9be5e2098ab6
VERDICT = ACCEPT_WITH_RESIDUAL
RESIDUALS = 6 non-blocking (§6.80; SourceRef result-level, asserted routing
            facts, descriptive postcondition, no model evidence, OpenAPI
            coverage, RetrievalPort deferral)
NEXT = C3-T8 — CONVERSATION_SESSION_INTERACTION_FOUNDATION
```

### C3-T8 — Conversation / Session Interaction Foundation (candidate)

```text
TASK = C3-T8 — CONVERSATION_SESSION_INTERACTION_FOUNDATION
STATE = APPROVED
ARCHITECTURE_REVIEW_C3_T8 = REWORK (blocker: direct FACT classification on
        InteractionTurn without qualified-Fact contract) — historical
ARCHITECTURE_REVIEW_C3_T8R1 = ACCEPT_WITH_RESIDUAL (prior blocker RESOLVED;
        6 non-blocking residuals; REVIEWED_IMPLEMENTATION_HEAD 22b4aef606;
        ledger §6.83)
BASE_HEAD = 3bee773a3210991562ae327bb1f72f861bf97fb1
IMPLEMENTATION_HEAD = 22b4aef60626cbf4f0f822a0972053f113f2ab71 (C3-T8R1)
EPISTEMIC_ADMISSIBILITY = InteractionTurn fails closed on FACT in this
        slice; USER_INPUT accepts None|OBSERVATION; DELIA_RESULT accepts
        None|OBSERVATION|CALCULATION|HYPOTHESIS|CONCLUSION|RECOMMENDATION
OWNER = delia-api/app/domain/interaction/
MODEL = InteractionSession{ACTIVE|CLOSED} + bounded SessionContext +
        InteractionTurn{USER_INPUT|DELIA_RESULT} +
        InteractionValidationResult/Code
RULES = validate/record_interaction_turn + close_interaction_session —
        deterministic, fail-closed (session_closed, cross_session_reference,
        empty_content)
REUSE = UserRef(new canonical ref in evidence domain) + EntityRef +
        EpistemicClass + EvidenceRef + SourceRef + DecisionPath +
        PlanCandidate
INVARIANTS = session != authorization/Memory/Knowledge/SoT; turn result
        != FACT; user text != authorization; plan in session != execution;
        cross-session refs fail closed
NONE = conversation/chat engines, repositories, retrieval port, RAG,
        Personal Memory runtime, model call, tool/PREPARE/ACT execution,
        persistence, migration, conversation UI, provider roles in Domain
EVIDENCE = ledger §6.82/§6.83; 20 C3-T8 section; TARGETED_C3_T8R1 PASS 42/42;
           FULL_DELIA_API PASS 252/252 at IMPLEMENTATION_HEAD
NEXT = C3-MEDIA-FOUNDATION-01 (brief pending:
       PREPARE_C3_MEDIA_FOUNDATION_01_IMPLEMENTATION_BRIEF)
```

### C3-MEDIA-FOUNDATION-01 — Multimodal / Media Evidence Foundation (authorized)

```text
TASK = C3-MEDIA-FOUNDATION-01 — MULTIMODAL_MEDIA_EVIDENCE_FOUNDATION
STATE = APPROVED
ARCHITECTURE_REVIEW_C3_MEDIA_FOUNDATION_01 = ACCEPT_WITH_RESIDUAL
        (ledger §6.86; REVIEWED_IMPLEMENTATION_HEAD 3821dc1562;
         residuals: REAL_MULTIMODAL_QUALITY_EVIDENCE TEST_NOT_RUN,
         BIOMETRIC_FOUNDATION DEFERRED, STT/TTS_PORTS DEFERRED,
         LIMITATIONS_CONTENT_BOUNDS non-blocking)
AUTHORIZED_BY = ARCHITECTURE_COORDINATION_C3_NEXT_STEP_DECISION
                (ANOTHER_BOUNDED_C3_SLICE_REQUIRED; ledger §6.84)
IMPLEMENTATION_HEAD = 3821dc1562f4dce68abc6103857ae65d6630e543
MODEL = MediaKind{IMAGE|AUDIO|VIDEO|SCREEN|DOCUMENT_IMAGE} +
        MediaRef + MediaRegion + MediaTimeRange + MediaObservation
        (delia-api/app/domain/media/)
OWNER = DÉLIA Intelligence / Multimodal (source/domain owner remains
        authoritative fact owner; DÉLIA = evidence/epistemic coordination)

ALLOWED_SCOPE = provider-neutral media/source references; typed multimodal
        observations; provenance; limitations; region/time-range semantics
        where justified; EpistemicClass/EvidenceRef/SourceRef/EntityRef
        reuse; deterministic conformance tests
FORBIDDEN = biometric identification/face/speaker/liveness/emotion/
        personality/employment inference; real camera/microphone/STT/TTS/
        vision providers; media persistence; RAG; tool execution;
        PREPARE/ACT; OT actuation; generic MediaEngine/MultimodalRouter
INVARIANTS = media content untrusted; multimodal extraction = OBSERVATION
        by default; observation != FACT; EvidenceRef/SourceRef !=
        authorization; confidence != authority; media metadata !=
        permission; visual finding != official quality decision;
        no free-form AI -> PLC/CNC/robot/machine path
ABSTRACTION_GATE = no speculative MediaEngine/MultimodalEngine/
        VisionRouter/MediaRegistry/ProviderRouter/GenericObservationEngine
        without a real current consumer
CP_TRACEABILITY = inspect CP-078/079/160/162/163/164/177 (conservative;
        authorization != PASS); biometric CP-184..187 stay outside this
        slice (separate bounded decision required)
EVIDENCE = ledger §6.85/§6.86; TARGETED_C3_MEDIA_01 PASS 47/47;
           FULL_DELIA_API PASS 299/299 at IMPLEMENTATION_HEAD
NEXT = C3-INTERACTION-RUNTIME-01 (coordination authorized; see below)
```

### C3-INTERACTION-RUNTIME-01 — Interactive Conversation Vertical Slice (authorized)

```text
TASK = C3-INTERACTION-RUNTIME-01 — INTERACTIVE_CONVERSATION_VERTICAL_SLICE
STATE = APPROVED (ARCHITECTURE_REVIEW_C3_INTERACTION_RUNTIME_01R2_FINAL
        = ACCEPT_WITH_RESIDUAL; persisted §6.91)
AUTHORIZED = YES (ARCHITECTURE_COORDINATION_INTERACTIVE_VERTICAL_SLICE)
EXECUTED = NO
IMPLEMENTATION_HEAD = c2f85834c5174f910e0e44dec768a487baabbd2c (R2;
        R1 4a57e70a46; prior candidate 9f470b8c0a reviewed REWORK)
PRIOR_BLOCKER_TEST_ONLY_ADAPTER_DEFAULT_RUNTIME_EXPOSURE = RESOLVED
MODE = TEXT_ONLY + READ/GENERATE_ONLY
MODEL = HandleInteractiveConversationTurn (app/application/interaction/)
        over InteractionSession/InteractionTurn + InvokeModel/
        ModelInvocationPort; POST /interaction/turns; DÉLIA MFE input/
        submit/result surface (plugins/delia)
OWNER = delia-api + plugins/delia
AUTHN = JWT validate + Core GET /me (existing middleware/provider)
AUTHZ = Core effective permission delia.access or is_superadmin;
        frontend permissions never authoritative; fail closed
SESSION_SEMANTICS = REQUEST_SCOPED (one InteractionSession per request;
        no repository/table/migration/history)
TURNS = USER_INPUT (epistemic None; untrusted input) -> DELIA_RESULT
        (non-FACT classes only; default HYPOTHESIS; FACT rejected)
MODEL_INVOCATION = reuses InvokeModel/ModelInvocationPort; bounded config
        (task_purpose_id delia.interaction.turn; schema
        delia.interaction.turn v1; instruction delia.interaction.base v1
        sha256-bound; expected field answer; timeout<=30s;
        input<=16384 chars)
REAL_PROVIDER_ADAPTER = IMPLEMENTED (OpenAICompatibleModelInvocationAdapter;
        app/infrastructure/model_invocation/; adapter_kind
        OPENAI_COMPATIBLE; ProviderExposureClass.EXTERNAL_APPROVED)
REAL_PROVIDER_PROTOCOL = OPENAI_COMPATIBLE (chat completions; no tools,
        no streaming, no function calling)
INITIAL_REAL_PROVIDER = OpenRouter gateway / Kimi model via env config
REAL_PROVIDER_GATE = PROVEN_FOR_CURRENT_CONFIG (DELPI operational env
        owns KIMI_*; DÉLIA reads DELIA_LLM_* mapped from the same secret
        source; incomplete config fails closed)
TESTING_RUNTIME = DETERMINISTIC_TEST_ADAPTER_ALLOWED (testing=True or
        explicit port/handler injection only)
DEFAULT_NON_TEST_RUNTIME_WITHOUT_PROVIDER = FAIL_CLOSED (no implicit
        TEST_ONLY fallback; handler absent -> bounded 503
        model_unavailable)
DELIA_RUNTIME_VOCABULARY = DELIA_LLM_* ONLY (compose boundary cleaned;
        COMPOSE_KIMI_DEPENDENCY=NONE; APPLICATION_KIMI_DEPENDENCY=NONE;
        INFRA_SHA=63656e5741e321ad7b8abb21fe37c9992f45d1ff)
TEST_ONLY_FALLBACK = DISABLED_OUTSIDE_TEST
REAL_MODEL_INTERACTION = PROVEN (8-case real eval at IMPLEMENTATION_HEAD;
        see ledger §6.89) | REAL_MODEL_EVAL = PASS
        (BUSINESS_FACT_NON_FABRICATION INCONCLUSIVE on the
        generic-writing case only; PASS where applicable)
FORBIDDEN = business reads; RAG/Knowledge retrieval; vector/embedding
        runtime; tool execution; PREPARE/ACT; Automation Hub; Personal
        Memory; Model Router; agent selection; Chat runtime reuse;
        media input; session persistence; migration; OT actuation
OUTPUT_GUARDS = tool_call/function_call fields, secret-bearing and
        CoT/scratchpad payloads rejected fail-closed; provider-claimed
        FACT never promoted; HTTP response exposes bounded IDs/content/
        epistemic_class/limitations/generated_at/model_invocation_id only
EVIDENCE = ledger §6.87-§6.89; TARGETED_C3_INTERACTION_RUNTIME +
           provider tests PASS 129/129; FULL_DELIA_API PASS 383/383;
           MFE PASS 29/29 + typecheck + build; REAL_MODEL_EVAL PASS
           (8 cases) at IMPLEMENTATION_HEAD
REVIEW = ARCHITECTURE_REVIEW_C3_INTERACTION_RUNTIME_01R2_FINAL
         = ACCEPT_WITH_RESIDUAL (persisted §6.91; residuals:
         PRODUCTION_READINESS=NOT_PROVEN, MODEL_ROUTER=NONE,
         PROVIDER_ROUTER=NONE, AGENT_SELECTION=NONE,
         DOMAIN_BUSINESS_READS=NONE, KNOWLEDGE_RETRIEVAL=NONE,
         RAG=NONE, TOOL_EXECUTION=NONE, PREPARE=NONE, ACT=NONE,
         PERSONAL_MEMORY=NONE, SESSION_PERSISTENCE=NONE)
NEXT = ARCHITECTURE_COORDINATION_FIRST_GOVERNED_DELPI_READ
```

### C3-INTERACTION-CONTINUITY-01 — Bounded Transient Multi-Turn Conversation (approved)

```text
TASK = C3-INTERACTION-CONTINUITY-01 — BOUNDED_TRANSIENT_MULTI_TURN_CONVERSATION
STATE = APPROVED (ARCHITECTURE_REVIEW_C3_INTERACTION_CONTINUITY_01
        = ACCEPT_WITH_RESIDUAL; persisted §6.91)
EXECUTED = NO
IMPLEMENTATION_HEAD = fdca215029a09dee862633460e7bc17bf1fa5639
BIND_HEAD = 79755ea96a1a90f9f1869a4dee8578aa892a1f8c
TRANSIENT_MULTI_TURN = PASS | HTTP_CONTEXT_CONTRACT = PASS
MFE_TRANSIENT_CONTEXT = PASS | CONTEXT_STORAGE = MFE_MEMORY_ONLY
SESSION_SEMANTICS = REQUEST_SCOPED | SESSION_PERSISTENCE = NONE
PERSONAL_MEMORY = NONE | ORGANIZATIONAL_KNOWLEDGE_WRITE = NONE
CONVERSATION_HISTORY_AUTHORITY = NONE
CURRENT_AUTHZ_PER_REQUEST = PASS
CONTEXT_TURN_KINDS = USER_INPUT | DELIA_RESULT (strict alternation)
CONTEXT_BOUND = PASS | CONTEXT_BOUND_SOURCE = MAX_INPUT_CHARS
CONTEXT_OVERSIZE_BEHAVIOR = FAIL_CLOSED (context_too_large)
MODEL_INVOCATION_PORT_REUSE = PASS
PROVIDER_CONTEXT_MAPPING = INFRASTRUCTURE_ONLY
REAL_MODEL_CONTINUITY = PROVEN (5-case real eval PASS at
        IMPLEMENTATION_HEAD; TEST_SHA_BINDING=EXACT)
HISTORY_NOT_TRUTH = PASS | HISTORY_NOT_AUTHORIZATION = PASS
ACCEPTED_RESIDUALS = SESSION_PERSISTENCE=NONE/intentional;
        PERSONAL_MEMORY=NONE/intentional;
        CONVERSATION_SUMMARIZATION=NONE/deferred;
        LONG_TERM_HISTORY=NONE/deferred;
        REAL_BUSINESS_DATA_ACCESS=NONE/next governed capability family
EVIDENCE = ledger §6.90-§6.91; continuity tests 30/30; full suite
           415/415; MFE 36/36 + typecheck + build; real eval PASS
NEXT = C3-MCP-INTEROP-01R1B (authenticated specialist discovery; R1A evidence pending review)
```

### C3-MCP-INTEROP-01 — Existing Specialist MCP Federation (candidate for review)

```text
TASK = C3-MCP-INTEROP-01 — EXISTING_SPECIALIST_MCP_FEDERATION
STATE = CANDIDATE_FOR_ARCHITECTURE_REVIEW
EXECUTED = NO
IMPLEMENTATION_HEAD = 783cc13578fe281425ae7793ccf5e3b97e3be362
SCOPE = provider-neutral interoperability boundary to the three
        existing approved specialist MCPs — DAVI (api-delpi),
        TÉO (transformometro-api), VISTA (tv-dashboard-api);
        no specialist business logic/AuthZ/catalog reimplemented;
        no direct Product/Transformômetro/TV adapters; no generic
        HTTP/MCP proxy; no A2A runtime
APPROVED_SPECIALISTS = DAVI | TÉO | VISTA (allowlist registry;
        unknown specialist/server/tool fails closed)
APPLICATION_BOUNDARY = SpecialistInteropPort + SpecialistInterop
        use case (provider-neutral; no MCP/HTTP/vendor types in
        Domain/Application)
INFRASTRUCTURE = infrastructure/interoperability/mcp — bounded
        JSON-RPC transport (DELPI profile: json_response +
        stateless_http) + McpSpecialistAdapter; two fail-closed
        boundaries (catalog projection + pre-wire invocation re-check)
OPERATION_CLASS = DÉLIA-owned registry (DISCOVERY/READ/PREPARE/ACT);
        remote metadata never elevates a class; C3 invocable =
        DISCOVERY only (davi.discover_delpi_information,
        teo.get_catalog, vista.get_catalog)
WRITE_TOOL_FILTER = PASS | PREPARE_EXPOSURE = NONE | ACT_EXPOSURE = NONE
MCP_RESULT = untrusted OBSERVATION (never auto-FACT; never authority)
CONNECTIVITY = transport PROVEN 3/3 (reachable + OAuth 401
        fail-closed challenge from delpi-delia-api); authenticated
        DÉLIA connectivity BLOCKED — specialist MCPs accept
        user-delegated OAuth only (service tokens forbidden by
        design) and no delegation mechanism / dev realm mcp-*
        clients exist yet (IDENTITY_DELEGATION=TO_INVENTORY)
DAVI_DISCOVERY / TEO_CATALOG / VISTA_CATALOG = TEST_NOT_RUN
        (authenticated path blocked; invalid-token probe proves
        real-wire 401 -> mcp_authentication_failed mapping)
BUSINESS_READ_EXECUTION = PHASE_GATED (C4_AUTHORIZED=NO)
TARGETED_TESTS = PASS 48/48 | FULL_DELIA_API = PASS 461/461
STATIC_VALIDATION = git diff --check clean
EVIDENCE = ledger §6.92; scripts/real_mcp_interop_eval.py output
           at IMPLEMENTATION_HEAD
VERDICT = ARCHITECTURE_REVIEW_C3_MCP_INTEROP_01 = REWORK (§6.93)
NEXT = C3-MCP-INTEROP-01R1B (authenticated specialist discovery; R1A evidence pending review)
```

### C3-MCP-INTEROP-01R1A — User-Delegated Identity Foundation (ACCEPT_WITH_RESIDUAL §6.95)

```text
TASK = C3-MCP-INTEROP-01R1A — USER_DELEGATED_IDENTITY_FOUNDATION
STATE = ACCEPT_WITH_RESIDUAL (review §6.95; evidence §6.94)
EXECUTED = NO
IMPLEMENTATION_HEAD = a5512c0b5d18f728f15cf0c652ffb0e8417e8e9d
IDENTITY_MODEL = Portal user bearer (request-scoped) → single
        confidential DÉLIA backend client (delia-api) → Keycloak
        token exchange → short-lived resource-bound access token
        preserving the SAME human subject → selected specialist MCP
RESOURCE_BINDING = exactly one MCP resource audience per delegated
        token (dedicated resource audience client-scopes on the
        requester client); mcp:tools remains the generic shared
        transport scope — no resource mapper inside it
REJECTED = static global user token envs; per-specialist DÉLIA
        clients; Portal token carrying MCP resource audiences;
        service-account/impersonation substitutes
CACHE = process-local in-memory, subject+token-fingerprint+resource
        keyed, <=120s reuse / <=300s hard cap, exp-margin enforced,
        invalidation API on authentication failure
REMOVED = DELIA_MCP_{DAVI,TEO,VISTA}_USER_TOKEN runtime path
SCOPE_OUT = business MCP READ (C4-gated), PREPARE/ACT (forbidden),
        MCP SDK migration, business tool execution
NEXT_ON_SUCCESS = C3-MCP-INTEROP-01R1B —
        AUTHENTICATED_SPECIALIST_DISCOVERY
```

### C3-MCP-INTEROP-01R1B — Authenticated Specialist Discovery (EXECUTED — evidence §6.96)

```text
TASK = C3-MCP-INTEROP-01R1B — AUTHENTICATED_SPECIALIST_DISCOVERY
STATE = EXECUTED — evidence pending architecture review (§6.96)
IMPLEMENTATION_HEAD = cc65cc6388371224d955f266257d6aa3ca4967ce
RESIDUALS_CLOSED = R1B-R1 mcp-* client parity (confidential, std flow,
        PKCE S256, no DAG/service accounts, idempotent bootstrap);
        R1B-R2 credential invalidation on auth failure from ANY wire
        op (initialize/tools/list/tools/call, no auto-retry);
        R1B-R3 exchanged-token azp == delia-api fail-closed
LIVE_PROOF = Core /me context PASS -> per-specialist delegated
        credential (same_sub, azp=delia-api, resource-bound,
        mcp:tools, no foreign aud, exp valid) -> authenticated
        initialize + tools/list PASS x3 -> SpecialistInterop
        classification projection (DISCOVERY only) -> optional
        discovery calls PASS (DAVI 2 tools / TEO 24 / VISTA 8;
        blocked 1/23/7; unknown remote names none)
DEV_ALIGNMENT = public-issuer Host on exchange request;
        MCP_RESOURCE_URL pinned to canonical contracts;
        per-specialist public Host header on internal MCP addressing;
        classic 2024-11-05 negotiation (2026-07-28 envelope path is
        handshake-less; server capability floor unchanged)
UNCHANGED = no business READ (C4-gated), PREPARE/ACT forbidden,
        C4_AUTHORIZED=NO, C3_EXECUTED=NO
NEXT_ON_REVIEW_ACCEPT = C3-MCP-INTEROP-01R1C —
        SECURITY_ACCEPTANCE_AND_BIND
```

### C4-MCP-GOVERNED-READS-01 — First Governed MCP Read, DAVI / Product Master (candidate for architecture review — evidence §6.101)

```text
TASK = C4-MCP-GOVERNED-READS-01 — FIRST_GOVERNED_MCP_READ_DAVI_PRODUCT_MASTER
STATE = CANDIDATE_FOR_ARCHITECTURE_REVIEW (execution evidence §6.101)
IMPLEMENTATION_HEAD = 58a2d018d1ef28081e82e18148caa192d9d0b735
SCOPE_FREEZE = DAVI execute_delpi_information -> underlying action
        search_products only; supporting discovery
        discover_delpi_information; dev-only; no PREPARE/ACT; no A2A;
        no generic MCP proxy; no direct Product adapter
PATH = Portal user -> POST /interaction/turns -> Core /me -> DAVI
        discover -> exactly-one search_products candidate ->
        schema-bounded arguments -> DAVI execute -> API DELPI Product
        Master use case -> existing domain AuthZ -> bounded
        SpecialistOutcome (OBSERVATION) -> grounding/provenance
        projection -> user response
LIVE_PROOF = real dev read PASS (10 items for "anel" description
        search; grounding_status=GROUNDED; provenance source=
        product-master/api-delpi, specialist=davi, protocol=MCP,
        action_id=search_products; limitation result_truncated;
        unauthenticated 401; control query NON_GROUNDED)
BLOCKED = every other DAVI action; TEO READ; VISTA READ; PREPARE; ACT;
        unknown specialist/capability; caller-supplied candidate token;
        forbidden/unknown arguments
TESTS = full delia-api 532/532 PASS; MFE 36/36 + typecheck + build;
        security negative matrix incl. injection/forgery/fallback
LIVE_NEGATIVE_DOMAIN_AUTHZ = TEST_NOT_RUN (no safe second identity;
        RBAC not mutated to manufacture evidence)
UNCHANGED = C3_EXECUTED=NO, C4_AUTHORIZED=NO (phase level),
        PRODUCTION_READINESS=NOT_PROVEN
NEXT_ON_REVIEW = ARCHITECTURE_REVIEW_C4_MCP_GOVERNED_READS_01
```

### ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01 — Specialist-owned MCP catalog correction (decision §6.109; evidence §6.110)

```text
TASK = ARCH-DRIFT-MCP-FEDERATION-CATALOG-OWNER-01
TYPE = EXECUTION_DRIFT_CORRECTION (architecture correction, NOT a
        phase reset/promotion)
DRIFT = SPECIALIST_CAPABILITY_CLASSES local full-tool mirror in
        domain/specialist_interop/rules.py consulted by both
        enforcement boundaries — SUPERSEDED AS TARGET (removed)
DECISION = specialist owns catalog; DÉLIA = provider-neutral
        orchestrator; tools/list + owner _meta["delpi/toolClass"] =
        classification source; invocation = fresh owner class AND
        DÉLIA policy bindings; unknown class = discoverable, never
        invocable; discovery/metadata/model grant nothing
IMPLEMENTATION_HEAD = fe434cdaf3713c9cb0d8e752f49690ed4bd81cee
        (runtime refactor + tests)
EVIDENCE = full delia suite 652 PASS incl. auto-discovery/synthetic-
        capability, disappearance, reclassification, adversarial
        metadata, owner-class fail-closed tests; live MCP eval PASS
        3/3 (DAVI 2 tools owner-typed, TÉO 24, VISTA 8 — only
        DISCOVERY-class invocable); live governed reads DAVI+TÉO
        PASS with provenance; PREPARE/ACT blocked unchanged
PRESERVED = DAVI search_products + TÉO gpt_analyze governed slices,
        delegated identity, Core/Domain authority, truthful fallback,
        C5 foundation, PREPARE/ACT blocked
UNCHANGED = C3_EXECUTED=NO, C4_AUTHORIZED=NO (phase), C5_AUTHORIZED=NO,
        PRODUCTION_READINESS=NOT_PROVEN
STATUS = ACCEPT_WITH_RESIDUAL
        (ARCHITECTURE_REVIEW_ARCH_DRIFT_MCP_FEDERATION_CATALOG_OWNER_01R1
        =ACCEPT_WITH_RESIDUAL §6.112; prior REWORK §6.111 closed by
        doc-only reconciliation; residual
        PRODUCTION_MCP_RUNTIME=NOT_PROVEN)
NEXT_ON_EVIDENCE = PROD-MCP-RUNTIME-ALIGNMENT-01
```

### PROD-MCP-RUNTIME-ALIGNMENT-01 — Production MCP delegated-identity alignment (evidence §6.113)

```text
TASK = PROD-MCP-RUNTIME-ALIGNMENT-01
TYPE = INFRASTRUCTURE_IMPLEMENTATION + PRODUCTION_HARDENING
        (no phase advancement; no real production apply)
SCOPE = production compose/env aligned to DELIA_EXCHANGE_* contract;
        legacy DELIA_MCP_*_USER_TOKEN removed from PROD; shared
        fail-closed Keycloak provisioner (--check/--apply) extracted
        from dev bootstrap into delia_mcp_keycloak_state.py with
        DEV/PROD thin wrappers; C4 bounded read flags present, OFF
        by default; operational runbook
IMPLEMENTATION_HEAD = 9857ebbd1e174b4a752f790a1e6a3a9267ab3318
        (rework head bound at commit — see §6.115)
EVIDENCE = provisioner unit suite 23 PASS (in-memory fake KC);
        isolated real Keycloak end-to-end: check=DRIFT(2)
        → apply=APPLIED(0) → check=NO_DRIFT(0) → re-apply
        idempotent; delegated exchange 3/3 same-sub/azp=delia-api/
        resource-bound aud/mcp:tools; dev bootstrap regression on
        live dev KC; delia-api full suite 652 PASS; docker compose
        config valid DEV+PROD
REWORK = ARCHITECTURE_REVIEW_PROD_MCP_RUNTIME_ALIGNMENT_01=REWORK
        (§6.114) → R2 rework (§6.116): binding decision superseded —
        PROD stays on Keycloak 24.x (no upgrade prerequisite);
        PROD_TOKEN_EXCHANGE_MODE=KC24_LEGACY_V1 (Preview feature);
        KC_FEATURES=token-exchange,admin-fine-grained-authz (both
        required — FGAP endpoints 500/NPE without the latter, proven
        on real 24.0.5); shared engine gained explicit strategy
        (KC24_LEGACY prod / KC26_STANDARD dev) with fail-closed
        version gate; KC24 path never touches delpi-central and never
        reads/writes standard.token.exchange.enabled; isolated real
        24.0.5 check→apply→check→idempotent + exchange 3/3 (same-sub,
        azp=delia-api, resource-bound aud, mcp:tools, no
        cross-audience) + negatives (403/401/400) PASS;
        DELIA_RUNTIME_CHANGE=NO; DEV KC26 regression PASS
        (tools/list 3/3). §6.115 KC26 rehearsal kept as deferred
        migration evidence only.
PRESERVED = specialist-owned catalogs, governed DAVI/TEO reads,
        PREPARE=BLOCKED, ACT=BLOCKED, no user/password management,
        no SQL, realm/portal preconditions fail-closed
UNCHANGED = C3_EXECUTED=NO, C4_AUTHORIZED=NO (phase),
        C5_AUTHORIZED=NO, PRODUCTION_READINESS=NOT_PROVEN,
        PRODUCTION_MCP_RUNTIME=NOT_PROVEN, REAL_PRODUCTION_APPLY=
        TEST_NOT_RUN
STATUS = IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
NEXT_ON_EVIDENCE = ARCHITECTURE_REVIEW_PROD_MCP_RUNTIME_ALIGNMENT_01R1
        (independent) then future controlled apply per runbook
```
