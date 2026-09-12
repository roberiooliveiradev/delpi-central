# 12 — Roadmap macro do Minha DELPI Copilot

> **Status:** planejamento canônico  
> **Produto:** aplicação standalone nova  
> **Autoridade de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Próxima etapa:** `C0.S0`

Este roadmap apresenta a evolução macro. A ordem atômica, dependências e gates vivem somente no Plano Mestre `16`.

## Visão geral

```text
C0 — Platform + Architecture Foundation Freeze
C1 — Standalone Application Bootstrap
C2 — Portal Context + Platform Commands
C3 — Intelligence Core
C4 — Business Reads + DELPI Business Graph
C5 — Governed Writes + Durable Work Foundation
C6 — Tasks/Cases/Rooms/Inbox/Watch + Ecosystem/Learning
C7 — Autonomy + Simulation + Model Routing + Rollout
```

## C0 — Platform + Architecture Foundation Freeze

Objetivo: entender a plataforma real e congelar boundaries, contratos e patterns antes de criar runtime.

Entregas:

- inventário Portal/Core/Gateway/Infra/MFEs/APIs;
- inventário OpenAPI/auth/entity/deep-link/events/rooms/notifications;
- Chat analisado apenas como referência, nunca como runtime base;
- nomes/path/service/manifest/DB ownership do Copilot congelados;
- authorities/bounded contexts;
- shared primitives;
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
- iframe integration baseline;
- security/generalization tests.

## C3 — Intelligence Core

Objetivo: construir do zero o runtime inteligente da Copilot API.

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
- multimodal/document/drawing pipeline;
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
- cross-domain analysis;
- unknown provider/metamorphic/generalization gates.

Não existe dependência da Onda J ou do runtime do Chat.

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
- crash/retry/replay safety.

## C6 — Product Work + Proactivity + Ecosystem

Objetivo: entregar trabalho empresarial persistente e expandir o ecossistema Copilot.

Entregas:

- Copilot Task;
- Copilot Case + Evidence Board;
- Interaction Rooms por reuse/extend/adapter conforme C0;
- Copilot Inbox;
- Watch OBSERVE/ADVISE;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- AI-ready app SDK/readiness;
- admin/coverage.

## C7 — Autonomy + Optimization + Rollout

Objetivo: ampliar autonomia, simulação e eficiência somente após o produto base estar comprovado.

Entregas:

- autonomia L0–L5;
- Watch ACT controlado;
- What-if/Simulation;
- Model Router/Compute Policy;
- performance/cost/scaling;
- progressive rollout;
- final security/accessibility/generalization;
- Product Complete gate.

## Dependência entre fases

```text
platform + architecture C0
↓
standalone app C1
↓
portal context C2
↓
intelligence core C3
↓
reads/graph C4
↓
writes/durable foundation C5
↓
work/proactivity/ecosystem C6
↓
autonomy/optimization C7
```

A ordem elimina refatorações previsíveis:

- MFE/API/paths/auth/deploy são provados antes do planner;
- `EntityRef/EvidenceRef/DecisionGate/Workflow` nascem antes de seus consumidores;
- OpenAPI-first é nativo do Copilot, não herdado do Chat;
- Task/Case/Watch usam o mesmo durable runtime;
- Portal hospeda, mas não recebe AI logic;
- Domain APIs continuam owners;
- Chat não precisa ser corrigido, migrado ou desligado para o Copilot evoluir.

## Releases de produto

### Foundation Release
`C0`

### Standalone Bootstrap Release
`C1`

### Contextual Platform Release
`C2`

### Intelligent Copilot Release
`C3 + C4 reads`

### Operational Copilot Release
`C5`

### Work Copilot Release
`C6`

### Mature Autonomous Platform
`C7`

## Primeira execução

```text
C0.S0 monorepo/platform inventory
→ C0.S1 boundary/names
→ C0.S2 authorities
→ C0.S3 shared primitives
→ C0.S4 architecture/persistence
→ C0.S5 integration contracts
→ C0.S6 RED harness
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 API skeleton
```

Estado executável: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).