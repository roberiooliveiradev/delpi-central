# 12 — Roadmap macro do Minha DELPI Copilot

> **Status:** planejamento canônico  
> **Autoridade de execução atômica:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Próxima etapa:** `C0.S0`

Este documento apresenta a evolução macro. A ordem de subetapas, dependências e gates vive somente no Plano Mestre.

## Visão geral

```text
C0 — Fundação arquitetural e contratos universais
C1 — Portal, navegação, entidades e Workspace Context
C2 — Intelligence Core: Copilot único, expertise, knowledge, multimodal e evidence
C3 — Business Reads + DELPI Business Graph
C4 — Governed Writes + Decision Gates
C5 — Durable Work: Workflows + Tasks + Cases + Rooms + Inbox
C6 — Proatividade + AI-ready Ecosystem + Governed Learning
C7 — Optimization + Autonomia + Simulation + Model Routing + Rollout
```

## C0 — Fundação arquitetural

Objetivo: estabilizar o vocabulário e as peças compartilhadas antes de qualquer feature dependente.

Entregas macro:

- inventário real de Portal/Core/AI/apps/agents/events/workflows/rooms/notifications;
- authorities e bounded contexts congelados;
- primitives compartilhados de entidade, fonte, evidence, capability, contexto, expertise, decisão, workflow, task, case e eventos;
- ports/persistence boundaries;
- versioning/correlation/idempotency/freshness/error semantics;
- contract harness;
- `FOUNDATION_FREEZE=PASS`.

Não construir feature do Copilot antes desse freeze.

## C1 — Portal e contexto

Objetivo: permitir que o Copilot saiba **onde o usuário está** e navegue com segurança.

Entregas:

- authorized Platform Capability Projection;
- CopilotBridge;
- open app/route/entity;
- Workspace Context Store;
- MFE context/deep-link adapter;
- Iframe Bridge;
- context UX e generalization tests.

## C2 — Intelligence Core

Objetivo: estabilizar a inteligência transversal antes de Business Actions em escala.

Entregas:

- sessão do Copilot sem agent obrigatório;
- Expertise Catalog/retrieval/composition;
- Domain Playbooks;
- Knowledge ACL integration;
- multimodal evidence;
- provenance/epistemic synthesis;
- shadow migration do modelo de agents;
- observabilidade operacional.

## C3 — Business Reads + Business Graph

Objetivo: conectar o Copilot aos dados reais de negócio com evidence e contexto cross-domain.

Entregas:

- Business Capability Projection a partir do Action Catalog;
- generic read parity;
- normalized outcomes/evidence;
- DELPI Business Graph mínimo;
- permission-aware traversal;
- análises cross-domain.

**Dependência:** gates OpenAPI-first relevantes da Minha DELPI AI precisam estar `PASS` para produção.

## C4 — Governed Writes + Decision Gates

Objetivo: liberar alterações somente com governança proporcional ao risco.

Entregas:

- Decision Gate Engine;
- impact preview + hash;
- confirmação/aprovação;
- idempotency/concurrency;
- generic write execution;
- outcome verification;
- remoção do gate operacional dependente de agent ativo;
- substituição do soft handoff por retrieval/replan/clarify.

## C5 — Durable Work

Objetivo: sair da limitação do turno/chat para trabalho que dura minutos, horas ou dias.

Entregas:

- Durable Workflow Runtime;
- checkpoints e wait states;
- DAG runner;
- Copilot Tasks;
- Copilot Cases + Evidence Board;
- Interaction Rooms;
- Copilot Inbox;
- reload/restart/resume sem duplicate writes.

## C6 — Proatividade + Ecossistema + Aprendizado Governado

Objetivo: permitir acompanhamento contínuo e crescimento do ecossistema sem hardcode central.

Entregas:

- Watch `OBSERVE/ADVISE`;
- AI-ready SDK/templates;
- readiness scanner/onboarding waves;
- project preferences;
- Organizational Knowledge;
- Governed Learning Loop;
- Expertise Studio;
- admin/coverage.

## C7 — Optimization, autonomia e rollout

Objetivo: ampliar autonomia e otimizar custo/latência somente depois das bases estarem comprovadas.

Entregas:

- autonomia L0–L5;
- Watch `ACT` controlado;
- What-if/Simulation pilots;
- Model Router/Compute Policy;
- cutover final do agent-routing legado;
- canary/rollback;
- final R1–R11 e Product Complete gate.

## Dependência entre as camadas

```text
primitives C0
↓
context/navigation C1
↓
intelligence/evidence C2
↓
reads/graph C3
↓
writes/decision C4
↓
durable work C5
↓
proactivity/ecosystem C6
↓
optimization/autonomy C7
```

A ordem existe para evitar refatorações previsíveis. Exemplo:

- `EvidenceRef` nasce em C0, não quando Case aparecer;
- `DecisionGate` nasce em C0 e executa em C4, não depois de writes;
- `Workflow/Task/Case` têm lifecycle semântico em C0 e persistência em C5;
- `EntityRef/RelationshipRef` nascem antes do Business Graph;
- expertise/playbook contracts nascem antes de agent migration;
- event envelope nasce antes de Watch.

## MVPs

### MVP de plataforma

```text
C0 + C1
```

Navega e entende contexto sobre fundações estáveis.

### MVP inteligente

```text
C2 + C3 reads
```

Copilot único, expertise, multimodalidade, evidence e consultas cross-domain.

### MVP operacional

```text
C4
```

Primeiros writes governados e verificáveis.

### MVP de trabalho

```text
C5
```

Tasks/Cases/Rooms/Inbox com workflows duráveis.

### Plataforma madura

```text
C6 + C7
```

Proatividade, learning governance, autonomia seletiva e otimização.

## Primeira implementação

```text
C0.S0 rebaseline/inventory
→ C0.S1 authorities/bounded contexts
→ C0.S2 shared primitives
→ C0.S3 persistence boundaries
→ C0.S4 cross-cutting semantics
→ C0.S5 contract harness
→ C0.S6 FOUNDATION_FREEZE
→ C1.S1
```

Estado executável: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).