# 02 — Arquitetura

## 1. Objetivo arquitetural

O Copilot deve ser uma camada transversal sobre a arquitetura atual da Minha DELPI, reutilizando identidade, RBAC, Core API, Portal Shell, `minha-delpi-ai-api`, OpenAPI Action Catalog, RAG e MFEs.

Não criar um produto paralelo à plataforma.

## 2. Componentes

```text
Portal Shell
├─ Router
├─ AuthContext
├─ Apps/Routes autorizados
├─ Copilot UI
├─ CopilotBridge
└─ WorkspaceContextBridge

minha-delpi-ai-api
├─ Turn Understanding
├─ Context/Memory
├─ Capability Retrieval
├─ Planner
├─ Policies/Confirmation
├─ Action Execution
├─ RAG/Knowledge
├─ Analysis/Synthesis
└─ Observability/Evals

Core API
├─ identidade efetiva
├─ apps/rotas
├─ permissions/RBAC
└─ auditoria/governança

Business APIs
├─ api-delpi
├─ APIs de portais
├─ serviços específicos
└─ integrações externas OpenAPI
```

## 3. Pipeline canônico

```text
mensagem + workspace context
→ segurança/input validation
→ structured understanding
→ goals/subtasks/dependencies
→ authorized capability discovery
→ retrieval/ranking
→ structured plan
→ policy/RBAC/sensitivity
→ confirm quando necessário
→ generic execution
→ observations/results
→ analysis/synthesis
→ renderPlan + UI commands
→ persistence/audit
```

## 4. Tipos de capability

```text
Business Action
→ operação de negócio via API/use case

Platform Action
→ operação do Portal/Shell

Knowledge Capability
→ RAG/search/documentos

Analysis Capability
→ transformação/comparação/síntese grounded

Artifact Capability
→ geração de relatório/mensagem/arquivo

Workflow Capability
→ composição governada de múltiplas capabilities
```

## 5. Fonte de verdade por responsabilidade

| Conceito | Fonte de verdade |
|---|---|
| identidade | Keycloak + Core context |
| permissões efetivas | Core API |
| apps/rotas autorizadas | `/core-api/me/apps` / contratos equivalentes |
| operação de negócio | API/use case + OpenAPI |
| contrato técnico de action | OpenAPI + Action Catalog |
| confirmação/sensitivity | policy determinística |
| contexto visual atual | Portal/MFE Workspace Context |
| conhecimento documental | fontes RAG autorizadas |
| navegação | Platform Capability Catalog derivado do Portal |
| apresentação de dados | schema/payload/metadata → renderPlan |

## 6. Princípio UI ↔ Copilot

A UI e o Copilot devem convergir para os mesmos use cases.

```text
MFE/UI ──────┐
             ▼
       Business Use Case/API
             ▲
Copilot ─────┘
```

Automação de UI só deve ser usada para ações verdadeiramente visuais, como navegação, foco, troca de aba ou aplicação de preferência local.

## 7. CopilotBridge

Responsável no Portal por receber **Platform Commands tipados** e validá-los antes da execução.

Exemplos:

```json
{
  "type": "portal.open_app",
  "target": { "appId": "portal-suprimentos" }
}
```

```json
{
  "type": "portal.open_entity",
  "target": {
    "entityType": "purchaseRequest",
    "entityId": "SC-00123"
  }
}
```

O LLM não produz `window.location`, URL arbitrária nem código React. Ele escolhe uma capability conhecida e o Portal executa o comando validado.

## 8. WorkspaceContextBridge

Responsável por sincronizar contexto útil do Portal/MFE com o Copilot:

```text
appId
routeId
entityRefs
filters
dateRange
selection
visibleDataRefs
presentationState
```

O contexto deve ser pequeno, estruturado, versionado e sem despejar estado React completo.

## 9. Capability Discovery

O planner não recebe o universo inteiro indiscriminadamente.

```text
permissions efetivas
→ capabilities permitidas
→ semantic retrieval
→ top-K
→ planner restrito aos candidates
```

O mesmo princípio já usado para Actions OpenAPI deve ser expandido para capabilities da plataforma.

## 10. Execução agentic

O executor deve operar em ciclos observáveis:

```text
PLAN
→ ACT
→ OBSERVE
→ UPDATE STATE
→ CONTINUE | COMPLETE | CLARIFY
```

Limites de segurança e custo controlam número de passos, tools, retries e profundidade.

## 11. Persistência

Persistir estado suficiente para continuidade sem depender de reinterpretação total:

- goals;
- selected capabilities;
- resolved entities;
- resolved arguments;
- pending requirements;
- result references;
- workspace context relevante;
- confirmations;
- audit events.

Não persistir chain-of-thought.

## 12. Clean Architecture

### Domain

- modelos de capability;
- policies puras;
- contracts de plan/confirmation;
- regras de autonomia.

### Application

- discover capabilities;
- plan task;
- execute workflow;
- bind arguments;
- coordinate confirmation;
- build response/render commands.

### Infrastructure

- Core/RBAC gateway;
- OpenAPI catalog repository;
- Portal capability repository;
- HTTP execution;
- LLM provider;
- persistence;
- vector/search adapters.

### Interfaces

- REST/SSE;
- Portal events;
- admin endpoints.

### Composition

- DI/wiring de implementations concretas.

## 13. Requisitos de escalabilidade

- novo app não exige editar o planner central;
- novo endpoint OpenAPI não exige selector dedicado;
- capabilities podem ser indexadas e buscadas semanticamente;
- catálogos podem ser materializados/cacheados;
- execução deve ser idempotente quando contrato permitir;
- writes precisam de correlation/audit ids;
- workflows longos precisam checkpoints e recuperação.
