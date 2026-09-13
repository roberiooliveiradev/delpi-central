# Minha DELPI Copilot — Plano Mestre Executável

**Status:** planejamento executável canônico  
**Autoridade de ordem:** **este documento é a única fonte de verdade para a sequência de implementação**  
**Produto:** aplicação standalone nova  
**Próxima etapa:** `C0.S0`  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Bootstrap:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
**DoD:** [`14-definition-of-done.md`](./14-definition-of-done.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Decisão de execução

O Copilot será construído do zero como aplicação independente.

```text
PROIBIDO
→ evoluir minha-delpi-ai-api para virar Copilot
→ evoluir plugins/minha-delpi-chat para virar Copilot
→ esperar correções/refactors do Chat para continuar Copilot
→ compartilhar tabelas/runtime do Chat como foundation

OBRIGATÓRIO
→ nova Copilot API
→ novo Copilot MFE
→ migrations próprias
→ manifesto próprio
→ Gateway/Compose próprios
→ deploy/rollback próprios
→ integração normal com Portal/Core/Keycloak/APIs
```

O Chat é apenas sistema vizinho/referência durante o inventário.

## 2. Objetivo foundation-first

Evitar que inteligência, mídia, biometria, conectividade externa, automação autônoma, RPA ou experiência industrial sejam construídas antes de provar que a nova aplicação e seus boundaries estão corretamente integrados à plataforma.

```text
PLATFORM + ARCHITECTURE + MEDIA/PRIVACY/BIOMETRIC/EXTERNAL/AUTOMATION/OT FOUNDATIONS
→ STANDALONE APPLICATION BOOTSTRAP
→ PORTAL + OPERATIONAL CONTEXT / PLATFORM COMMANDS
→ INTELLIGENCE CORE + MULTIMODAL/BIOMETRIC/INTERNET/CONNECTOR/DECISION FOUNDATIONS
→ BUSINESS + EXTERNAL READS + GRAPH + READ-ONLY OPERATIONAL INTELLIGENCE
→ GOVERNED BUSINESS/EXTERNAL/AUTOMATION WRITES + DURABLE FOUNDATION
→ PRODUCT WORK + MEETING/FRONTLINE + EVENTS + AUTOMATION HUB + PROACTIVITY + ECOSYSTEM
→ ADVANCED REALTIME + AUTONOMOUS OPERATIONS + EXTERNAL PROACTIVITY + OPTIMIZATION + ROLLOUT
```

## 3. Authorities documentais

```text
16 = ordem
17 = ownership/contracts
20 = tests/gates
21 = state/persistence
25 = requirements
49 = code architecture/design patterns
50 = standalone product boundary
51 = current platform baseline
52 = repo/bootstrap target
53 = multimodal/Meeting/Frontline/industrial spec
54 = biometric identity/Human Observation governance
55 = Internet Research/external connectors/OAuth/external learning
56 = Microsoft Teams connector/meeting integration
57 = event-driven autonomous operations + Automation & Execution Hub
ledger = execution evidence/status
```

Specs temáticas não podem reabrir a decisão de usar Chat como base nem criar uma ordem paralela.

## 4. Invariantes

1. Copilot API é serviço independente.
2. Copilot MFE é microfrontend independente.
3. Nenhum runtime import do Chat.
4. Nenhuma tabela do Chat é authority Copilot.
5. Nenhum endpoint do Chat é proxy obrigatório para Copilot.
6. Core API continua authority de apps/rotas/RBAC.
7. Keycloak continua authority de autenticação.
8. Portal continua Shell/Router/host; não recebe AI business logic.
9. Domain APIs continuam authority de seus dados/regras.
10. `api-delpi` continua owner das integrações DELPI/TOTVS que já expõe.
11. `plugin-ui` é design system compartilhado.
12. Business Actions são OpenAPI-first nativamente no Copilot.
13. Capability Projection não duplica OpenAPI/owners.
14. Workspace Context não concede permission.
15. Expertise/Playbooks não concedem permission.
16. Shared primitives internos do Copilot nascem antes das features consumidoras.
17. Business Graph referencia dados; não replica systems of record.
18. Writes usam Decision Gate + revalidation + idempotency/audit conforme risco.
19. Durable Work não cria segundo action executor.
20. Chain-of-thought não é persistida/exposta.
21. Clean Architecture + Ports & Adapters + DDD pragmático conforme `49`.
22. Não criar abstraction/speculative generic framework sem Abstraction Gate.
23. Infraestrutura compartilhada só é reutilizada quando neutra e governada.
24. Voz/imagem/vídeo/screen share são modalidades, nunca bypass de RBAC/policy.
25. Meeting/Frontline usam a mesma Copilot API e o mesmo policy/work runtime.
26. Contexto industrial reutiliza WorkspaceContext/EntityRef; não cria authority paralela.
27. Raw media retention exige purpose/policy explícitos; data minimization é default.
28. Device identity não substitui user identity.
29. Biometric match não substitui authenticated session/Core permission.
30. Reconhecimento facial/voz é capability governada de usuários conhecidos/enrolled, com ambiguity/correction/revocation.
31. Human Observation descreve fatos/padrões objetivos do processo, não personalidade, honestidade, emoção como verdade, saúde ou valor profissional global.
32. Biometria/Human Observation não é authority automática de decisão trabalhista.
33. Observação de processo gera candidate knowledge, nunca mudança automática de produção.
34. Internet/external content é untrusted data; nunca altera system/policy/RBAC/retention.
35. Web fetch passa por boundary seguro de egress.
36. OAuth/provider scopes seguem least privilege e não substituem Core/domain authorization.
37. Provider credentials/tokens nunca entram em prompt, LLM context, MFE ou logs comuns.
38. Conexão pessoal não vira fonte organizacional implicitamente.
39. External read e external write são capabilities diferentes; `draft != send`.
40. External write usa Policy/Decision Gate quando material e exige verified outcome.
41. Provider events/webhooks convergem para EventEnvelope, dedupe e reconciliation.
42. Informação externa durável vira candidate Knowledge antes de publicação.
43. WhatsApp não usa scraping de sessão pessoal como integração default.
44. Teams é capability family do Microsoft 365 connector, não runtime paralelo.
45. **Copilot = inteligência/contexto/decisão/orquestração; Automation & Execution Hub = execução.**
46. **RPA é executor substituível; business rule/decision não pertence ao bot.**
47. **Executor preference: API → integração nativa → função/script → RPA → computer-use → humano.**
48. Planner trabalha com capability semântica; nunca com click/selector/coordenada de RPA.
49. Nem todo evento chama LLM; FAST/OPERATIONAL/REASONING paths são distintos.
50. Readiness material usa facts/rules/Policy verificáveis quando disponíveis; LLM não é autoridade única.
51. Event payload nunca concede autorização nem side effect por si só.
52. Background/autonomous action usa identidade explícita de usuário/serviço e revalidation.
53. Technical executor success não equivale automaticamente a business success; Outcome deve ser verificado quando material.
54. Autonomia é capability/context/risk scoped; não existe L4/L5 global irrestrito.
55. L5 permanece OFF por default e exige allowlist/budgets/kill switch.
56. Watch `PREPARE` é distinto de `ACT`.
57. Computer-use é fallback avançado/sandboxed, não primeiro executor.
58. Copilot não é safety controller; autonomia empresarial L5 não implica autoridade OT.
59. `PARTIAL`, `INCONCLUSIVE`, stale evidence, duplicate authority, Chat dependency, media/privacy/biometric/external/automation violation ou OT safety violation bloqueiam fechamento.

## 5. Grafo canônico

```text
C0 — Platform + Architecture Foundation Freeze
 |
 v
C1 — Standalone Application Bootstrap
 |
 v
C2 — Portal + Operational Context + Platform Commands
 |
 v
C3 — Intelligence + Multimodal/Biometric/External/Decision Foundations
 |
 v
C4 — Business + External Reads + Business Graph + Operational Read Intelligence
 |
 v
C5 — Governed Business/External/Automation Writes + Durable Work Foundation
 |
 v
C6 — Tasks/Cases/Rooms/Inbox/Watch + Meeting/Frontline + Automation Hub + Events/Learning
 |
 v
C7 — Autonomous Operations + Advanced Realtime + External Proactivity + Optimization + Rollout
```

---

# C0 — Platform + Architecture Foundation Freeze

## C0.S0 — Rebaseline factual do monorepo

Inventariar com arquivo/símbolo/contrato/owner/consumer.

### Portal

- `AuthContext`/Keycloak lifecycle;
- `AppHost` federated lifecycle;
- AppLauncher/menu/routes;
- `getAccessToken` host props;
- full-page layouts;
- overlay/panel/drawer infrastructure;
- Workspace/context patterns;
- notifications/socket;
- theme/accessibility;
- federation share scope;
- browser media permission/capture patterns;
- mobile/tablet/kiosk/shared-device patterns.

### Core API

- `/me`, `/me/apps`, `/me/routes`;
- manifest registration/versioning;
- app/route/permission models;
- RBAC resolver;
- notifications;
- presence/app usage;
- audit;
- avatar/user metadata;
- corporate photo/profile source;
- integration/service auth patterns;
- device/session registration patterns.

### Gateway/Infra

- API/MFE path conventions;
- streaming/websocket/SSE/WebRTC patterns;
- dev/prod parity;
- Compose profiles/services;
- postgres/storage patterns;
- object/media storage;
- encrypted sensitive storage/key-management patterns;
- outbound HTTP/proxy/DNS/egress patterns;
- SSRF/private/link-local/metadata blocking patterns;
- secrets/vault owner;
- OAuth callback route patterns;
- webhook ingress/signature validation patterns;
- health checks;
- sequential scripts;
- env examples;
- shared volumes/network;
- queues/brokers/workers/schedulers;
- service-account/background identity patterns;
- desktop/session infrastructure usable por automação, se existir.

### MFEs

- manifests/federation/bootstrap/mount/unmount;
- `plugin-ui` usage;
- HTTP/auth clients;
- deep links/context;
- permission usage;
- responsive/accessibility;
- camera/microphone/file/media usage;
- external connection/settings UX;
- automation/admin/execution UX existente, se houver.

### APIs

- `api-delpi` e demais APIs existentes;
- OpenAPI availability/version;
- JWT/auth middleware;
- permissions;
- idempotency/write semantics;
- events/websockets;
- pagination/error envelopes;
- entity IDs/deep links;
- produção/manutenção/qualidade sources para OP/operação/máquina/lote/revisão;
- business postcondition/outcome sources para writes materiais.

### Existing collaboration/work infrastructure

- interaction rooms;
- requests/cases;
- notifications/inbox-like concepts;
- approvals;
- event bus/jobs/workers/schedulers;
- durable workflow patterns;
- meeting/collaboration artifacts;
- procedures/training sources.

### Media/Meeting/Frontline/Biometric inventory

Mapear browser audio/video, speech/vision providers, storage, retention/privacy, recording/transcription, room hardware, shared devices, production terminals, device identity, network constraints, biometric enrollment/templates/providers/liveness, participant/presence sources e governance owner.

### Internet/External Connector inventory

Mapear search/web research, safe fetch/browser automation, Microsoft Graph/Google Workspace/WhatsApp Business/Slack/GitHub connectors, OAuth flows, token storage/rotation/revocation, provider webhooks/subscriptions, reconciliation, attachment scanning, provider compliance/data classification.

### Automation / RPA / Autonomous Operations inventory

Mapear factual e classificar:

- ferramentas RPA/orchestrators/licenças existentes;
- bots/robots/packages e owners;
- automações desktop/web atuais;
- scripts/functions/jobs automatizados;
- queues/workers/worker pools/heartbeats;
- schedulers/polling jobs;
- event sources/brokers/topics/streams;
- service accounts/background identities;
- credential injection/storage owners;
- desktop/session/VDI execution environments;
- package/version/deploy/rollback patterns;
- retry/idempotency patterns;
- RPA screenshots/artifacts/logging/retention;
- existing rule/decision engines;
- process engines/BPM/workflow owners;
- business postcondition/outcome verification sources;
- notification/escalation channels;
- kill switch/emergency-stop patterns;
- automation ownership/governance/SLA/support.

Não assumir ferramenta RPA específica nem criar um novo Hub antes de provar ownership/gap.

### Microsoft Teams inventory

Seguir `56`: Entra app registrations, Graph scopes, resource-specific consent, chats/channels/meetings/transcripts/recordings/change notifications, app/tab/bot distribution, ACL/privacy e realtime-media constraints.

### Industrial/OT inventory

Somente inventário/read-only: machine/PLC/CNC/robot/SCADA/MES interfaces, telemetry owners, safety owners/interlocks, approved read APIs, command APIs/protocols sem assumir uso, segregation IT/OT.

### Chat — reference only

Mapear arquitetura/providers/RAG/multimodal/actions somente para evitar dívida/reuso indevido.

Classificação:

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

### Saídas de C0.S0

- platform integration inventory;
- API/OpenAPI inventory;
- MFE/manifest inventory;
- rooms/events/notifications/work inventory;
- media/device/meeting/frontline/biometric inventory;
- Internet/egress/OAuth/external connector inventory;
- Teams inventory;
- **automation/RPA/event/queue/worker/service-identity inventory**;
- privacy/retention/external-data inventory;
- industrial/OT boundary inventory;
- `17` atualizado;
- `18` atualizado;
- `51` revalidado;
- ledger HEAD/evidence.

**Sem runtime diff do Copilot.**

## C0.S1 — Freeze de product boundary e nomes

Congelar backend/MFE roots, service/container conventions, paths, manifest id, DB/schema ownership, health/admin/OAuth/webhook paths, egress/media/biometric/external connection ownership e **Automation & Execution Hub ownership direction**.

Target recomendado continua:

```text
minha-delpi-copilot-api/
plugins/minha-delpi-copilot/
/apps/minha-delpi-copilot
/apps/minha-delpi-copilot-api
```

Automation Hub não vira novo microservice automaticamente. C0 decide módulo/bounded context/neutral platform service somente por evidence/ADR.

## C0.S2 — Freeze de authorities e bounded contexts

Definir owners para identidade/RBAC, hosting, Workspace Context, biometric identity, conversations, planner, Expertise/Knowledge, media, Internet Research, external connections/actions/events, Teams, **Event/Signal ingestion, Decision Intelligence, Automation Capability Registry, Executor lifecycle, RPA worker/queue integration, outcome verification**, Meeting/Frontline, Evidence, Policy/Decision, Workflow/Task/Case/Watch/Inbox, notifications, audit/evals e OT safety.

Domain APIs continuam business authorities. Automation/RPA não vira business authority.

## C0.S3 — Freeze de shared primitives

Definir/reutilizar CorrelationContext, EntityRef, RelationshipRef, SourceRef, EvidenceRef, OutcomeRef, CapabilityProjection, PlatformCommand/Result, WorkspaceContext, Expertise/Playbook, DecisionGate, WorkflowPlan/Step, TaskRef, CaseRef, EventEnvelope, audit contract, MediaRef/biometric/external refs somente se necessários.

Para automation, preferir reutilizar `CapabilityProjection`, `EventEnvelope`, `OutcomeRef`, `WorkflowStep` e CorrelationContext antes de criar primitive nova. `AutomationExecutionRef`/`ExecutorRef` só entram se C0 provar necessidade transversal.

## C0.S4 — Freeze de arquitetura/patterns/persistence/privacy/automation boundaries

Aplicar `49` e congelar layers/DI/repositories/errors/state machines/events/outbox/retry/idempotency/frontend state/migrations/tests/Abstraction Gate, media/biometric/external boundaries e adicionalmente:

- event source trust/authenticity;
- dedupe/ordering/correlation;
- polling fallback semantics;
- FAST/OPERATIONAL/REASONING decision path contract;
- deterministic readiness Policy/Specification rules;
- executor preference and selection boundary;
- semantic automation capability contract;
- background service/user identity;
- execution lifecycle/correlation/idempotency;
- RPA worker/queue/package/credential boundaries;
- computer-use sandbox boundary;
- postcondition/outcome verification;
- notification/escalation truth semantics;
- capability-scoped autonomy and kill switches.

## C0.S5 — Integration contracts

Congelar contratos Portal↔MFE, MFE↔API, API↔Core/Domain/AI/media/biometric/internet/external/secret/event/device, e:

```text
Event Source ↔ Event Adapter ↔ EventEnvelope
Copilot Work/Decision ↔ Automation Capability Registry
Copilot Work ↔ Executor Port
Executor Adapter ↔ API/Function/RPA/Computer-Use runtime
Execution lifecycle ↔ Outcome Verifier
Outcome ↔ Notification/Evidence/Audit
```

OT command contract não é criado nesta etapa.

## C0.S6 — RED contract/conformance harness

Adicionar aos negatives existentes:

- forged/untrusted event creates action;
- duplicate event causes duplicate execution;
- event payload grants authorization;
- planner emits RPA click/selector details;
- RPA chosen despite authoritative supported API without approved exception;
- background action without explicit user/service identity;
- executor success accepted as business success without required postcondition verification;
- ambiguous executor timeout blindly retried;
- workflow resume duplicates RPA/API effect;
- RPA credential/session leaks across workers/users;
- `PREPARE` silently transitions to `ACT`;
- global L5 enables unrelated capabilities;
- autonomous action ignores kill switch/budget/limit;
- computer-use accesses non-allowlisted app/network;
- free-form LLM→OT command.

## C0.S7 — FOUNDATION_FREEZE

C1 desbloqueia somente se gates anteriores +:

```text
AUTOMATION_EXECUTION_BOUNDARY = PASS
EVENT_SIGNAL_BOUNDARY = PASS
BACKGROUND_IDENTITY_BOUNDARY = PASS
EXECUTOR_CONTRACT_BOUNDARY = PASS
OUTCOME_VERIFICATION_BOUNDARY = PASS
AUTONOMY_SCOPE_BOUNDARY = PASS
```

---

# C1 — Standalone Application Bootstrap

Objetivo: provar aplicação independente antes da inteligência.

## C1.S1 — Copilot API skeleton

Novo root, Flask/app factory conforme padrão, layers, config/logging, `/health`, tests.

## C1.S2 — Authentication + Core context

JWT/Core current-user/apps/routes/permission context sem local RBAC duplication.

## C1.S3 — Copilot MFE skeleton

Vite/React/Module Federation/plugin-ui/bootstrap/mount/unmount/typed host props/responsive/accessibility. Nenhuma media/biometric/external/automation execução automática.

## C1.S4 — Manifest + Core registration path

Manifesto próprio, minimal permissions/routes/backend metadata/registration scripts.

## C1.S5 — Gateway + Compose dev/prod

Rotas/serviços próprios, no Chat dependency, env/health; callback/webhook paths somente se C0 contract exigir.

## C1.S6 — Portal full-page mount

Authorized mount/F5/deep route/token→API/Chat independence.

## C1.S7 — Global Copilot host contract

Thin host; no AI logic no Portal.

## C1.S8 — Independence Gate

OWN API/MFE/Manifest/Gateway/Compose/JWT/Core/Federation/plugin-ui + NO_CHAT_* + independent rollback.

---

# C2 — Portal + Operational Context + Platform Commands

WorkspaceContext bounded, Global Bridge, Platform Capability Projection, typed navigation commands, MFE context/deep-link SDK, shared-device baseline, iframe baseline e security/generalization gate. Automation context pode referenciar capability/execution status somente como bounded refs; não concede execution authority.

---

# C3 — Intelligence Core + Multimodal/Biometric/External/Decision Foundations

Tudo pertence à Copilot API nova.

## C3.S1–S10

Mantêm provider abstraction, conversation runtime, structured understanding, OpenAPI Action Catalog, Capability retrieval, Expertise, Playbooks, Knowledge/RAG, multimodal/media/biometric foundations e policies conforme specs canônicas.

## C3.S11 — Internet Research foundation

SearchProviderPort + SafeWebFetchPort + Source/Evidence/freshness, safe egress/injection controls.

## C3.S12 — External Connection foundation

OAuth/API authorization → ExternalConnection → secretRef → provider adapter → normalized capabilities.

## C3.S13 — Event/Decision Intelligence foundation

Introduzir contratos e policies, sem material ACT:

```text
authorized event/signal
→ EventEnvelope
→ context need
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
→ structured finding/decision candidate
```

Requisitos:

- nem todo evento chama LLM;
- FAST usa deterministic Policy/State Machine;
- OPERATIONAL usa bounded reads/rules e modelo pequeno/classifier somente se necessário;
- REASONING usa Graph/Knowledge/Expertise/LLM;
- critical readiness com regra verificável não vira prompt-only decision;
- event payload não altera policy/authorization.

## C3.S14 — Evidence/epistemic synthesis

FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION.

## C3.S15 — Structured planner

Typed plans, sem RPA clicks/selectors/provider UI detail.

## C3.S16 — Intelligence/generalization gate

Positive/sibling/negative/unknown/metamorphic/injection/media/biometric/external/event-decision parity.

---

# C4 — Business + External Reads + Business Graph + Operational Read Intelligence

- API inventory/import/refresh;
- generic business reads;
- external reads;
- Evidence normalization;
- Business Graph;
- operational/external correlation;
- cross-domain analysis.

## C4 — additional operational intelligence requirement

Read-only readiness/anomaly use cases podem calcular, por exemplo:

```text
invoice readiness
production report plausibility
stock risk
supplier delay risk
machine downtime context
```

Sem side effect nesta fase. Resultado deve distinguir FACT/CALCULATION/HYPOTHESIS e referenciar authoritative sources.

---

# C5 — Governed Business/External/Automation Writes + Durable Work Foundation

## C5.S1 — Decision Gate Engine

Risk/sensitivity/impact/hash/approval.

## C5.S2 — Generic business write executor

Final RBAC/policy revalidation/idempotency.

## C5.S3 — External write executor/adapters

Draft/send/calendar/message/file actions conforme `55/56`.

## C5.S4 — Automation Capability Registry/Projection

Registrar/mapping versionado de semantic capability para executor disponível:

```text
capabilityRef
→ executorRef/version/type
→ input/output schema
→ pre/postconditions
→ timeout/retry/idempotency
→ owner/environment/status
```

Planner nunca recebe click/selector/coordenada.

## C5.S5 — Executor Ports/Adapters

Implementar somente executors priorizados por evidence:

```text
Domain/API Executor
Function/Script Executor
RPA Executor
Computer-Use Executor only if already justified
Notification Executor
Human Task Adapter
```

API permanece preferida quando owner contract suporta a operação.

## C5.S6 — AutomationExecution lifecycle

```text
QUEUED → RUNNING → SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT
```

Correlation/inputHash/attempt/idempotency/error/result refs. RPA worker/queue/lease/heartbeat somente se RPA for priorizado.

## C5.S7 — Outcome verification

Technical success é separado de business postcondition. Verificar via Domain API/event/authoritative record sempre que material.

## C5.S8 — Durable Workflow runtime/checkpoints/waits

Workflow continua único orquestrador de capabilities/executors.

## C5.S9 — Modality/source/event-to-action governance

Texto, voz, meeting, frontline, web, external message ou event entram no mesmo Decision/Workflow/executor path. Nenhuma origem cria canal de write paralelo.

## C5.S10 — crash/retry/idempotency gate

No duplicate API/external/RPA effect after timeout/retry/resume.

---

# C6 — Product Work + Proactivity + Meeting/Frontline + Automation Hub + Ecosystem

Task, Case, Room, Inbox, provider events, external subscriptions, Knowledge/Learning, Expertise Studio, AI-ready, Meeting e Frontline seguem specs existentes.

## C6 — Watch evolution

Watch modes canônicos:

```text
OBSERVE
ADVISE
PREPARE
```

`ACT` permanece bloqueado em C6.

`PREPARE` pode montar action args/preview/draft/work plan sem side effect.

## C6 — Automation & Execution Hub product/admin

Quando C5 executor foundation estiver comprovada, expor gradualmente:

- Automation Catalog/mappings;
- executions/queue/status;
- worker health/capabilities/environment quando RPA existir;
- failures/ambiguous outcomes;
- exceptions waiting human decision;
- version/owner/autonomy policy;
- success versus verified-outcome metrics;
- kill-switch status;
- Task/Case/Workflow correlation.

Hub não cria segundo Workflow engine nem segundo planner.

## C6 — Notifications/escalations

Outcome/event/Watch podem notificar por Minha DELPI, email, Teams, WhatsApp Business e channels aprovados, com recipient/severity/dedupe/SLA/escalation policy.

Manual exception deve pausar/retomar o mesmo Durable Workflow.

---

# C7 — Autonomous Operations + Advanced Realtime + External Proactivity + Optimization + Rollout

## C7.S1 — Autonomy L0–L5

Autonomia é capability/context/risk scoped. L5 OFF default.

## C7.S2 — Watch ACT / Autonomous Operations

Selecionados somente após allowlist/policy/budgets/identity/revalidation/kill switch:

```text
Event
→ Watch ACT
→ context/decision path
→ AutonomyPolicy
→ Durable Workflow
→ semantic capability
→ Executor
→ verified Outcome
→ Evidence/Audit
→ Notification
```

Anchor obrigatório quando faturamento autônomo fizer parte do declared scope:

```text
ready-to-invoice
→ deterministic readiness
→ autonomy allowed
→ billing.invoice.issue
→ API/RPA executor
→ verify invoice exists/valid
→ notify
```

## C7.S3 — What-if/Simulation

Only reproducible domain models.

## C7.S4 — Model Router/Compute Policy

Only after baseline metrics.

## C7.S5 — Advanced realtime/media/biometric

Somente com evidence real.

## C7.S6 — Advanced external automation/browser/computer-use

Somente com evidence e scope explícito. Computer-use é sandboxed/allowlisted/credential-isolated, same Policy/Decision semantics, kill switch, audit; não substitui API/RPA determinístico por conveniência.

## C7.S7 — Industrial/OT safety gate

Default NO ACTUATION. Qualquer future physical actuation exige iniciativa/gate separado com industrial owner, risk assessment, typed deterministic commands, allowlist, machine-state checks, human authorization conforme risco, independent safety PLC/interlocks, simulation/test, fail-safe/kill switch e audit.

## C7.S8 — Scale/performance/cost

Incluir event throughput, decision latency, queue latency, worker utilization, executor cost, outcome verification latency e autonomy incident metrics.

## C7.S9 — Progressive rollout

Internal → reads → governed writes → executor foundation → PREPARE watches → automation admin → selected ACT → capability-scoped L5 → advanced computer-use/realtime somente quando justified.

## C7.S10 — Final verification

Security/privacy/accessibility/unknown/metamorphic/rollback/Chat independence/biometric/external/automation/OT boundaries.

## C7.S11 — Product Complete

No material unresolved requirements for declared scope.

---

## 6. Itens explicitamente fora do roadmap/default scope

Antigas migrações de agents do Chat permanecem fora do escopo.

Também não pertence ao default scope:

```text
open-world facial recognition
psychological/personality inference
hidden employee surveillance
unbounded raw media/biometric retention
unrestricted web/browser access
provider tokens in LLM/MFE
personal external source auto-promotion
implicit draft→send
personal WhatsApp Web scraping
planner emitting raw RPA clicks/selectors
RPA as business-rule authority
one global unrestricted L5 mode
event payload directly executing write
blind retry after ambiguous RPA/API write
computer-use with unrestricted corporate-network access
free-form LLM→machine control
Copilot replacing industrial safety interlocks
```

## 7. Protocolo por subetapa

```text
REVALIDATE HEAD/WORKTREE
→ read 16/17/20/25/49/50/51/52/53/54/55/56/57 + spec applicable
→ dependency gate
→ READY_TO_EXECUTE
→ baseline
→ minimal correct owner-level diff
→ producer/consumer wiring
→ unit/contract/integration
→ positive/sibling/negative
→ security/RBAC/privacy/biometric/external/automation/safety
→ generalization/metamorphic/unknown
→ independence check against Chat
→ architecture conformance
→ residual search
→ COMPLETE_GATE
→ docs/ledger
→ unlock next
```

## 8. Regra anti-refatoração

Antes de criar service/schema/table/framework/media pipeline/device context/biometric store/external connector/web fetcher/event bus/RPA hub/executor registry/worker queue/computer-use/browser automation/OT adapter, provar:

1. owner real?
2. neutral shared owner existente?
3. cria dependency no Chat?
4. duplica Core/RBAC/domain/provider/safety authority?
5. shared primitive já resolve?
6. próxima fase exige redesign?
7. pattern justificado pelo `49`?
8. sibling/unknown provider/executor funciona sem planner hardcode?
9. persistence realmente necessária?
10. token/credential fica protegido?
11. read/write e PREPARE/ACT continuam separados?
12. event payload está sendo confundido com permission/action authority?
13. deterministic rule suficiente está sendo substituída desnecessariamente por LLM?
14. API autoritativa existe e mesmo assim RPA está sendo escolhido sem justificativa?
15. technical success está sendo confundido com business Outcome?
16. automation background identity está explícita/auditável?
17. autonomy está scoped ou virou global?
18. computer-use pode atingir app/network fora do allowlist?
19. atuação física está sendo confundida com Business Action?

Se houver violation material: **não implementar** até corrigir o desenho.

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

Nenhuma intelligence/media/biometric/Internet/connector/Teams/RPA/automation/frontline feature precede a prova da aplicação standalone e dos boundaries de privacy/device/identity/egress/credentials/event/execution/outcome/autonomy/OT.
