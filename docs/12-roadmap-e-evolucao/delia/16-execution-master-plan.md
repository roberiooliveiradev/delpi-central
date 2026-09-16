# DÉLIA — Plano Mestre Executável

**Status:** planejamento executável canônico  
**Autoridade de ordem:** **este documento é a única fonte de verdade para a sequência de implementação**  
**Produto:** **DÉLIA**, aplicação standalone nova  
**Próxima etapa:** `ARCHITECTURE_REVIEW_C0_S3` (`C0.S0..=C0.S2=APPROVED`; `C0.S3=CANDIDATE_FOR_ARCHITECTURE_REVIEW`; `C0.S4_AUTHORIZED=NO`; C0 permanece `NOT_STARTED`; `FOUNDATION_FREEZE=NOT APPROVED`; `DÉLIA_RUNTIME_DIFF=NONE`)
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
C0.S3_AUTHORIZED = YES
C0.S3 = CANDIDATE_FOR_ARCHITECTURE_REVIEW
C0.S4_AUTHORIZED = NO
FOUNDATION_FREEZE = NOT APPROVED
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
DÉLIA_RUNTIME_DIFF = NONE
NEXT = ARCHITECTURE_REVIEW_C0_S3
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

**C0.S3-T2 (docs):** decisões persistidas em `21` §4 + `17` §3 + `25` §17 + ledger §6.26. Estado: `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. **Não** aceito; **não** autoriza C0.S4; `NEW_RUNTIME_ABSTRACTIONS=NONE`; `DÉLIA_RUNTIME_DIFF=NONE`.

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

## C0.S5 — Integration contracts

Congelar typed contracts para platform/domain/external/event/automation/**recurring-work trigger**/process/model/sandbox/edge boundaries. O contrato deve separar DÉLIA-owned recurring definition/occurrence correlation do scheduler físico. Nenhum provider SDK/tool protocol/scheduler-specific type vaza para Domain/Application canônicos.

## C0.S6 — RED contract/conformance/privacy/security harness

Required negatives incluem:

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

---

# C1 — Standalone Application Bootstrap

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
- shared-device/session cleanup;
- operational context OP/machine/product/operation/posto;
- no memory/Edge/device/tool/provider state as permission authority.

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