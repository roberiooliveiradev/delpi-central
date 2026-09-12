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

Evitar que inteligência, mídia, biometria ou experiência industrial sejam construídas antes de provar que a nova aplicação e seus boundaries estão corretamente integrados à plataforma.

```text
PLATFORM + ARCHITECTURE + MEDIA/PRIVACY/BIOMETRIC/OT FOUNDATIONS
→ STANDALONE APPLICATION BOOTSTRAP
→ PORTAL + OPERATIONAL CONTEXT / PLATFORM COMMANDS
→ INTELLIGENCE CORE + MULTIMODAL/BIOMETRIC FOUNDATIONS
→ BUSINESS READS + GRAPH
→ GOVERNED WRITES + DURABLE FOUNDATION
→ PRODUCT WORK + MEETING/FRONTLINE + PROACTIVITY + ECOSYSTEM
→ ADVANCED REALTIME + AUTONOMY + OPTIMIZATION + ROLLOUT
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
17. Business Graph referencia dados; não replica sistemas owners.
18. Writes usam Decision Gate + revalidation + idempotency/audit.
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
30. Reconhecimento facial/voz permitido somente como capability governada de usuários conhecidos/enrolled, com ambiguity/correction/revocation.
31. Observação humana pode descrever padrões objetivos do processo, não inferir personalidade, honestidade, emoção como verdade, saúde, atributos sensíveis ou valor profissional global.
32. Biometria/Human Observation não pode ser authority automática de contratação, promoção, punição, remuneração, avaliação formal ou desligamento.
33. Observação de processo gera candidate knowledge, nunca mudança automática de produção ou perfil secreto de trabalhador.
34. Copilot não é safety controller; autonomia empresarial L5 não implica autoridade OT.
35. `PARTIAL`, `INCONCLUSIVE`, stale evidence, duplicate authority, Chat dependency, media/privacy/biometric violation ou OT safety violation bloqueiam fechamento.

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
C3 — Intelligence Core + Multimodal/Biometric Foundations
 |
 v
C4 — Business Reads + DELPI Business Graph
 |
 v
C5 — Governed Writes + Durable Work Foundation
 |
 v
C6 — Tasks/Cases/Rooms/Inbox/Watch + Meeting/Frontline + Ecosystem/Learning
 |
 v
C7 — Advanced Realtime + Autonomy + Simulation + Model Routing + Rollout
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
- overlay/panel/drawer infrastructure para global Copilot surface;
- Workspace/context patterns;
- notifications/socket;
- theme/accessibility;
- federation share scope;
- browser media permission/capture patterns, se existirem;
- mobile/tablet/kiosk/shared-device patterns, se existirem.

### Core API

- `/me`, `/me/apps`, `/me/routes`;
- manifest registration/versioning;
- app/route/permission models;
- RBAC resolver;
- notifications;
- presence/app usage;
- audit;
- avatar/user metadata;
- corporate photo/profile source, se existir;
- integration/service auth patterns;
- device/session registration patterns, se existirem.

### Gateway/Infra

- API/MFE path conventions;
- streaming/websocket/SSE/WebRTC-related patterns;
- dev/prod parity;
- Compose profiles/services;
- postgres/storage patterns;
- object/media storage;
- encrypted sensitive storage/key-management patterns;
- health checks;
- sequential scripts;
- env examples;
- shared volumes/network;
- realtime/network limits/proxies relevantes.

### MFEs

Inventariar representativamente e depois cobrir o conjunto relevante:

- manifests;
- federation config;
- bootstrap/mount/unmount;
- `plugin-ui` consumption;
- HTTP/auth client;
- deep links/context;
- permission usage;
- current portal integrations;
- responsive/accessibility patterns;
- camera/microphone/file/media usage, se houver.

### APIs

Inventariar APIs disponíveis e seus contratos:

- `api-delpi`;
- commercial-api;
- supplies/requests/financial/customer-experience e demais APIs existentes;
- OpenAPI availability/version;
- JWT/auth middleware;
- permission requirements;
- idempotency/write semantics;
- events/websockets;
- pagination/error envelopes;
- entity IDs/deep links;
- produção/manutenção/qualidade sources para OP, operação, máquina, lote e revisão quando existirem.

### Existing collaboration/work infrastructure

- commercial interaction rooms;
- Minhas Solicitações/cases/requests;
- notifications/inbox-like concepts;
- approvals;
- event bus/jobs/workers/schedulers;
- durable workflow patterns if any;
- meeting/room/collaboration artifacts existentes;
- procedures/training sources.

### Media/Meeting/Frontline/Biometric inventory

Mapear factual e classificar:

- browser audio/video capabilities;
- speech/vision providers/config existentes;
- file/object/media storage;
- retention/privacy policies atuais;
- recording/transcription patterns;
- room hardware/processes relevantes;
- shared workstations/tablets/kiosks;
- production terminals;
- device identity/session patterns;
- network constraints no chão de fábrica;
- accessibility/noise constraints;
- existing camera/vision systems, se houver;
- existing procedure/training systems;
- corporate avatar/photo sources;
- voice sample sources, se existirem e forem aprovados;
- biometric enrollment owner/process, se existir;
- biometric template storage/key-management patterns;
- identity matching/liveness/anti-spoof capabilities já existentes;
- participant lists/presence sources;
- governance owner para biometria/Human Observation;
- prohibited inference classes e correction/revocation requirements.

Nenhum item inexistente vira `PLATFORM_REUSE` por suposição.

### Industrial/OT inventory

Somente inventário/read-only nesta etapa:

- machine/PLC/CNC/robot/SCADA/MES interfaces existentes;
- industrial events/telemetry owners;
- safety owners/interlocks;
- approved read-only APIs;
- command APIs/protocols existentes, **sem assumir que Copilot poderá utilizá-los**;
- segregation IT/OT e security owners.

### Chat — reference only

Mapear apenas para **não repetir erros** e identificar componentes neutros:

- `minha-delpi-ai-api` architecture;
- `plugins/minha-delpi-chat` federation/manifest;
- provider/RAG/multimodal patterns;
- tool/action architecture;
- known coupling/legacy problems.

Classificação permitida para qualquer finding:

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

Nunca classificar `minha-delpi-ai-api` como runtime base do Copilot.

### Saídas de C0.S0

- platform integration inventory;
- API/OpenAPI inventory;
- MFE/manifest inventory;
- shared infrastructure map;
- existing rooms/events/notifications map;
- media/device/meeting/frontline inventory;
- biometric identity/Human Observation inventory;
- privacy/retention owner inventory;
- industrial/OT boundary inventory;
- `17` atualizado;
- `18` atualizado;
- `51` revalidado;
- ledger HEAD/evidence.

**Sem runtime diff do Copilot.**

## C0.S1 — Freeze de product boundary e nomes

Congelar:

```text
backend root name
MFE root name
serviceName
container name convention
MFE basePath
API basePath
manifest id
DB/schema ownership
health path
admin paths
streaming transport direction
media storage ownership direction
biometric storage ownership direction
```

Target recomendado:

```text
minha-delpi-copilot-api/
plugins/minha-delpi-copilot/
/apps/minha-delpi-copilot
/apps/minha-delpi-copilot-api
```

Meeting/Frontline/Biometric não criam novos product backends por default.

Mudança exige evidence/ADR.

## C0.S2 — Freeze de authorities e bounded contexts

Definir owners para:

```text
identity/RBAC
portal hosting/navigation
workspace context
device identity/session
biometric enrollment/identity association
human observation
Copilot conversations
capability discovery
OpenAPI action catalog
planner
expertise/playbook
knowledge
multimodal/media
meeting semantics
frontline assistance semantics
entity/relationship projection
evidence
policy/decision
workflow/task/case
watch/inbox semantics
notification delivery
audit/evals
model/provider policy
privacy/consent/retention
industrial/OT safety boundary
```

Core continua authority do usuário corporativo; biometric subsystem apenas associa candidate `userRef`.

## C0.S3 — Freeze de shared primitives

Definir/reutilizar semanticamente:

- `CorrelationContext`;
- `EntityRef`;
- `RelationshipRef`;
- `SourceRef`;
- `EvidenceRef`;
- `OutcomeRef`;
- `CapabilityProjection`;
- `PlatformCommand/Result`;
- `WorkspaceContext`;
- `ExpertisePack/Selection/Context`;
- `DomainPlaybook`;
- `DecisionGateRequest/Decision`;
- `WorkflowPlan/Step`;
- `TaskRef`;
- `CaseRef`;
- `EventEnvelope`;
- audit contract;
- `MediaRef` **somente se C0 provar necessidade transversal**;
- `BiometricEnrollmentRef` / `BiometricIdentityCandidate` / `PersonObservationRef` **somente se C0 provar a forma correta e necessária**.

Não criar `FrontlineContext` paralelo a WorkspaceContext, outro Evidence model para mídia ou outro modelo de usuário paralelo ao Core.

C0 congela semântica; tabelas surgem apenas se necessárias.

## C0.S4 — Freeze de arquitetura/patterns/persistence/privacy/biometric boundaries

Aplicar `49` e congelar:

- layers/dependency rules;
- ports/adapters;
- composition root/DI;
- repositories;
- error/result model;
- state machine conventions;
- event/outbox conventions;
- retry/timeout/idempotency;
- frontend state ownership;
- migration policy;
- testing pattern;
- Abstraction Gate;
- ADR exception process;
- media provider boundaries;
- transient versus durable media;
- consent/capture visibility;
- retention classes;
- biometric enrollment/template/association lifecycle;
- threshold/unknown/correction/revocation semantics;
- liveness/anti-spoof requirement criteria;
- prohibited inference classes;
- shared-device session isolation;
- realtime budgets/backpressure direction;
- OT safety non-authority.

Definir storage ownership da nova Copilot API sem usar Chat tables.

## C0.S5 — Integration contracts

Congelar contratos de integração:

```text
Portal Host ↔ Copilot MFE
Portal WorkspaceContext ↔ Copilot
Copilot MFE ↔ Copilot API
Copilot API ↔ Core API
Copilot API ↔ Domain APIs
Copilot API ↔ AI/media providers/stores
Copilot API ↔ biometric providers/storage when approved
Copilot API ↔ notification/event adapters
Device/session adapter ↔ Copilot
Media capture surface ↔ Copilot media boundary
```

OT command contract **não** é criado nesta etapa apenas porque interface industrial existe. Read-only telemetry/context pode ser adaptado conforme owner/policy.

## C0.S6 — RED contract/conformance harness

Antes do runtime:

- invalid JWT;
- unauthorized Core app/route;
- invalid WorkspaceContext;
- invalid Entity/Evidence refs;
- Chat dependency detection;
- forbidden imports/dependency direction;
- invalid manifest/base path;
- invalid federation host contract;
- secret/token leakage;
- duplicate authority;
- invalid OpenAPI action contract;
- Decision hash/replay negatives;
- event duplicate;
- architecture pattern conformance;
- hidden media capture negative;
- undefined retention negative;
- shared-device user-state leak negative;
- biometric candidate granting permission negative;
- low-confidence forced identity negative;
- revoked enrollment still matching negative;
- template/log leakage negative;
- forbidden emotion/personality inference negative;
- automatic employment decision from biometric/human observation negative;
- voice modality authorization parity negative;
- screen/camera injection negative;
- arbitrary LLM→OT command negative.

## C0.S7 — FOUNDATION_FREEZE

C1 desbloqueia somente se:

```text
PLATFORM_INVENTORY = PASS
STANDALONE_BOUNDARY = PASS
NAMES_PATHS = PASS
AUTHORITIES = PASS
SHARED_PRIMITIVES = PASS
ARCHITECTURE_PATTERNS = PASS
PERSISTENCE_BOUNDARIES = PASS
INTEGRATION_CONTRACTS = PASS
MEDIA_PRIVACY_BOUNDARIES = PASS
BIOMETRIC_IDENTITY_BOUNDARY = PASS
HUMAN_OBSERVATION_BOUNDARY = PASS
SHARED_DEVICE_BOUNDARY = PASS
OPERATIONAL_CONTEXT_BOUNDARY = PASS
OT_SAFETY_BOUNDARY = PASS
CONFORMANCE_HARNESS = PASS
CHAT_RUNTIME_DEPENDENCY = 0
FOUNDATION_DUPLICATION = 0 material
```

---

# C1 — Standalone Application Bootstrap

Objetivo: provar aplicação independente antes da inteligência.

## C1.S1 — Copilot API skeleton

- novo root;
- Flask/app factory conforme padrão aprovado;
- domain/application/interfaces/infrastructure/composition;
- config/env;
- structured logging;
- `/health`;
- tests.

## C1.S2 — Authentication + Core context

- JWT validation;
- Core current-user adapter;
- `/me/apps`/routes/permission context conforme necessidade;
- no local RBAC duplication.

## C1.S3 — Copilot MFE skeleton

- novo plugin root;
- Vite/React;
- Module Federation;
- `@delpi/plugin-ui`;
- shared React;
- bootstrap/mount/unmount;
- typed host props;
- responsive/accessibility baseline;
- media permission state foundation sem auto-capture;
- biometric capability UI OFF until C0/C3 gates permit it.

## C1.S4 — Manifest + Core registration path

- manifesto próprio;
- minimal access/admin permissions;
- routes;
- backend metadata;
- registration/update scripts conforme padrão vigente.

## C1.S5 — Gateway + Compose dev/prod

- API route própria;
- MFE route própria;
- services independentes;
- no `depends_on` Chat;
- env examples;
- health;
- streaming/media transport tuning apenas quando contract exigir.

## C1.S6 — Portal full-page mount

- authorized user vê/abre app;
- remoteEntry 200;
- mount/unmount;
- token → API;
- F5/deep route;
- no Chat running requirement.

## C1.S7 — Global Copilot host contract

Implementar host mínimo no Portal para side panel/global entry, reutilizando o mesmo MFE.

Nenhuma AI logic no Portal.

## C1.S8 — Independence Gate

Desligar/ausentar Chat runtime não pode quebrar bootstrap Copilot.

```text
OWN_API = PASS
OWN_MFE = PASS
OWN_MANIFEST = PASS
OWN_GATEWAY_ROUTE = PASS
OWN_COMPOSE = PASS
JWT_CORE = PASS
FEDERATED_MOUNT = PASS
PLUGIN_UI = PASS
NO_CHAT_IMPORT = PASS
NO_CHAT_API_DEP = PASS
NO_CHAT_DB_AUTHORITY = PASS
INDEPENDENT_ROLLBACK = PASS
```

---

# C2 — Portal + Operational Context + Platform Commands

## C2.S1 — Workspace Context Store/contract

Portal/MFEs publicam contexto bounded.

Contexto operacional usa `EntityRef` para OP/máquina/produto/operação/lote/posto quando sources existem.

## C2.S2 — Copilot Global Bridge

Thin host bridge; no planner/policy in Portal.

## C2.S3 — Platform Capability Projection

Core `/me/apps`/authorized routes → semantic platform capabilities.

## C2.S4 — Commands

- open app;
- open route;
- open entity;
- view commands quando declarados.

## C2.S5 — MFE context/deep-link SDK

Helper compartilhável sem business logic.

## C2.S6 — Shared-device/session context baseline

Quando aplicável:

- user current session;
- device/workstation bounded metadata;
- capability flags mic/camera/touch/screen/biometric-ready;
- user-switch/context-clear semantics;
- device identity não concede RBAC;
- biometric candidate não é user session.

## C2.S7 — Iframe integration baseline

`PORTAL_ONLY` universal e bridge seguro para apps que suportarem.

## C2.S8 — Context/security/generalization gate

Unauthorized/stale/F5/logout/user-switch/unknown app/iframe/URL arbitrary/send-stream parity.

---

# C3 — Intelligence Core + Multimodal/Biometric Foundations

Tudo nesta fase pertence à **Copilot API nova**.

## C3.S1 — Model/provider abstraction

Port + adapter; baseline simples, sem Model Router avançado.

## C3.S2 — Conversation/turn runtime

Own session/conversation model, sem `agent_id` legado.

## C3.S3 — Structured understanding

Goals/entities/requirements/attachments/modality metadata.

## C3.S4 — Copilot OpenAPI ingestion + Action Catalog foundation

Implementação própria, OpenAPI-first.

## C3.S5 — Capability retrieval/projection

Permission-aware candidates.

## C3.S6 — Expertise Catalog/retrieval

Single Copilot; no departmental agents.

## C3.S7 — Domain Playbooks

Methodology, evidence criteria, not endpoints.

## C3.S8 — Knowledge/RAG

Copilot-owned retrieval with ACL/provenance.

## C3.S9 — Multimodal + media foundations

Implementar de forma incremental conforme escopo/evidence:

```text
document/native extraction
OCR
image/drawing vision
speech-to-text
text-to-speech
short-video ingestion
screen/camera evidence
closed-set face recognition/verification when approved
speaker recognition/diarization when approved
bounded Human Observation when approved
```

Cada provider atrás de port/adapter justificado.

Mídia gera `EvidenceRef`/`MediaRef` conforme foundation, nunca novo evidence model.

Biometric result gera candidate association; não PermissionGrant.

## C3.S10 — Media/biometric policy/session foundation

Quando voice/camera/video/biometric entrarem:

- explicit capture/identity-recognition state;
- transient versus retained media;
- retention class enforcement;
- biometric template lifecycle;
- threshold/unknown/correction/revocation;
- liveness/anti-spoof conforme finalidade;
- media session lifecycle;
- provider data policy;
- stop/cleanup behavior;
- budget/size/duration limits.

## C3.S11 — Evidence/epistemic synthesis

FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION.

Visual/audio/human-observation finding não vira fato autoritativo sem source/regra adequada.

## C3.S12 — Structured planner

Planner outputs typed plans, not technical content JSON leakage.

## C3.S13 — Intelligence/multimodal/biometric generalization gate

Positive/sibling/negative/unknown/metamorphic/injection/budget/stream/voice/image/video/identity parity.

Biometric evals incluem false accept/reject, unknown-person handling, correction, revoke/delete, spoof/replay quando aplicável e permission-elevation negative.

---

# C4 — Business Reads + DELPI Business Graph

## C4.S1 — API inventory import/refresh

Domain OpenAPIs → Copilot Action Catalog.

## C4.S2 — Generic read executor

Schema-valid, authorization-aware, outcome-normalized.

## C4.S3 — Evidence from API results

Freshness/source/outcome refs.

## C4.S4 — Business Graph runtime

EntityRef/RelationshipRef, permission-aware traversal, source fetch from owner.

## C4.S5 — Operational context correlation

Quando sources existirem, correlacionar:

```text
OP ↔ produto/revisão
operação ↔ procedimento
máquina ↔ manutenção/eventos
lote/material ↔ fornecedor/qualidade
media/evidence ↔ entity refs
person/user participation refs ↔ session/evidence only when necessary and authorized
```

Sem duplicar master data ou criar pessoa como Graph authority paralela ao Core.

## C4.S6 — Cross-domain analysis

Graph + APIs + expertise + evidence.

## C4.S7 — Unknown-provider/generalization gate

No endpoint/provider/entity hardcode.

---

# C5 — Governed Writes + Durable Work Foundation

## C5.S1 — Decision Gate Engine

Risk/sensitivity/impact/hash/approval.

## C5.S2 — Generic write executor

Final RBAC/policy revalidation and idempotency.

## C5.S3 — Outcome verification

No ambiguous success narrative.

## C5.S4 — WorkflowPlan runtime

DAG + canonical capability executor.

## C5.S5 — Checkpoints/waits

`wait_user`, `wait_approval`, `wait_event`, timeouts/cancel.

## C5.S6 — Modality-to-action governance

Candidate actions originadas de:

```text
text
voice
meeting transcript
frontline session
visual finding
human observation
```

entram no mesmo planner/Decision Gate/executor. Nenhuma modality ou biometric match executa write por canal paralelo.

## C5.S7 — crash/retry/idempotency gate

No duplicate write, inclusive após repeated utterance/event/resume.

---

# C6 — Product Work + Proactivity + Meeting/Frontline + Ecosystem

## C6.S1 — Copilot Task

## C6.S2 — Copilot Case + Evidence Board

## C6.S3 — Interaction Room integration

Reuse/extend existing owner if C0 proves it.

## C6.S4 — Copilot Inbox

Work/decision/watch/meeting-action projection.

## C6.S5 — Watch OBSERVE/ADVISE

Event-driven where available.

## C6.S6 — Organizational Knowledge

Reference/Decision/Experience/Solution Patterns.

## C6.S7 — Governed Learning

feedback/meeting/process/frontline observation → candidate → eval → review → publish.

Não persistir worker profiling secreto como aprendizado.

## C6.S8 — Expertise Studio

## C6.S9 — AI-ready app SDK/readiness

Context/Entity/deep-link/action/OpenAPI readiness.

## C6.S10 — Meeting Mode

Entregar progressivamente:

- explicit start/stop;
- voice/transcript;
- live grounded business queries;
- camera/screen/media when authorized;
- closed-set face/speaker participant recognition quando habilitado;
- ambiguity/correction UX;
- decisions/pending topics;
- candidate actions;
- ata viva;
- Task/Case/Room linkage;
- next-meeting continuity;
- retention/consent/identity-recognition visibility.

## C6.S11 — Frontline Mode

Entregar progressivamente:

- simplified/large-touch UI;
- shared-device session isolation;
- biometric identity assistance quando habilitada;
- OP/machine/product/operation context;
- hands-free voice + fallback;
- camera/image assistance;
- bounded Human Observation of process patterns;
- drawing/procedure/training help;
- issue/escalation actions through Domain APIs;
- knowledge candidate capture;
- no hidden worker profiling;
- no physical machine command path.

## C6.S12 — ecosystem/proactivity/meeting/frontline/biometric gate

Provar Meeting/Frontline surface parity de RBAC/policy/Evidence, accessibility, privacy, shared-device isolation, biometric correction/revocation, no sensitive inference, no automatic employment decisions e learning governance.

---

# C7 — Advanced Realtime + Autonomy + Optimization + Rollout

## C7.S1 — Autonomy L0–L5

L5 OFF default.

Autonomia empresarial não concede OT nem reduz biometric/user authorization requirements.

## C7.S2 — Watch ACT

Allowlisted/policy/Decision Gate.

## C7.S3 — What-if/Simulation

Only reproducible domain models.

## C7.S4 — Model Router/Compute Policy

Only after baseline metrics.

## C7.S5 — Advanced realtime/media/biometric

Somente com evidence real de valor e foundation já comprovada:

- continuous voice session optimization;
- advanced video/frame sampling;
- optimized biometric matching;
- edge processing de mídia/biometria quando necessário e aprovado;
- concurrency/backpressure;
- network degradation;
- cost/latency budgets;
- room devices/wearables como extensões futuras.

## C7.S6 — Industrial/OT safety gate

Default permanece **NO ACTUATION**.

Qualquer future OT actuation só entra após iniciativa/gate explicitamente aprovado contendo:

```text
industrial owner
risk assessment
typed deterministic commands
allowlist
machine state/preconditions
human authorization as required
independent safety PLC/interlocks
simulation/test environment
fail-safe/kill switch
audit
```

Sem isso, todo free-form LLM→machine command = BLOCK.

## C7.S7 — Scale/performance/cost

## C7.S8 — Progressive rollout

Internal → cohort → reads → writes → durable/proactive → Meeting/Frontline → governed biometrics → selected autonomy/realtime.

## C7.S9 — Final verification

Security, privacy, accessibility, unknown/sibling/metamorphic, rollback, Chat independence, biometric governance, no sensitive inference, OT boundary.

## C7.S10 — Product Complete

No material unresolved requirements for declared scope.

---

## 6. Itens antigos explicitamente removidos do roadmap

Não pertencem mais ao Copilot:

```text
migrar AgentSpecializationService do Chat
remover userActivatedAgent no Chat
substituir softAgentHandoff no Chat
migrar Chat sessions/agent_id
esperar Onda J/llm-json-decoupling do Chat
fazer cutover do Minha DELPI Chat
```

Também não pertence ao default scope:

```text
open-world/indiscriminate facial recognition
emotion/personality/character inference from face or voice
hidden employee surveillance/scoring
automatic employment decisions based on biometrics
unbounded raw-media/biometric-template retention
free-form LLM→machine control
Copilot replacing industrial safety interlocks
```

Reconhecimento fechado de usuários enrolled e Human Observation objetiva pertencem ao roadmap somente sob `54`.

## 7. Protocolo por subetapa

```text
REVALIDATE HEAD/WORKTREE
→ read 16/17/20/25/49/50/51/52/53/54 + spec applicable
→ dependency gate
→ READY_TO_EXECUTE
→ baseline
→ minimal correct owner-level diff
→ producer/consumer wiring
→ unit/contract/integration
→ positive/sibling/negative
→ security/RBAC/privacy/biometric/safety
→ generalization/metamorphic/unknown when applicable
→ independence check against Chat
→ architecture conformance
→ residual search
→ COMPLETE_GATE
→ docs/ledger
→ unlock next
```

## 8. Regra anti-refatoração

Antes de criar service/schema/table/framework/media pipeline/device context/biometric store/OT adapter:

1. pertence ao Copilot ou a platform/domain/industrial owner existente?
2. existe neutral shared owner real?
3. isso cria dependency no Chat?
4. isso duplica Core/RBAC/domain/industrial safety rules?
5. shared primitive já existe?
6. WorkspaceContext/EntityRef/EvidenceRef já resolvem o conceito?
7. próxima fase conhecida exigirá redesign?
8. pattern é justificado pelo `49`?
9. sibling/unknown funciona sem hardcode?
10. raw media/template persistence é realmente necessária?
11. modality/biometric result introduz bypass de permission/Decision?
12. device identity ou biometric candidate está sendo confundido com authenticated user?
13. Human Observation está virando inferência psicológica/sensível ou decisão trabalhista automática?
14. atuação física está sendo confundida com Business Action?

Se 3, 4, 7, 11, 12, 13 ou 14 = sim: **não implementar** até corrigir o desenho.

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

Nenhuma intelligence/media/biometric/frontline feature precede a prova de aplicação standalone e dos boundaries de privacy/device/identity/OT.