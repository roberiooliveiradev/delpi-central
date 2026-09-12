# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem de implementação:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Regra:** cada responsabilidade possui um owner canônico. Projeções, caches, indexes, expertise e playbooks são derivados/orientadores; não viram segunda authority.

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Consumidores principais | Proibido |
|---|---|---|---|
| identidade | Keycloak + integração Core | Portal, APIs, AI | identidade técnica superuser do Copilot |
| permissões efetivas | Core API/RBAC | Portal, AI, APIs | permission derivada de prompt/expertise/context |
| apps/rotas autorizados | Core `/me/apps`/equivalente | Portal Capability Projection | lista manual app→URL no Copilot |
| negócio | APIs/use cases de domínio | UI, Copilot | regra de negócio no frontend/LLM |
| contrato técnico de Business Action | OpenAPI + Action Catalog | capability retrieval/executor | catálogo manual por endpoint |
| navegação visual | Portal Shell/CopilotBridge | Chat/Copilot | URL arbitrária do LLM |
| workspace visual | Portal + MFE/iframe adapters | AI turn context | usar contexto como autorização |
| entity identity | owner de domínio + canonical `EntityRef` adapter | Context, Graph, Case, Evidence | inventar IDs paralelos |
| relationships | domain owner + Business Graph relationship registry | Graph/traversal | copiar dataset operacional inteiro |
| capability projection | derivada de authorities | retrieval/planner/UX | virar source técnica independente |
| expertise | Expertise Catalog | retriever/context composer | conceder permission/tools |
| playbook | Domain Playbook Catalog | planner | conter endpoint como authority |
| knowledge visibility | Knowledge ACL + identity/policy | RAG/AI | pack/projeto ampliar ACL |
| multimodal perception | extractor/service versionado | evidence pipeline | tratar OCR/VLM como conclusão |
| evidence/provenance | source owner + Evidence contract | synthesis/Case/audit | claim material sem fonte quando disponível |
| policy/sensitivity | Policy/Safety server-side | writes/workflows/watch | instrução LLM relaxar policy |
| decision gate | Policy + approval owner | write/workflow | confirmação visual ser authority final |
| workflow/task/case | orchestration application owner | Portal/Inbox/Rooms | segundo executor HTTP |
| room/collaboration | owner existente de sala, se reutilizável | Case/Copilot | ACL implícita por membership |
| inbox | Portal/work orchestration | usuário | read item disparar write |
| events/watch | event owner + watch policy | workflows/alerts | polling app-specific central |
| organizational knowledge | knowledge governance | Copilot/expertise | auto-publicar conversa como verdade |
| model/compute policy | AI infrastructure/policy | runtime | seleção ad hoc espalhada em features |
| audit/observability | infraestrutura canônica | admin/evals | CoT, secrets, JWT |

## 2. Componentes

| Componente | Responsabilidade |
|---|---|
| Portal Shell | experiência global, Router, workspace ativo |
| CopilotBridge | validar/executar Platform Commands |
| IframeBridge | bridge seguro de contexto/comandos visuais |
| Chat MFE | UX conversacional/activity/decision UI/rendering |
| `minha-delpi-ai-api` | understanding, retrieval, planning, orchestration, synthesis |
| Action Catalog | representação operacional derivada do OpenAPI |
| Capability Projection | índice autorizado de capabilities |
| Expertise Catalog/Retriever | especialização dinâmica |
| Playbook Catalog/Adapter | método de domínio para planejamento |
| Knowledge/RAG | conhecimento autorizado |
| Multimodal Adapter | percepção estruturada de arquivos/imagens/desenhos |
| Policy/Safety | allow/deny/gate/autonomy |
| Durable Workflow Runtime | checkpoints/waits/resume, reutilizando executors canônicos |
| DELPI Business Graph | referências/relacionamentos permission-aware |
| Case/Task services | unidades de trabalho persistente |
| Observability | traces/metrics/audit/evidence de execução |

## 3. Primitive registry — definidos semanticamente em C0

C0 deve **reutilizar equivalentes existentes** antes de criar qualquer novo schema. Os nomes abaixo são conceituais.

### 3.1 Correlação

`CorrelationContextV1`

```text
requestId
conversationId
turnId
workflowId?
taskId?
caseId?
traceId?
```

Usado transversalmente; não criar IDs desconectados por feature.

### 3.2 `EntityRefV1`

```json
{
  "entityType": "product",
  "entityId": "90264238",
  "sourceSystem": "api-delpi",
  "label": "90264238"
}
```

É referência lógica, não snapshot do objeto inteiro.

### 3.3 `RelationshipRefV1`

```json
{
  "from": {"entityType":"complaint","entityId":"R1"},
  "relationshipType": "concerns_product",
  "to": {"entityType":"product","entityId":"90264238"},
  "authority": "domain",
  "sourceRef": "...",
  "confidence": 1.0
}
```

Distinguir relação authoritative de inferred.

