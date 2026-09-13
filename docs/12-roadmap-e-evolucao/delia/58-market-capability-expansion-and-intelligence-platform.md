# DÉLIA — Expansão de Capacidades de Mercado e Plataforma de Inteligência

**Status:** thematic architecture/product spec  
**Nome do produto:** **DÉLIA — DELPI · Ecossistema de Ligações, Inteligência e Automação**  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Ownership:** [`17-component-and-contract-map.md`](./17-component-and-contract-map.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Objetivo

Formalizar capacidades complementares que levam a DÉLIA de um assistente/orquestrador para uma **plataforma corporativa de inteligência operacional**, sem criar autoridades paralelas nem engines redundantes.

A expansão cobre:

```text
Process Intelligence / Process Mining / Task Mining
AI Control Tower
MCP / A2A interoperability
Personal Memory / Personalization
DELPI Semantic Business Layer
Analysis Sandbox
Artifact Workspace
Predictive / Prescriptive Intelligence
Operational / Digital Twin
Edge / Offline AI
AI / Model Asset Lifecycle (MLOps)
AI Capability Marketplace / Studio
```

Estas capacidades são targets progressivos. Nenhuma tecnologia/vendor é presumida existente até C0.S0 produzir evidence.

## 2. Princípio estrutural

```text
DATA / EVENTS / PEOPLE / MACHINES / EXTERNAL SOURCES
                         │
                         ▼
               DÉLIA INTELLIGENCE PLANE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 Process Intelligence  Semantic Layer  Business Graph
        │                │                │
        └────────────────┼────────────────┘
                         ▼
           Decision / Planning / Simulation
                         │
                         ▼
             Automation & Execution Hub
                         │
                         ▼
              Verified Business Outcome
                         │
                         ▼
             Governance / Learning / Control
```

## 3. Process Intelligence

Process Intelligence deve permitir descobrir como os processos realmente acontecem, e não apenas executar fluxos previamente conhecidos.

Escopo alvo:

```text
Process Discovery
Process Mining
Task Mining
Conformance Checking
Variant Analysis
Bottleneck Detection
Rework / Loop Detection
Wait-Time Analysis
Automation Opportunity Detection
Agent/Automation Process Mining
Process KPI Mining
```

Fluxo canônico:

```text
Event Logs / Business Events
→ normalized process events
→ process instance/case correlation
→ discovered variants
→ conformance/bottleneck analysis
→ Evidence
→ improvement/automation candidate
→ human/process-owner review
→ Watch / Playbook / Automation candidate
→ deployment
→ outcome measurement
→ process mining again
```

Process Mining nunca altera processo/policy automaticamente.

Task Mining, quando envolver interação de usuários, exige governança de privacidade, transparência, purpose limitation e proibição de hidden worker profiling.

## 4. AI Control Tower

A DÉLIA deve evoluir para possuir uma camada administrativa de governança de todo ativo de IA/automação relevante.

Target inventory:

```text
DÉLIA runtime
models
prompts/system policies
Expertise Packs
Playbooks
Watches
Automations
RPA packages/workers
Computer-Use executors
MCP servers
A2A agents
connectors
Edge models
AI applications
```

Cada ativo deve poder expor, conforme aplicável:

```text
owner
version
status
risk class
autonomy level
permissions/data access
health
latency
cost
usage
quality/evals
incidents
kill switch
dependencies
rollout cohort
rollback state
business value / outcome metrics
```

AI Control Tower é plano de governança/observabilidade, não novo planner.

## 5. MCP e A2A

DÉLIA deve ser preparada para interoperabilidade padronizada.

### MCP

Uso alvo:

```text
DÉLIA
→ governed MCP client/gateway
→ approved MCP server
→ tools/resources/prompts-capabilities
```

Regras:

- discovery não concede permission;
- todo tool invocation passa por capability/policy/Decision semantics aplicáveis;
- server/tool metadata é untrusted until validated;
- secrets não entram no LLM;
- allowlist, versioning, provenance, timeout, rate limit e kill switch;
- MCP não substitui OpenAPI/Domain authority quando contrato oficial já existe.

### A2A

Uso alvo:

```text
DÉLIA
→ A2A gateway/adapter
→ approved external/specialized agent
→ bounded task/result/artifact
→ Evidence/Outcome
```

DÉLIA permanece o produto principal. Agentes externos não viram agentes departamentais internos nem recebem autoridade implícita.

## 6. Personal Memory e Personalization

Separar:

```text
ORGANIZATIONAL KNOWLEDGE
!=
USER PERSONAL MEMORY
```

Personal Memory pode armazenar somente informação permitida e governada para melhorar continuidade e personalização.

Candidate classes:

```text
user preferences
preferred output format
active projects/tasks
frequent entities/topics
saved working context
explicitly remembered facts
recent relevant decisions/work state
```

Requisitos:

- source/provenance quando material;
- user visibility/control;
- correction/forget/disable semantics;
- retention classes;
- no secret/token/password storage;
- no hidden personality/psychological profile;
- no use to elevate RBAC;
- personal memory does not become organizational Knowledge automatically.

## 7. DELPI Semantic Business Layer

Business Graph responde **como entidades se relacionam**. Semantic Business Layer responde **o que conceitos e métricas significam**.

Candidate primitive:

```text
SemanticDefinition
  id
  name
  type: metric | dimension | concept | rule_reference
  businessMeaning
  formula/expression?
  grain
  dimensions
  owner
  sourceRefs
  freshness
  version
  accessPolicyRef
  status
```

Exemplos:

```text
faturamento
pedido atrasado
lead time
estoque disponível
inadimplência
OEE
scrap
OTIF
margem
```

DÉLIA não inventa fórmula para métrica corporativa quando definição governada existir.

## 8. Analysis Sandbox

Target: ambiente efêmero e isolado para análise avançada.

Capacidades possíveis:

```text
Python
SQL sobre datasets autorizados
DataFrames
statistics
forecasting
optimization
charts
temporary files
CSV/XLSX transformations
```

Boundary:

```text
bounded authorized inputs
→ isolated sandbox
→ deterministic/tool execution
→ artifacts/results
→ Evidence/Source/Outcome refs
```

Proibido:

- network access irrestrito;
- acesso direto a secrets;
- usar sandbox como bypass de Domain API/RBAC;
- persistir dataset sensível sem retention policy;
- executar código arbitrário não governado em infraestrutura corporativa.

## 9. Artifact Workspace

DÉLIA deve poder produzir e manter artefatos de trabalho, não apenas texto de chat.

Target artifacts:

```text
report
spreadsheet
presentation
document
PDF
chart
dashboard snapshot
process map
BPMN candidate
checklist
procedure draft
8D
FMEA
A3
SWOT
project plan
meeting minutes
```

Artifacts carregam owner, source/evidence references, version, status e sharing policy quando duráveis.

Candidate lifecycle:

```text
DRAFT → REVIEW → APPROVED/PUBLISHED | ARCHIVED
```

Nem todo artefato exige aprovação; o lifecycle depende da classe/risco.

## 10. Predictive e Prescriptive Intelligence

DÉLIA deve suportar progressivamente:

```text
DESCRIPTIVE   → o que aconteceu?
DIAGNOSTIC    → por que aconteceu?
PREDICTIVE    → o que provavelmente acontecerá?
PRESCRIPTIVE  → o que devemos fazer?
```

Casos alvo:

```text
atraso de pedido/fornecedor
ruptura de estoque
falha de máquina
scrap/qualidade
demanda
inadimplência
capacidade
lead time
manutenção
risco de prazo
```

Predição deve transportar model/version/confidence/features/source window/limitations. Prescrição é recommendation ou action candidate, não write automático sem policy.

## 11. Operational / Digital Twin

Business Graph não deve ser renomeado para Digital Twin.

Operational Twin é target separado para representar estado operacional dinâmico quando fontes reais justificarem.

Exemplo:

```text
Plant
└─ Line
   └─ Machine
      ├─ current state
      ├─ active OP
      ├─ product/revision
      ├─ cycle/context
      ├─ alarms
      ├─ maintenance
      ├─ quality
      └─ energy/telemetry
```

Uso:

```text
current state
→ scenario/simulation
→ impact projection
→ recommendation
→ optional governed action
```

Twin não substitui MES/SCADA/Domain/OT authority.

## 12. Edge / Offline AI

Target industrial progressivo:

```text
Cloud DÉLIA
+
Governed Edge Runtime
```

Edge pode executar somente capacidades explicitamente provisionadas:

```text
cached procedures/drawings
local rules
FAST PATH
local vision inference
optional local STT
telemetry preprocessing
event buffering
degraded offline assistance
later synchronization
```

Requisitos:

- signed/versioned packages/models;
- device identity/attestation when applicable;
- offline permission/session semantics;
- bounded stale-data behavior;
- secure sync/reconciliation;
- remote revoke/kill switch where possible;
- no independent enterprise policy authority at edge;
- no bypass of machine safety/interlocks.

## 13. AI / Model Asset Lifecycle (MLOps)

Model Router decide **qual modelo usar**. AI Asset Lifecycle governa **como modelos existem e evoluem**.

Assets:

```text
LLM
embedding
vision
speech
forecast
anomaly detector
classifier
optimization model
edge model
```

Candidate metadata:

```text
modelId/version
owner
provider/runtime
purpose
training/source lineage when applicable
evaluation set/results
risk class
deployment environments
latency/cost
quality thresholds
drift metrics
approval
rollout
rollback/deprecation
```

Nenhum modelo crítico é atualizado silenciosamente sem version/eval/rollout/rollback semantics.

## 14. AI Capability Marketplace / Studio

Target de publicação governada para capacidades reutilizáveis.

Itens candidatos:

```text
Expertise Packs
Playbooks
Watches
Automations
Connectors
MCP Servers
A2A Agents
Artifact Templates
Analysis Templates
Frontline Skills
Semantic Definitions
```

Lifecycle comum quando material:

```text
DRAFT
→ REVIEW
→ EVALUATED
→ APPROVED
→ PUBLISHED
→ DEPRECATED | REVOKED
```

Marketplace/Studio não cria permissão. Publicar capability não concede acesso a usuários.

## 15. Integração entre as capacidades

```text
Process Intelligence
→ descobre gap/oportunidade
→ Expertise/Playbook/Watch/Automation candidate

Semantic Layer + Business Graph
→ contextualizam dados
→ Predictive/Prescriptive / Simulation

Analysis Sandbox
→ análise/modelagem efêmera
→ Artifact Workspace

Automation Hub
→ execução
→ Outcome
→ Process Intelligence / Control Tower

AI Control Tower
→ governa models/connectors/MCP/A2A/automations/edge

Marketplace/Studio
→ lifecycle de publicação governada
```

## 16. Prioridade arquitetural

### P0 — foundation-impacting

```text
Process Intelligence event semantics/inventory
AI Control Tower inventory/governance model
MCP/A2A trust boundary
Personal Memory privacy boundary
Semantic Business Layer ownership
```

Esses itens devem ser considerados em C0 para evitar refatoração estrutural.

### P1 — product intelligence

```text
Analysis Sandbox
Artifact Workspace
Predictive/Prescriptive Intelligence
```

### P2 — industrial/scale

```text
Operational Twin
Edge/Offline AI
AI Asset Lifecycle/MLOps
```

### P3 — democratization/ecosystem

```text
AI Capability Marketplace / Studio
```

Prioridade não substitui a ordem C0–C7 do Plano Mestre.

## 17. C0 inventory additions

C0.S0 deve inventariar, sem criar runtime:

```text
process/event logs and case correlation sources
existing process/task mining tools or telemetry
business metric glossary/catalog/BI semantic definitions
existing personal preference/profile/memory storage and governance
sandbox/notebook/data-science runtime patterns
artifact/document generation/storage/versioning owners
forecast/optimization/anomaly models already in use
simulation/digital-twin/plant-model sources
edge/industrial compute devices and model deployment patterns
model registry/MLOps/evaluation/deployment tooling
MCP servers/clients and A2A agents/protocol use
AI asset inventories/control-plane tooling
internal catalog/marketplace/studio publication patterns
```

Unknown = `NOT_PROVEN`.

## 18. Security/privacy invariants

```text
process mining != employee surveillance
personal memory != secret psychological profile
semantic layer != duplicate business authority
sandbox != unrestricted code/network execution
artifact != automatically authoritative document
prediction != fact
prescription != automatic action
operational twin != OT source of truth
edge != independent authorization authority
MCP/A2A discovery != permission
marketplace publication != access grant
AI Control Tower != second planner
```

## 19. North Star ampliado

> **DÉLIA deve entender não apenas dados e perguntas, mas também pessoas autorizadas, processos reais, semântica empresarial, estado operacional, previsões, cenários e capacidades disponíveis; deve produzir trabalho útil, coordenar execução, operar online ou de forma degradada no edge quando aprovado, interoperar com tools/agentes externos e manter toda a inteligência governada por uma AI Control Tower.**
