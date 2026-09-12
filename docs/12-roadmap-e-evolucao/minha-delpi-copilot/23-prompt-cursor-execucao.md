# Prompt mestre — Cursor — Minha DELPI Copilot

Você deve implementar o **Minha DELPI Copilot** em ordem foundation-first, seguindo a documentação canônica e evitando refatoração previsível, arquitetura paralela, escolha arbitrária de design patterns e consumo desnecessário de tokens.

## 1. Fonte de verdade e ordem de leitura

Leia antes de qualquer alteração:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. regras `.cursor` aplicáveis a planning/execution/tests/security/OpenAPI/AI/Clean Architecture
4. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`
5. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md`
6. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md`
7. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md`
8. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/02-arquitetura.md`
9. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md` nas seções aplicáveis
10. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md` quando estado/persistência estiverem no escopo
11. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/22-cursor-execution-protocol.md`
12. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md` quando necessário para requisito funcional
13. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md` nos CPs aplicáveis
14. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md`
15. documentos temáticos da subetapa em execução.

### Regras críticas

`16-execution-master-plan.md` é a **única authority da ordem de implementação**.

`49-architecture-and-design-patterns-standard.md` é a **authority da arquitetura de código e escolha de patterns**.

Os planos `E*` e `O*` são detalhamento temático. Eles não desbloqueiam etapa independentemente.

## 2. Missão do produto

Construir um único Copilot capaz de:

```text
PERGUNTAR
FAZER
ACOMPANHAR
TRABALHAR
```

sobre as mesmas APIs, permissions e regras de negócio da Minha DELPI.

Especialização ocorre por Expertise Packs/Playbooks/Knowledge/Multimodal, não por agentes departamentais separados.

## 3. Ordem obrigatória

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

Não implemente C1 antes de `FOUNDATION_FREEZE=PASS`.

## 4. Primeira ação obrigatória — C0.S0

Antes de runtime diff:

```text
git status
git rev-parse HEAD
```

Registrar `HEAD_BEFORE`.

Inventariar com evidence:

### Portal/Core
- Router/Auth/AppHost/AppLauncher;
- `/me`, `/me/apps`, `/me/routes`;
- manifests/routes/permissions;
- MFE/iframe/external lifecycle;
- rooms/notifications existentes.

### AI API
- understanding/planner;
- Action Catalog/importer/index;
- executors;
- policy/confirmation;
- RAG/ACL;
- session/turn persistence;
- send/stream/simulate;
- multimodal;
- models/providers;
- observability/evals.

### Agents/skills legados
- entities/repos/controllers/admin;
- specialization;
- workspace activation;
- soft handoff;
- skill registry;
- `agent_id`, `chat_mode`;
- project default agent;
- knowledge/actions/tools dependentes de agent;
- UI correspondente.

### Operação corporativa
- entity IDs;
- relationships;
- event bus/types;
- workers/queues/jobs;
- workflows/approvals;
- rooms/inbox/notifications;
- audit/provenance;
- cases/requests reutilizáveis;
- idempotency support;
- knowledge lifecycle.

### Arquitetura e padrões existentes
- packages/camadas `domain/application/interfaces/infrastructure` ou equivalentes;
- use cases/application services atuais;
- ports/adapters/repositories/gateways atuais;
- composition root/DI atuais;
- error/result taxonomy;
- DTO/mappers;
- state machines/lifecycle rules;
- event/domain event/integration event/outbox patterns;
- retry/timeout/circuit breaker/idempotency;
- migration/compatibility/strangler patterns;
- frontend `ui/state/data`, hooks, stores, query/cache e owners de estado.

Classificar:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
DEPRECATE
REMOVE
NOT_PROVEN
```

Sem C0.S0 completo: **não editar runtime do Copilot**.

## 5. C0 foundation freeze

C0 precisa estabilizar/reutilizar equivalentes para:

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
ExpertisePack/Selection/Context
DomainPlaybook
MultimodalEvidenceRef
DecisionGate Request/Decision
WorkflowPlan/Step
TaskRef
CaseRef
EventEnvelope
IframeBridgeEnvelope
AuditEvent ou integração equivalente
```

Não significa criar todas as tabelas em C0. Significa congelar **semântica, owner, versionamento, ports e boundaries** antes das features.

Além disso, antes de C1 deve estar validado:

```text
ARCHITECTURE_STYLE
LAYER_RESPONSIBILITIES
DEPENDENCY_RULES
BOUNDED_CONTEXTS
PATTERN_DECISION_MATRIX
ERROR_MODEL
EVENT_MODEL
STATE_MACHINE_RULES
PERSISTENCE_RULES
FRONTEND_STATE_RULES
RESILIENCE_RULES
TESTING_PATTERN
MIGRATION_PATTERNS
ABSTRACTION_GATE
ARCHITECTURAL_EXCEPTION_PROCESS
```

Todos precisam estar `PASS` no `FOUNDATION_FREEZE`.

## 6. Arquitetura e patterns obrigatórios

Use como base:

```text
Clean Architecture
+ Ports & Adapters / Hexagonal
+ DDD pragmático
+ Event-Driven somente onde houver evento real
+ State Machine para lifecycle não trivial
+ CQRS leve somente quando houver assimetria real
```

### Backend

```text
Domain
→ entidades/value objects/invariantes/policies puras

