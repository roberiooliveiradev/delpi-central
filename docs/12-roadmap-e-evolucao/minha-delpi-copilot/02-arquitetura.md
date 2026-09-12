# 02 — Arquitetura do Minha DELPI Copilot

**Status:** arquitetura alvo canônica  
**Ordem de construção:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo arquitetural

O Minha DELPI Copilot é uma camada transversal sobre a plataforma existente, reutilizando:

- Gateway;
- Keycloak;
- Core API/RBAC;
- Portal Shell;
- `minha-delpi-ai-api`;
- Chat MFE;
- OpenAPI + Action Catalog;
- RAG/Knowledge;
- multimodalidade;
- APIs de domínio;
- MFEs e iframes.

Não criar um produto ou stack de IA paralelos.

## 2. Princípio do Copilot único

Existe um único Copilot de produto.

```text
NÃO
usuário → agente Engenharia → handoff → agente Qualidade

SIM
usuário → Minha DELPI Copilot
→ goals/context
→ capabilities autorizadas
→ expertise/playbooks
→ knowledge/evidence
→ planner
→ policy
→ execution
```

Domínios especializam o mesmo runtime por Expertise Packs, Domain Playbooks, Knowledge scopes e tools.

## 3. Foundation-first

A arquitetura é organizada em duas dimensões:

### 3.1 Foundations compartilhadas

```text
Identity/RBAC
Correlation
Entity/Relationship refs
Source/Evidence/Outcome refs
Capability contracts
Workspace Context
Expertise/Playbook contracts
Decision Gate contracts
Workflow/Task/Case lifecycles
Event envelope
Audit/Observability
```

### 3.2 Features construídas sobre as foundations

```text
Navigation
Context
Expertise
Multimodal analysis
Business Reads
Business Graph
Business Writes
Durable Work
Cases/Rooms/Inbox
Watch
Learning
Simulation
Model Routing
```

Uma feature não pode redefinir foundation já existente.

## 4. Arquitetura macro

```text
                               USUÁRIO
                                  │
                       Portal / Chat / Case UX
                                  │
                      Workspace + Entity Context
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Minha DELPI Copilot     │
                    │      AI Runtime         │
                    └────────────┬────────────┘
                                 │
       ┌─────────────────────────┼──────────────────────────┐
       ▼                         ▼                          ▼
Understanding             Capability Retrieval       Expertise/Playbooks
       │                         │                          │
       └──────────────┬──────────┴──────────────┬───────────┘
                      ▼                         ▼
               Knowledge/Evidence         Structured Planner
                      │                         │
                      └─────────────┬───────────┘
                                    ▼
                         Policy / Decision Gate
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              Platform Actions Business Actions Internal Tools
                     │              │              │
                     ▼              ▼              ▼
               Portal Bridge   Generic Executor  RAG/Vision/etc
                                    │
                                    ▼
                              Domain APIs
                                    │
                                    ▼
                         Outcome / Evidence
                                    │
                              Observe/Replan
```

## 5. Camadas de runtime

### 5.1 Experience Layer

Owners:

- Portal Shell;
- Chat MFE;
- MFEs;
- iframe adapters;
- Task/Case/Inbox UX.

Responsável por apresentação/interação, não autorização real de negócio.

### 5.2 Intelligence Layer

Owner principal: `minha-delpi-ai-api`.

Responsabilidades:

- structured understanding;
- goal decomposition;
- capability retrieval;
- expertise/playbook retrieval;
- knowledge/evidence composition;
- planning;
- synthesis;
- workflow orchestration;
- recommendation;
- presentation plan.

### 5.3 Policy/Safety Layer

Responsável por:

- allowed capabilities;
- sensitivity/risk;
- Decision Gates;
- autonomy policy;
- provider data policy;
- limits/budgets;
- confirmation/approval;
- audit requirements.

LLM não relaxa policy.

### 5.4 Execution Layer

Reutiliza executors canônicos:

```text
Platform → CopilotBridge/Portal handlers
Business → Action Catalog + generic HTTP executor
Knowledge → RAG/search tools
Multimodal → document/image/drawing adapters
```

