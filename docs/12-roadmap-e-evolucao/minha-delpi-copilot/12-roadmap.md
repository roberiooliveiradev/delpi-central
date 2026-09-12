# 12 — Roadmap macro do Minha DELPI Copilot

> **Status:** planejamento canônico  
> **Produto:** aplicação standalone nova  
> **Autoridade de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
> **Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
> **Próxima etapa:** `C0.S0`

Este roadmap apresenta a evolução macro. A ordem atômica, dependências e gates vivem somente no Plano Mestre `16`.

## Visão geral

```text
C0 — Platform + Architecture + Media/Privacy/Biometric/OT Foundation Freeze
C1 — Standalone Application Bootstrap
C2 — Portal + Operational Context + Platform Commands
C3 — Intelligence Core + Multimodal/Biometric Foundations
C4 — Business Reads + DELPI Business Graph
C5 — Governed Writes + Durable Work Foundation
C6 — Tasks/Cases/Rooms/Inbox/Watch + Meeting/Frontline + Ecosystem/Learning
C7 — Autonomy + Advanced Realtime + Simulation + Model Routing + Rollout
```

## C0 — Platform + Architecture Foundation Freeze

Objetivo: entender a plataforma real e congelar boundaries, contratos e patterns antes de criar runtime.

Entregas:

- inventário Portal/Core/Gateway/Infra/MFEs/APIs;
- inventário OpenAPI/auth/entity/deep-link/events/rooms/notifications;
- inventário de browser/media APIs, streaming e storage;
- inventário de dispositivos compartilhados, tablets/kiosks/postos e infraestrutura de reunião quando existente;
- inventário de fontes de contexto industrial: OP, operação, máquina, posto, lote, produto e revisão;
- inventário de integrações/eventos OT existentes sem assumir autorização de comando;
- inventário de fontes corporativas de foto/avatar/voz, participant presence e qualquer infraestrutura biométrica existente;
- privacy/consent/retention/media policy boundaries;
- biometric enrollment/template/liveness/correction/revocation boundaries;
- Human Observation prohibited-inference boundary;
- shared-device identity/session boundaries;
- Chat analisado apenas como referência, nunca como runtime base;
- nomes/path/service/manifest/DB ownership do Copilot congelados;
- authorities/bounded contexts;
- shared primitives;
- decisão sobre necessidade de `MediaRef`, `BiometricEnrollmentRef`, `BiometricIdentityCandidate` ou equivalentes;
- Clean Architecture + Ports & Adapters + DDD pragmático;
- persistence/integration boundaries;
- Pattern Decision Matrix + Abstraction Gate;
- contract/conformance harness;
- `CHAT_RUNTIME_DEPENDENCY = 0`;
- `FOUNDATION_FREEZE = PASS`.

## C1 — Standalone Application Bootstrap

Objetivo: provar que o Copilot é uma aplicação nova e operacionalmente independente antes de investir na inteligência.

Entregas:

- `minha-delpi-copilot-api` skeleton;
- JWT validation;
- Core API integration;
- `plugins/minha-delpi-copilot` skeleton;
- Module Federation + `plugin-ui`;
- manifesto próprio;
- Gateway dev/prod próprio;
- Compose dev/prod próprio;
- full-page federated mount no Portal;
- global side-panel host contract;
- responsive/accessibility baseline;
- capability flags/media permission handling foundation;
- biometric capability UI/state OFF até os gates correspondentes;
- health/logging/config;
- rollback independente;
- prova de funcionamento com Chat desligado.

## C2 — Portal Context + Platform Commands

Objetivo: transformar o Portal em host contextual do Copilot sem mover inteligência para o Shell.

Entregas:

- Workspace Context;
- Global Copilot Bridge;
- Platform Capability Projection a partir do Core;
- `open_app`, `open_route`, `open_entity`;
- MFE context/deep-link helper;
- contexto operacional via `EntityRef` para OP/máquina/produto/operação/posto;
- bounded device/session metadata quando necessário;
- shared-device user-switch/isolation semantics;
- biometric candidate não substitui user session/RBAC;
- iframe integration baseline;
- security/generalization tests.

## C3 — Intelligence Core + Multimodal/Biometric Foundations

Objetivo: construir do zero o runtime inteligente da Copilot API e os fundamentos multimodais/biométricos sem criar experiências paralelas.

Entregas:

- provider/model abstraction baseline;
- conversation/turn state próprio;
- structured understanding;
- OpenAPI ingestion próprio;
- Copilot Action Catalog/index;
- capability retrieval;
- Expertise Packs;
- Domain Playbooks;
- Knowledge/RAG próprio;
- speech input/output baseline quando priorizado;
- multimodal document/image/drawing pipeline;
- short-video/media ingestion conforme escopo;
- media Evidence/Provenance;
- transcription foundations;
- closed-set face recognition/verification quando priorizado/aprovado;
- speaker recognition/diarization quando priorizado/aprovado;
- enrollment/template/liveness/unknown/correction lifecycle;
- bounded Human Observation quando priorizada/aprovada;
- Evidence/Provenance;
- structured planner;
- observability/evals.