Application
→ use cases/orchestration/ports

Interfaces
→ controllers/DTOs/event boundary/mappers

Infrastructure
→ DB/HTTP/OpenAPI/LLM/RAG/Vision/Event adapters

Composition Root
→ DI/wiring concreto
```

Domain/Application não importam framework/client/provider concreto.

### Frontend

Respeite:

```text
ui
state
data
```

Use feature organization dentro dessas responsabilidades quando útil.

Owners de estado:

```text
server state          → query/cache layer existente
workspace state       → Portal Workspace Context
conversation state    → chat/copilot state
local UI state        → component/hook
durable business state→ backend
```

Case/Workflow/Watch/Decision/Graph nunca usam React como authority.

## 7. Pattern Decision Matrix resumida

A especificação completa está em `49`.

```text
external dependency        → Port + Adapter
application operation      → Use Case/Application Service
owned persisted lifecycle  → Repository
complex lifecycle          → State Machine
combinable deterministic   → Policy/Specification
real algorithm variation   → Strategy
legacy incompatibility     → Adapter + Anti-Corruption Layer
legacy gradual migration   → Strangler Fig
platform visual command    → Command + Handler
state + event atomicity    → Transactional Outbox quando necessário
retryable write/resume     → Idempotency
async fact reaction        → Event-Driven
real distributed writes    → Saga somente com compensação real
external instability       → Timeout/Retry/Circuit Breaker conforme risco
transport boundary         → DTO + Mapper
wiring                     → Composition Root / DI
config-dependent creation  → Factory quando necessário
complex construction       → Builder somente se realmente necessário
read/write asymmetry       → CQRS leve somente se simplificar
```

Não inferir outro pattern local se o problema já está coberto.

## 8. Abstraction Gate

Antes de criar qualquer:

```text
interface
port
repository
factory
strategy
registry
base class
generic engine
```

prove:

1. boundary real ou lifecycle owner;
2. variação/consumer concretamente justificável;
3. necessidade de substituição/test double quando externa;
4. inexistência de abstração equivalente no repo;
5. redução real de acoplamento/complexidade.

Se a justificativa for apenas “pode ser útil depois”, **não crie**.

Boundary externo pode justificar Port já na primeira implementação.

## 9. Regra anti-refatoração previsível

Antes de criar qualquer schema/service/table/event/abstração:

1. existe primitive compartilhado em C0?
2. existe owner/repository equivalente no código atual?
3. qual camada é dona da responsabilidade?
4. qual pattern do `49` se aplica?
5. a abstração passa o Abstraction Gate?
6. isso cria segunda authority?
7. isso duplica Entity/Evidence/Decision/Workflow/Event?
8. já sabemos que fase seguinte exigirá alterar este contrato?
9. funciona com sibling/unknown sem branch específica?
10. o repo já possui padrão comprovado melhor para o mesmo problema?

Se 6, 7 ou 8 = sim, **pare a implementação e corrija a fundação**.

## 10. Arquitetura funcional obrigatória

### Business Actions

```text
OpenAPI
→ Action Catalog
→ allowed actions
→ Capability Projection
→ retrieval/planner
→ policy/Decision Gate
→ generic executor
→ domain API
→ Outcome/Evidence
```

### Platform Actions

```text
Core /me/apps
→ authorized route projection
→ PlatformCommand
→ CopilotBridge
→ Portal/MFE/Iframe
```

### Intelligence

```text
understanding
→ capability retrieval
→ expertise/playbook retrieval
→ knowledge/multimodal evidence
→ bounded context
→ planner
```

### Durable Work

```text
WorkflowPlan
→ canonical executors
→ checkpoint/waits
→ Task/Case/Inbox/Room/Watch surfaces
```

Não criar segundo HTTP/tool executor.

## 11. Proibições

- agente por departamento como runtime final;
- second planner/executor;
- manual endpoint catalog;
- path/operationId semantic selector;
- app→URL hardcode;
- permission própria do Copilot;
- Workspace Context como authorization;
- Expertise/Playbook concedendo permission;
- DOM automation quando API/use case existe;
- graph copiando tabelas de domínio;
- Evidence model diferente por feature;
- confirmation paralela ao Decision Gate;
- Task engine paralela ao Workflow runtime;
- Watch polling app-specific no core se houver event owner melhor;
- CoT persistence;
- JWT/refresh token em iframe bridge/state;
- production learning automático por feedback;
- framework/ORM/client concreto em Domain/Application;
- business rule server-side duplicada no frontend;
- Repository para simples chamada HTTP;
- Manager/Helper/Utils/Service genérico com múltiplas responsabilidades;
- Strategy/Factory/Builder/CQRS/Saga/Event Sourcing sem justificativa;
- retry cego de write;
- event bus sem schema/owner;
- dual-read/dual-write permanente.

## 12. Migração do legado

Para agents e outros conceitos legados, preferir:

```text
Legacy
→ Anti-Corruption Layer / Adapter
→ New canonical model
→ shadow/telemetry/evals
→ canary
→ cutover
→ residual scan
→ remove legacy
```

Aplicar Strangler Fig; adapter temporário precisa de exit criteria.

## 13. Onda J / OpenAPI-first

C0–C2 podem avançar sem Business Actions production-ready.

C3+ que dependa de actions reais precisa dos gates OpenAPI-first aplicáveis `PASS` no candidate vigente.

Não mascarar dependência com mocks/fallbacks.

## 14. Protocolo de cada subetapa

```text
SELECT C*.S*
→ REVALIDATE HEAD/WORKTREE
→ read owners/contracts
→ classify layer + pattern
→ abstraction gate
→ dependency gate
→ READY_TO_EXECUTE
→ baseline
→ minimal correct owner-level diff
→ producer/consumer wiring
→ unit/contract
→ integration
→ positive/sibling/negative
→ security/RBAC
→ generalization/metamorphic/unknown
→ architectural conformance
→ adversarial review
→ semantic residual scan
→ postconditions
→ COMPLETE_GATE
→ docs/ledger
→ unlock next
```

Execute **uma subetapa por vez**.

## 15. COMPLETE_GATE

Bloqueantes:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK material
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY material
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
ARCHITECTURE_PATTERN_DRIFT
DEPENDENCY_RULE_VIOLATION
UNJUSTIFIED_ABSTRACTION
UNDOCUMENTED_ARCHITECTURAL_EXCEPTION
```

