# 15 — Mapa de integração com a Minha DELPI atual

## Componentes existentes a evoluir

### `minha-delpi-ai-api`

Reutilizar/evoluir:

- entendimento/decomposição;
- memory/context;
- Action Catalog;
- retrieval/planner;
- OpenAPI validation;
- policy/confirmation;
- executor;
- RAG;
- synthesis/presentation;
- observability/evals.

Adicionar gradualmente:

- Capability abstraction acima de Actions;
- Platform Capability adapter/port;
- Workspace Context ingestion;
- workflow state/checkpoints;
- navigation observations.

### `plugins/minha-delpi-chat`

Reutilizar/evoluir:

- composer;
- streaming/activity;
- rich presentation;
- conversation state;
- agents/projects.

Adicionar:

- context chips;
- confirmation cards estruturados;
- workflow progress;
- navigation status;
- painel/presentation adaptado ao modo Copilot quando necessário.

### `portal`

Adicionar:

- `CopilotBridge`;
- `PlatformCapabilityCatalog`;
- `WorkspaceContextBridge`;
- registry de adapters dos MFEs;
- validação de Platform Commands;
- integração com Router/AuthContext/apps autorizados.

### Core API

Reutilizar:

- `/me`;
- `/me/apps`;
- `/me/routes`/contrato equivalente;
- permissions/RBAC;
- apps/manifests/routes.

Avaliar extensão somente se necessária para metadata semântica de capabilities de Portal, mantendo Core como owner de governança e não de inteligência LLM.

### APIs de negócio

Reutilizar/evoluir OpenAPI e use cases. Evitar endpoints exclusivos “para IA” quando a operação já pertence ao domínio existente.

## Fluxo completo esperado

```text
Portal AuthContext
→ authorized apps/routes
→ Platform Capability Catalog
                  ┐
OpenAPI Actions ──┼→ Authorized Capability View
Knowledge tools ──┘
         │
         ▼
minha-delpi-ai-api planner
         │
         ├─ Business Action → API/use case
         ├─ Platform Action → CopilotBridge
         ├─ Knowledge → RAG
         └─ Analysis/Artifact → services
         │
         ▼
observations + results
         │
         ▼
response/renderPlan/activity
         │
         ▼
plugins/minha-delpi-chat + Portal
```

## Ownership

| Conceito | Owner recomendado |
|---|---|
| capability domain model | `minha-delpi-ai-api/domain` |
| capability orchestration | `minha-delpi-ai-api/application` |
| OpenAPI adapter | `minha-delpi-ai-api/infrastructure` |
| Portal capability adapter | Portal + port no AI API |
| workspace context contract | contrato compartilhado Portal/Copilot |
| business rules | API/use case do domínio proprietário |
| RBAC | Core/API backend |
| navigation execution | Portal Shell |
| renderização | plugin-ui/chat MFE |
| policy/confirmation | AI/application+domain, respaldada pelo backend |

## Regra de evolução

Antes de criar componente novo, verificar se a responsabilidade já existe no chat base ou Portal. O Copilot deve ser uma evolução coordenada, não duplicação da plataforma.