### 3.4 `SourceRefV1`

Referência à origem verificável:

```text
sourceType
sourceId/provider
entityRef?
action/result ref?
document/attachment ref?
timestamp/freshness
```

### 3.5 `EvidenceRefV1`

```text
evidenceId
sourceRef
kind
value/ref
location?
observedAt
freshness
confidence?
limitations[]
```

Classification separada:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

`FACT`/`CALCULATION` precisam provenance suficiente quando material.

### 3.6 `OutcomeRefV1`

Representa outcome real de uma capability/action, com status, entity refs/result refs e evidence associável.

### 3.7 `PlatformCommandV1` / `PlatformCommandResultV1`

Targets lógicos (`appId`, `routeId`, `EntityRef`), nunca URL livre.

### 3.8 `WorkspaceContextV1`

```text
appId
routeId
entityRefs[]
filters
selection
dateRange
visibleDataRefs[]
source
updatedAt
```

Bounded, sanitizado, sem token e sem datasets completos.

### 3.9 `CapabilityProjectionV1`

Contém semântica para retrieval/UX + `sourceRef` canônico. Não copia OpenAPI inteiro nem vira executor.

### 3.10 Especialização

- `ExpertisePackV1`;
- `ExpertiseSelectionV1`;
- `ExpertiseContextV1`;
- `DomainPlaybookV1`.

Regras:

```text
expertise/playbook ≠ permission
expertise/playbook ≠ endpoint catalog
```

### 3.11 `MultimodalEvidenceRefV1`

Attachment/document ref + observations + page/region + confidence + extractor/version + limitations.

### 3.12 Decision Gate

`DecisionGateRequestV1`:

```text
decisionId
capability/action ref
impact summary
arguments hash
evidence refs
risk/sensitivity
required gate level
expiresAt
```

`DecisionGateDecisionV1`:

```text
decisionId
decision/approval state
actor ref
decidedAt
```

Níveis:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

### 3.13 Workflow e trabalho persistente

- `WorkflowPlanV1`;
- `WorkflowStepV1`;
- `TaskRefV1`;
- `CaseRefV1`.

Contrato C0 define IDs/status/relações; persistência/runtime só em C5 após inventário.

### 3.14 `EventEnvelopeV1`

```text
eventId
eventType
source
entityRefs[]
occurredAt
payloadRef/payload bounded
correlation
```

Semântica de dedupe e replay definida em C0; Watch vem depois.

### 3.15 `IframeBridgeEnvelopeV1`

Fonte detalhada: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).

### 3.16 Audit event

Usar contrato existente se houver; precisa correlacionar user/request/workflow/capability/policy/decision/outcome sem armazenar CoT.

## 4. Producer → consumer graph

```text
Keycloak
→ Core identity/RBAC
→ allowed apps/routes/actions/knowledge

Core /me/apps
→ Platform Capability Projection
→ AI retrieval
→ PlatformCommand
→ CopilotBridge
→ Router/MFE/Iframe

OpenAPI
→ Action Catalog
→ allowed Business Actions
→ Capability Projection
→ retrieval/planner
→ policy/Decision Gate
→ generic executor
→ domain API
→ OutcomeRef/EvidenceRef

Workspace MFE/Iframe
→ WorkspaceContext
→ AI understanding/retrieval

Attachments
→ multimodal extraction
→ EvidenceRef
→ expertise/playbook/analysis

Expertise content
→ Expertise Catalog/index
→ retrieval
→ bounded ExpertiseContext

Playbook
→ applicability
→ WorkflowPlan guidance

EntityRefs + RelationshipRefs
→ Business Graph traversal
→ source API fetch
→ EvidenceRef

WorkflowPlan
→ Durable Workflow Runtime
→ Task/Case
→ waits/Inbox/Room/Watch
```

## 5. Anti-duplication rules

Não criar:

- `CaseEntityRef` incompatível com `EntityRef`;
- `WorkflowEvidence` diferente de `EvidenceRef` sem motivo material;
- confirmation schema separado de Decision Gate;
- event envelope próprio para Watch se `EventEnvelope` existe;
- outro result/outcome type só para Business Graph;
- second Action Catalog;
- agent-specific tool registry como authority final;
- memory paralela por app/case;
- graph table que replique objetos inteiros da API.

## 6. C0 inventory questions obrigatórias

Antes de criar cada primitive, responder:

```text
Existe equivalente atual?
Quem produz?
Quem consome?
É público/externo?
Tem persistence?
Tem migration consumers?
Tem versioning?
Tem tests?
Pode ser estendido sem quebrar contrato?
```

Quando não houver prova: `NOT_PROVEN`, não inventar.

## 7. Ordem de estabilização

```text
Authorities
→ primitives
→ ports/persistence boundaries
→ contract tests
→ FOUNDATION_FREEZE
→ feature implementations
```

A implementação concreta de uma feature não pode redefinir primitive já congelado sem abrir explicitamente uma mudança arquitetural/versionada.