Durable Workflow coordena executors; não os duplica.

### 5.5 State/Work Layer

Responsável por:

- workflow checkpoints;
- Tasks;
- Cases;
- waits;
- decision refs;
- event resume;
- Inbox materialization.

## 6. Canonical pipeline

```text
input/message/event
+ WorkspaceContext
+ entity refs
+ attachments
+ durable work state quando aplicável

→ input/security validation
→ structured understanding
→ goals/entities/requirements
→ authorized capability candidates
→ expertise/playbook retrieval
→ knowledge/multimodal evidence
→ bounded context composition
→ structured plan
→ policy/risk/Decision Gate evaluation
→ execute/read/wait
→ Outcome/Evidence
→ observe/update state
→ continue | clarify | wait | complete
→ synthesis/presentation
→ persist/audit/metrics
```

## 7. Sources of truth

| Conceito | Authority |
|---|---|
| identidade | Keycloak + Core integration |
| permissions efetivas | Core API |
| apps/rotas | Core API |
| business rules | APIs/use cases de domínio |
| business action technical contract | OpenAPI + Action Catalog |
| navigation | Portal Shell/Router |
| workspace visual | Portal/MFE/iframe |
| entity identity | domain owner + shared EntityRef adapter |
| relationships | domain owner + Business Graph relationship registry |
| expertise | Expertise Catalog |
| playbooks | Domain Playbook Catalog |
| knowledge visibility | Knowledge ACL |
| multimodal observation | extractor/service versionado |
| evidence provenance | source owner + Evidence contract |
| policy/decision | Policy/Safety |
| workflow state | durable work owner |
| model/compute selection | centralized Compute Policy |
| audit | audit/observability infrastructure |

## 8. Platform Actions

Fluxo:

```text
Core /me/apps
→ authorized route projection
→ semantic retrieval
→ PlatformCommand
→ Portal validation/revalidation
→ Router/MFE/Iframe handler
→ PlatformCommandResult
```

Exemplos genéricos:

- `portal.open_app`;
- `portal.open_route`;
- `portal.open_entity`;
- view commands suportados.

Sem URL livre do modelo.

## 9. Workspace Context

Contrato bounded compartilhado por MFE/iframe/Portal.

Pode conter:

```text
appId
routeId
entityRefs
filters
selection
dateRange
visibleDataRefs
source
```

Não contém:

- estado React completo;
- DOM;
- token;
- permission authority;
- dataset grande sem necessidade.

## 10. Business Actions

```text
UI ───────────────┐
                  ▼
             Domain API
                  ▲
Copilot → Action Catalog
```

O Copilot não aprende endpoints pela tela.

Pipeline:

```text
semantic intent
→ allowed action retrieval
→ schema/argument binding
→ policy
→ Decision Gate se necessário
→ generic executor
→ domain API
→ verified outcome
```

## 11. Entity model e Business Graph

### EntityRef

É referência lógica estável, não objeto duplicado.

### RelationshipRef

Conecta entidades com source/provenance.

### Business Graph

```text
EntityRefs + RelationshipRefs
→ permission-aware traversal
→ related source refs
→ fetch atual nas APIs donas
```

O graph pode materializar relações/cache, mas não virar sistema mestre de estoque, pedido, produto etc.

## 12. Evidence/Provenance

Toda análise madura usa um contrato compartilhado.

```text
SourceRef
→ EvidenceRef
→ FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION
→ presentation/audit/case
```

Evidence é reutilizado por multimodalidade, API results, Graph, Case e Workflow.

## 13. Expertise

```text
goals/context/entities/attachments/project prefs
→ Expertise retrieval
→ selected packs
→ bounded ExpertiseContext
```

Pack pode orientar:

- terminologia;
- análise;
- evidence expectations;
- preferred playbooks;
- knowledge refs;
- multimodal needs.

Não concede action/permission.

## 14. Domain Playbooks

Playbook descreve método:

```text
applicability
stages
evidence checklist
decision criteria
completion criteria
recommended capability semantics
```

Planner transforma método em WorkflowPlan usando capabilities reais autorizadas.