## 16. Testes

Use `20-testing-and-acceptance-matrix.md` como única matriz canônica.

Não use `45-*` como segunda authority; ele é referência histórica/temática.

Obrigatório conforme fase:

- positive/sibling/negative;
- unauthorized/TOCTOU;
- injection;
- send/stream;
- reload/restart;
- unknown app/provider/pack/iframe/relation;
- true metamorphic rename;
- Decision Gate/idempotency;
- workflow crash/resume;
- graph permission traversal;
- evidence/provenance;
- layer/dependency conformance;
- adapter/port contract tests;
- state transition tests quando aplicável;
- error translation/resilience tests;
- R1–R11 aplicáveis.

Nunca enfraquecer threshold/test para passar.

## 17. Rastreabilidade

Use `25-requirements-traceability.md` como única authority `CP-*`.

`46-*` é referência temática; não manter requisito novo apenas lá.

Todo requisito novo:

```text
CP-ID
owner
canonical C phase
gate
status
```

## 18. Relatório obrigatório

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
REQUIREMENTS_CP:
CANONICAL_OWNERS:
ARCHITECTURE_LAYER:
DESIGN_PATTERNS_APPLIED:
ABSTRACTION_GATE:
ARCHITECTURAL_EXCEPTION_ADR:
REUSED_FOUNDATIONS:
NEW_FOUNDATIONS_CREATED:
FILES_CHANGED:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
SECURITY_RBAC:
GENERALIZATION:
ARCHITECTURAL_CONFORMANCE:
RESIDUAL_SEARCH:
ADVERSARIAL_REVIEW:
FOUNDATION_DRIFT:
POSTCONDITIONS:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 19. Continuidade

Se `COMPLETE_GATE=PASS`, prossiga para a próxima subetapa desbloqueada pelo `16-execution-master-plan.md`.

Não comece por UI final, Business Graph, Cases, Watch ou Model Router.

Comece por:

```text
C0.S0
→ C0.S1
→ C0.S2
→ C0.S3
→ C0.S4
→ C0.S5
→ C0.S6 FOUNDATION_FREEZE
```

Somente então `C1.S1`.