Não há migração de agents/sessions/tools do Minha DELPI Chat.

## C4 — Business Reads + Business Graph

Objetivo: consultar sistemas de negócio diretamente e produzir análises cross-domain grounded.

Entregas:

- OpenAPI refresh/inventory;
- generic read executor;
- normalized Outcome/Evidence;
- DELPI Business Graph;
- permission-aware traversal;
- correlação de mídia/contexto com OP, produto, máquina, lote, manutenção, qualidade e outras entities autorizadas;
- user/person refs apontam para authority Core, não shadow biometric profile;
- cross-domain analysis;
- unknown provider/metamorphic/generalization gates.

## C5 — Governed Writes + Durable Work Foundation

Objetivo: liberar alterações governadas e criar a fundação durável usada pelas unidades de trabalho posteriores.

Entregas:

- Decision Gate Engine;
- impact preview;
- generic write executor;
- idempotency/concurrency;
- outcome verification;
- WorkflowPlan runtime;
- checkpoints;
- wait_user/wait_approval/wait_event;
- crash/retry/replay safety;
- candidate actions oriundas de voz/reunião/frontline/Human Observation passam pelo mesmo governance pipeline;
- biometric match nunca substitui final actor/session revalidation.

## C6 — Product Work + Proactivity + Meeting/Frontline + Ecosystem

Objetivo: entregar trabalho empresarial persistente e expandir o ecossistema Copilot para colaboração, reuniões e chão de fábrica.

Entregas:

- Copilot Task;
- Copilot Case + Evidence Board;
- Interaction Rooms por reuse/extend/adapter conforme C0;
- Copilot Inbox;
- Watch OBSERVE/ADVISE;
- Meeting Mode;
- face/speaker participant association governada quando habilitada;
- ata viva com decisões/evidence/actions candidatas;
- Frontline Mode;
- biometric identity assistance em shared devices quando habilitada;
- assistência hands-free;
- training assistance;
- Human Observation limitada a sinais objetivos do processo;
- process-observation knowledge candidates;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- AI-ready app SDK/readiness;
- admin/coverage.

Meeting/Frontline continuam usando a mesma Copilot API, RBAC, policy, Evidence e Durable Work.

## C7 — Autonomy + Advanced Realtime + Optimization + Rollout

Objetivo: ampliar autonomia, simulação e eficiência somente após o produto base estar comprovado.

Entregas:

- autonomia L0–L5;
- Watch ACT controlado;
- What-if/Simulation;
- Model Router/Compute Policy;
- continuous multimodal assistance somente se evidence/custo/policy justificarem;
- advanced video sampling/realtime;
- optimized biometric processing sem reduzir thresholds/governance;
- edge/device optimization quando necessária;
- room appliances/wearables como extensão futura;
- performance/cost/scaling;
- progressive rollout;
- final security/accessibility/generalization;
- Product Complete gate.

**Comando físico de máquina/OT não é consequência automática de C7.** Qualquer atuação OT requer programa/gate separado de segurança industrial.

## Dependência entre fases

```text
platform + architecture + media/privacy/biometric/OT foundations C0
↓
standalone app C1
↓
portal + operational context C2
↓
intelligence + multimodal/biometric foundations C3
↓
reads/graph/context correlation C4
↓
writes/durable foundation C5
↓
work + meeting/frontline + proactivity/ecosystem C6
↓
advanced realtime/autonomy/optimization C7
```

A ordem elimina refatorações previsíveis:

- MFE/API/paths/auth/deploy são provados antes do planner;
- media/privacy/device/biometric/OT boundaries são definidos antes de voz/câmera/video/recognition;
- `EntityRef/EvidenceRef/DecisionGate/Workflow` nascem antes de seus consumidores;
- contexto industrial reutiliza `WorkspaceContext`/`EntityRef` em vez de criar modelo paralelo;
- biometric identity aponta para user authority existente em vez de criar shadow directory;
- OpenAPI-first é nativo do Copilot, não herdado do Chat;
- Task/Case/Watch/Meeting/Frontline usam o mesmo durable/policy runtime;
- Portal hospeda, mas não recebe AI logic;
- Domain APIs continuam owners;
- câmera/voz/vídeo/biometria não ampliam permissões;
- Human Observation não vira avaliação psicológica/trabalhista;
- Chat não precisa ser corrigido, migrado ou desligado para o Copilot evoluir.

## Releases de produto

### Foundation Release
`C0`

### Standalone Bootstrap Release
`C1`

### Contextual Platform Release
`C2`

### Intelligent Multimodal/Biometric Copilot Release
`C3 + C4 reads`, somente para capabilities aprovadas no escopo

### Operational Copilot Release
`C5`

### Work + Meeting + Frontline Copilot Release
`C6`

### Mature Autonomous/Realtime Platform
`C7`

## Primeira execução

```text
C0.S0 monorepo/platform/media/device/biometric/OT inventory
→ C0.S1 boundary/names
→ C0.S2 authorities
→ C0.S3 shared primitives
→ C0.S4 architecture/persistence/privacy/media/biometric
→ C0.S5 integration contracts
→ C0.S6 RED harness
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 API skeleton
```

Estado executável: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).