## 15. Multimodalidade

```text
attachment
→ native parsing/OCR/VLM
→ observations com page/region/confidence/limitations
→ EvidenceRef
→ expertise/playbook/analysis
```

Multimodal observation não é domain conclusion.

## 16. Decision Gates

Modelo único de governança de decisão:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Inputs podem incluir:

- risk/sensitivity;
- impact;
- arguments hash;
- evidence refs;
- autonomy;
- approver requirements.

## 17. Durable Workflow

```text
WorkflowPlan
→ steps/dependencies
→ execute canonical capabilities
→ checkpoint
→ wait_user / wait_approval / wait_event / wait_time
→ resume/revalidate
→ complete/fail/cancel
```

Não cria novo HTTP/tool stack.

## 18. Task / Case / Room / Inbox

### Task
Unidade de trabalho curta/média backed por workflow.

### Case
Investigação/trabalho prolongado com entity/evidence/task/workflow refs.

### Room
Colaboração humana + Copilot; preferir owner existente.

### Inbox
View/materialização sobre estados de Work/Decision/Watch; não novo engine.

## 19. Watch/Event-driven

```text
EventEnvelope
→ Watch condition
→ dedupe/cooldown
→ permission/policy revalidation
→ OBSERVE | ADVISE | ACT
```

ACT exige autonomia explícita e Decision Gate quando aplicável.

## 20. Organizational Knowledge e Learning

Knowledge operacional evolui somente por ciclo governado:

```text
candidate
→ review
→ eval
→ publish
→ rollout
```

Case resolution pode gerar candidate Experience, nunca verdade automática.

## 21. Model Router

Centralizado e implementado somente após baseline.

Classes conceituais:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

Considera privacy, availability, quality, latency, cost e output contract.

## 22. Clean Architecture

### Domain

- refs/value objects puros;
- policy rules puras;
- state machine semantics;
- sem DB/HTTP/LLM/framework.

### Application

- retrieve/compose/plan;
- decision orchestration;
- workflow/task/case use cases;
- graph traversal use cases;
- knowledge/evidence coordination.

### Infrastructure

- DB repositories;
- vector/index;
- OpenAPI importer/executor adapters;
- LLM/embedding/model providers;
- event adapters;
- multimodal adapters;
- persistence/queues.

### Interfaces

- REST/SSE/events;
- Portal commands;
- admin APIs.

### Composition

- DI/wiring.

## 23. Scalability/generalization

A arquitetura precisa permitir:

- novo app sem planner patch;
- novo OpenAPI provider sem endpoint selector;
- novo Expertise Pack sem core patch;
- novo Playbook sem novo agente;
- novo entity/relationship type sem planner branch;
- novo iframe compatível sem app-specific command no core;
- novo model/provider via Compute Policy, não `if` espalhado.

## 24. Migration do legado agents

```text
agent specialization → Expertise
agent tool gate → capabilities + policy
soft handoff → retrieval/replan/clarify
project default agent → project preferences/context
agent_id routing → temporary compatibility → removal
```

Compatibilidade possui exit criteria.

## 25. Anti-patterns proibidos

- second planner/tool executor;
- agent por departamento como produto final;
- manual endpoint catalog;
- path/opId semantic routing;
- graph como réplica dos bancos;
- evidence diferente por feature;
- confirmation paralela ao Decision Gate;
- Task engine paralelo ao Workflow runtime;
- Watch polling hardcoded por app;
- DOM automation para Business Action;
- CoT persistence;
- permission derivada de prompt/context/pack;
- model routing espalhado por feature.

## 26. Architecture success scenario

> “Investigue esta reclamação, analise o desenho, relacione produção e fornecedor, monte um 8D, acompanhe a nova revisão e, quando ela chegar, reavalie e prepare as ações necessárias.”

Um único runtime deve combinar:

```text
Context
+ Entity/Graph
+ Multimodal Evidence
+ Expertise/Playbook
+ Business Reads
+ Durable Workflow/Case
+ Watch/Inbox
+ Decision Gate
+ Business Write
+ Audit
```

sem trocar de agente e sem criar authorities paralelas.