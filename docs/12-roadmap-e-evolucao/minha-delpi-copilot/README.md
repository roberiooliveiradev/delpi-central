# Minha DELPI Copilot

> **Status:** `PLANNED / NOT_STARTED`  
> **Próxima etapa:** **C0.S0 — Rebaseline e inventário total**  
> **Ordem executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Arquitetura/design patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
> **Governança documental:** [`48-documentation-governance-and-architecture-review.md`](./48-documentation-governance-and-architecture-review.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. North Star

> **Minha DELPI Copilot entende o contexto da organização, conecta dados, pessoas, processos e aplicações, investiga problemas, executa trabalho, acompanha resultados e transforma conhecimento empresarial em ação governada.**

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → navegar, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
```

## 2. Princípios

1. Existe **um único Copilot** de produto.
2. Domínios especializam por Expertise Packs, Playbooks, Knowledge e tools — não por agentes departamentais.
3. Tudo que executa negócio reutiliza APIs/use cases reais.
4. OpenAPI + Action Catalog são authority técnica de Business Actions.
5. Core/RBAC continua authority de permissões.
6. Portal continua authority de navegação.
7. Workspace Context é contexto, não autorização.
8. Entity/Evidence/Decision/Workflow/Event usam foundations compartilhadas.
9. Business Graph conecta referências; não duplica bancos.
10. Writes usam Decision Gates, idempotency e audit conforme risco.
11. Durable Work reutiliza os mesmos executors; não cria tool stack paralelo.
12. Chain-of-thought não é exposta/persistida.
13. Runtime segue **Clean Architecture + Ports & Adapters + DDD pragmático**, conforme `49`.
14. Event-Driven, CQRS, Saga, Strategy, Factory e outras abstrações só entram quando a matriz/Abstraction Gate justificar.
15. Domain/Application não dependem de framework/provider concreto; wiring ocorre no Composition Root.
16. Estado durável de negócio permanece no backend; React não vira authority de Case/Workflow/Decision/Watch/Graph.

## 3. Arquitetura resumida

```text
                          MINHA DELPI COPILOT
                                  │
                    Goals / Workspace / Entities
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
      Capabilities           Expertise/Playbooks   Knowledge/Evidence
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  ▼
                           Structured Planner
                                  │
                         Policy / Decision Gate
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
      Platform Actions      Business Actions      Internal Tools
             │                    │                    │
             ▼                    ▼                    ▼
         Portal/MFE          Domain APIs          RAG/Vision/etc
                                  │
                                  ▼
                         Outcome / Evidence
                                  │
                     Durable Workflow quando preciso
                                  │
                    Task / Case / Room / Inbox / Watch
```

### Arquitetura de código

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure

Composition Root → DI/wiring
```

Dependências externas são protegidas por Ports & Adapters quando há boundary real. A escolha de patterns não é inferida livremente por etapa; segue [`49`](./49-architecture-and-design-patterns-standard.md).

## 4. Ordem foundation-first

```text
C0 Foundations
→ C1 Platform/Context
→ C2 Intelligence Core
→ C3 Business Reads + Graph
→ C4 Governed Writes
→ C5 Durable Work
→ C6 Proactivity/Ecosystem/Learning
→ C7 Optimization/Autonomy/Rollout
```

### C0 é obrigatório antes de features

```text
C0.S0 inventory + padrões existentes
→ C0.S1 authorities/bounded contexts
→ C0.S2 shared primitives
→ C0.S3 persistence/ports boundaries
→ C0.S4 cross-cutting semantics + architecture/pattern freeze
→ C0.S5 contract/conformance harness
→ C0.S6 FOUNDATION_FREEZE
```

Só então C1 inicia.

Isso evita construir hoje um `Confirmation`, `Evidence`, `Entity`, `Workflow`, `Event`, `Repository`, `Factory`, `Strategy` ou state model que precisaria ser substituído depois.

## 5. Foundations compartilhadas

C0 define/reutiliza semanticamente:

```text
CorrelationContext
EntityRef
RelationshipRef
SourceRef
EvidenceRef
OutcomeRef
CapabilityProjection
PlatformCommand
WorkspaceContext
IframeBridgeEnvelope
ExpertisePack / ExpertiseSelection / ExpertiseContext
DomainPlaybook
MultimodalEvidenceRef
DecisionGate
WorkflowPlan / WorkflowStep
TaskRef
CaseRef
EventEnvelope
AuditEvent/equivalent
```

C0 não significa criar todas as tabelas. Persistence só nasce quando o gap real for provado.

### Foundation arquitetural

C0 também congela:

```text
architecture style
layer responsibilities
dependency rules
bounded contexts
pattern decision matrix
error model
event model
state-machine rules
persistence rules
frontend state ownership
resilience/idempotency rules
testing pattern
migration/strangler patterns
Abstraction Gate
architectural exception/ADR process
```

## 6. Funcionalidades do produto alvo

- chat global/contextual;
- app/route/entity navigation;
- MFE e iframe context;
- Business reads/writes;
- DELPI Business Graph;
- Expertise Packs + Domain Playbooks;
- multimodalidade/desenhos;
- Evidence/Provenance;
- epistemic UX;
- Decision Gates;
- Durable Workflows;
- Copilot Tasks;
- Copilot Cases + Evidence Board;
- Interaction Rooms;
- Copilot Inbox;
- Copilot Watch;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- What-if/Simulation;
- Model Router/Compute Policy;
- autonomia L0–L5;
- AI-ready onboarding;
- observabilidade/audit/rollout.

Especificação completa: [`24-product-specification.md`](./24-product-specification.md).

## 7. Dependência OpenAPI-first

A iniciativa `llm-json-decoupling` da Minha DELPI AI permanece bloqueadora para Business Actions production-ready enquanto os gates relevantes não estiverem PASS.

```text
C0–C2 → podem avançar
C3+ Business Actions reais → dependem dos gates aplicáveis
```

Não criar workaround no Copilot.

## 8. Authorities que o Cursor deve conhecer

| Documento | Authority |
|---|---|
| `16` | ordem e dependências |
| `17` | ownership/primitives |
| `49` | arquitetura de código/design patterns/Abstraction Gate |
| `20` | testes/gates |
| `21` | estado/persistência |
| `23` | prompt mestre |
| `25` | CP requirements |
| ledger | estado/evidence |

Produto/arquitetura:

| Documento | Papel |
|---|---|
| `02` | arquitetura técnica |
| `12` | roadmap macro |
| `13` | catálogo funcional |
| `14` | DoD |
| `15` | integration map |
| `24` | produto completo |
| `48` | governança/precedência/revisão |

Specs temáticas são lidas somente quando a subetapa tocar o tema.

## 9. Specs temáticas principais

- `03` Capability model
- `04` Platform Actions
- `05` Workspace Context
- `06` Business Action Parity
- `07` Workflows/Durable Work
- `08` Security/Autonomy/Audit
- `09` UX
- `10` AI-ready
- `11` Observability/Evals
- `18` App Onboarding Matrix
- `19` Rollout/Migrations
- `26` Iframe Bridge
- `27–33` Single Copilot/Expertise/Playbooks/Multimodal/Migration
- `34` Market benchmark
- `35` Business Graph
- `36` Tasks/Cases/Rooms
- `37` Inbox/Watch
- `38` Evidence
- `39` Decision/Simulation
- `40` Organizational Knowledge
- `41` Expertise Studio
- `42` Model Router
- `43` Durable Workflow
- `44` Operational thematic map

`49` é authority normativa, não apenas spec temática.

`45`, `46` e `47` são `SUPERSEDED / REFERENCE_ONLY` porque seus conteúdos foram consolidados em `20`, `25` e `23`.

## 10. Primeiro passo

Não iniciar pela UI, Graph, Case, Watch ou Model Router.

Abrir [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md) e executar **somente C0.S0**.

Durante C0.S0, além do inventário funcional/técnico, mapear os patterns reais já usados no repositório para validar `49` antes do `FOUNDATION_FREEZE`.

Estado real deve ser registrado em [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).