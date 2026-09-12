# 15 — Mapa de integração com a Minha DELPI atual

**Status:** mapa canônico de integração  
**Ordem de implementação:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Princípio

O Copilot evolui os owners existentes antes de criar novos componentes.

```text
REUSE
→ EXTEND
→ MIGRATE
→ CREATE_REQUIRED somente com gap provado
```

## 2. `minha-delpi-ai-api`

### Reutilizar/evoluir

- understanding/decomposition;
- conversation/memory;
- Action Catalog;
- retrieval/planner;
- OpenAPI validation/binding;
- generic action executor;
- RAG/Knowledge;
- multimodal/document vision;
- synthesis/presentation;
- policy/safety;
- persistence;
- observability/evals;
- model/provider abstraction.

### Evoluir para

- single-Copilot session model;
- Capability Projection;
- Expertise Catalog/Retrieval/Context;
- Domain Playbook Catalog/Adapter;
- Evidence/Provenance normalization;
- Decision Gate orchestration;
- durable workflow coordination;
- Task/Case orchestration ports;
- Business Graph query/use cases;
- Watch/event coordination;
- Organizational Knowledge governance;
- Compute Policy/Model Router quando C7 liberar.

### Não criar

- segundo planner;
- segundo HTTP executor;
- agent runtime por departamento;
- manual endpoint catalog;
- CoT store.

## 3. `plugins/minha-delpi-chat`

### Reutilizar/evoluir

- composer;
- streaming/activity;
- rich presentation;
- conversation/history;
- feedback;
- attachments;
- project context onde fizer sentido.

### Adicionar/evoluir

- context chips;
- sources/evidence presentation;
- epistemic labels quando material;
- Decision Gate UI;
- Task/Workflow progress;
- Case/Inbox entry points quando disponíveis;
- navigation/platform command presentation;
- single-Copilot UX sem agent selector obrigatório.

### Migrar

- agent selection/handoff UX → expertise/project preferences ou remover conforme plano de migração.

## 4. Portal Shell

### Reutilizar

- Router;
- AuthContext;
- authorized apps/routes;
- AppHost;
- shell lifecycle.

### Adicionar/evoluir

- Authorized Platform Capability Projection;
- CopilotBridge;
- Workspace Context Store/Bridge;
- Entity deep-link resolver;
- MFE context adapter contract;
- IframeBridge;
- global Copilot surface;
- Inbox/Task/Case navigation surfaces quando C5 liberar.

Portal executa Platform Actions e valida targets; não executa business rules.

## 5. Core API

Reutilizar como authority de:

- identidade/contexto do usuário;
- apps/routes;
- permissions/RBAC;
- app registration/manifests;
- audit/governance onde aplicável.

Avaliar extensão somente se C0 provar gap de metadata de plataforma. Não mover inteligência LLM, Expertise ou Business Graph semantic reasoning para Core apenas por conveniência.

## 6. APIs de domínio

Continuam owners de negócio.

Devem ser reutilizadas/evoluídas para:

- OpenAPI de qualidade;
- consistent entity identifiers;
- source timestamps/version quando material;
- idempotency em writes quando possível;
- domain events quando já fizerem sentido;
- clear authorization;
- outcomes verificáveis.

Evitar endpoints exclusivos “para IA” se o use case já existe no domínio.

## 7. MFEs

Responsabilidades AI-ready possíveis:

- Workspace Context;
- EntityRefs;
- deep-link metadata;
- visual commands;
- contextual entry points;
- source/result presentation.

Não duplicam business rules/RBAC server-side.

## 8. Apps iframe

Integração progressiva:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Portal/IframeBridge cuida de context/visual commands. Business Actions continuam por APIs.

## 9. Shared UI / plugin-ui

Reutilizar componentes para:

- activity;
- status;
- Decision Gate cards;
- evidence/source disclosure;
- Entity cards;
- Task/Case status;
- Inbox items;
- timeline;
- accessibility patterns.

Não criar visuais incompatíveis por plugin quando shared component atende.

## 10. Knowledge/RAG

Reutilizar current ingestion/search/ACL owners.

Evoluir para distinguir, quando necessário:

```text
Reference Knowledge
Operational Knowledge
Decision Knowledge
Experience Knowledge
```

Expertise/Project preference não amplia ACL.

## 11. Multimodal runtime

Reutilizar document vision/drawing analysis existentes.

Adapter normaliza para EvidenceRef com:

- attachment/source;
- page/region;
- confidence;
- extractor/model version;
- limitations.

Não acoplar a agent ativo.

## 12. Event infrastructure

C0 deve inventariar:

- existing event bus;
- socket/event patterns;
- background workers/queues;
- domain events;
- notification patterns.

Watch e `wait_event` devem usar owner existente quando adequado. Não criar event bus paralelo sem gap provado.

## 13. Rooms/interaction

C0 deve mapear salas já implementadas nos Portais.

Meta:

```text
CaseRef ↔ RoomRef
```

Copilot integra contexto/resumo/pending actions, sem duplicar message/file storage se owner existente atende.

## 14. Notifications/Inbox

Inventariar notification center/patterns existentes.

Copilot Inbox deve preferir view/materialization sobre:

- Decision Gates;
- Tasks;
- Cases;
- Workflows;
- Watch alerts.

Não criar workflow engine dentro da Inbox.

## 15. Business Graph

### Sources

- Entity IDs dos domínios;
- domain relationships/events/contracts;
- explicit inferred relationships quando autorizadas.

### Owner

Copilot/Platform pode manter relationship registry/index e query port, mas source objects continuam nas APIs donas.

### Fluxo

```text
EntityRef
→ RelationshipRef traversal
→ permission check
→ related EntityRefs/SourceRefs
→ fetch current data from owner API
```

## 16. Decision/Approval integration

C0 deve inventariar confirmation/approval mechanisms existentes.

Target é um `DecisionGate` compartilhado, reutilizando infra atual quando suficiente.

Não criar “confirmation card backend” e “approval workflow backend” independentes sem necessidade.

## 17. Durable Workflow integration

C0 deve mapear jobs/queues/workflow/background infrastructure.

Runtime C5 deve reutilizar:

- scheduler/worker infra;
- persistence primitives;
- locks/idempotency;
- event handling;

quando compatíveis.

O orchestration layer continua chamando executors canônicos.

## 18. Model/provider integration

C0 inventaria provider abstraction e metrics.

C7 Compute Policy/Model Router deve ficar centralizada na AI API/infrastructure, não distribuída em Skills/Features.

## 19. Fluxo completo alvo

```text
Keycloak/Core
→ identity + permissions + apps/routes

Portal/MFE/Iframe
→ Workspace + Entity Context

OpenAPI Actions ─┐
Platform Actions ├→ Authorized Capability View
Knowledge ───────┤
Internal Tools ──┘

Goals/Context
→ Expertise/Playbooks
→ Knowledge/Multimodal Evidence
→ Planner
→ Policy/Decision Gate
→ canonical executor(s)
→ Domain API/Portal/Internal Tool
→ Outcome/Evidence
→ Workflow/Task/Case state when durable
→ Presentation/Inbox/Room/Watch
→ Audit/Evals
```

## 20. Integration rule

Antes de criar componente:

```text
Does owner already exist?
Can existing contract be extended?
Would new component duplicate an authority?
Would next known phase force this contract to change?
```

Se houver duplicação ou refatoração previsível, voltar ao C0 foundation design antes de implementar.