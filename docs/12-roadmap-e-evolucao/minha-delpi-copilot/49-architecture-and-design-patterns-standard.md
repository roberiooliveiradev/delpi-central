# Minha DELPI Copilot — Padrão Normativo de Arquitetura e Design Patterns

**Status:** `CANONICAL_AUTHORITY` para arquitetura de código e escolha de patterns  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Ownership/contracts:** [`17-component-and-contract-map.md`](./17-component-and-contract-map.md)  
**State/persistence:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Regra:** nenhuma subetapa de runtime pode inferir livremente arquitetura/pattern quando este documento já define o padrão aplicável.

## 1. Objetivo

Reduzir variabilidade arquitetural, refatoração previsível e consumo de tokens durante a implementação do Minha DELPI Copilot.

O Cursor/IA deve primeiro **classificar o problema**, depois aplicar o pattern definido aqui e somente então implementar.

```text
NÃO
problema
→ IA inventa arquitetura local
→ implementa
→ descobre inconsistência
→ refatora

SIM
problema
→ classifica responsabilidade/boundary
→ consulta pattern canônico
→ reutiliza foundation/owner
→ implementa
→ testa contrato
```

Este documento não substitui as instruções oficiais nem as regras `.cursor`. Ele especializa essas regras para o Copilot.

## 2. Arquitetura base obrigatória

O Copilot adota:

```text
Clean Architecture
+
Hexagonal Architecture / Ports & Adapters
+
DDD pragmático
+
Event-Driven Architecture somente onde houver eventos reais
+
State Machines para lifecycles não triviais
+
CQRS leve somente quando command/read possuírem necessidades materialmente diferentes
```

### 2.1 Princípio de simplicidade

> Usar o menor pattern que preserve ownership, testabilidade, segurança, generalização e evolução.

Não aplicar DDD cerimonial, CQRS total, Event Sourcing, Saga, Factory, Strategy ou abstração genérica apenas porque o pattern existe.

## 3. Regra de dependência

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure

Composition Root conecta tudo.
```

Dependências de código devem apontar para dentro.

O domínio/application não pode depender de:

- Flask;
- React;
- SQLAlchemy model;
- PostgreSQL driver;
- requests/httpx client concreto;
- provider de LLM concreto;
- vector database concreto;
- event broker concreto;
- implementation-specific SDK externo.

Infraestrutura implementa ports definidos pelas camadas internas.

## 4. Backend — responsabilidades por camada

### 4.1 `domain`

Pode conter:

- Entities/Aggregates quando existir identidade/lifecycle próprio;
- Value Objects;
- enums de domínio;
- invariantes puras;
- Domain Policies puras;
- Specifications puras quando realmente combináveis;
- Domain Events quando representarem fato do domínio;
- ports somente quando a abstração pertence semanticamente ao domínio.

Não pode:

- acessar banco;
- chamar HTTP;
- chamar LLM;
- importar Flask/SQLAlchemy;
- ler variável de ambiente;
- publicar evento em broker;
- serializar DTO de transporte.

### 4.2 `application`

Owner de orchestration/use cases.

Pode conter:

- Use Cases / Application Services;
- Commands/Queries de aplicação;
- ports de repositories/gateways/external capabilities;
- orchestrators;
- transaction boundaries abstratas;
- policy invocation;
- state transition use cases;
- mapping entre domain/result refs quando necessário.

Não deve conter:

- SQL;
- URL/path/provider hardcoded;
- regra React/UI;
- client concreto;
- detalhes de framework.

### 4.3 `interfaces` / transport adapters

Pode conter:

- Flask controllers/routes;
- request/response DTOs;
- schemas de transporte;
- event consumers/producers de borda;
- mappers de transport ↔ application;
- validation de shape/boundary.

Não deve conter regra de negócio.

### 4.4 `infrastructure`

Pode conter:

- SQLAlchemy/PostgreSQL repositories;
- HTTP adapters;
- OpenAPI adapters;
- LLM/model adapters;
- vector/RAG adapters;
- object/file storage adapters;
- OCR/vision adapters;
- event broker/outbox implementations;
- telemetry adapters;
- caches/materializers.

Infrastructure não redefine policy/semântica do domínio.

### 4.5 `composition root`

Único local normal para wiring concreto:

```text
config
→ create adapters
→ create repositories
→ create policies
→ create use cases
→ register controllers/handlers
```

Proibido instanciar infraestrutura escondida dentro de domain/application services.

## 5. Frontend — arquitetura obrigatória

Respeitar a Clean Architecture oficial do projeto:

```text
ui
state
data
```

Preferir organização por feature **dentro dessas responsabilidades** quando reduzir acoplamento.

Exemplo conceitual:

```text
copilot/
  ui/
    components/
    pages/
  state/
    hooks/
    reducers-or-store/
  data/
    api/
    adapters/
    contracts/
```

### 5.1 `ui`

- rendering;
- composição visual;
- events de usuário;
- acessibilidade;
- presentation-only transformations.

Não executa regra de negócio server-side nem decide permission.

### 5.2 `state`

- estado local e transversal de UX;
- hooks reutilizáveis;
- reducers/state machines de UI quando lifecycle justificar;
- Portal Workspace Context conforme owner definido.

### 5.3 `data`

- clients/adapters tipados;
- serialização;
- cache/query integration existente;
- contract mapping.

Não criar regra de negócio duplicada para “facilitar a tela”.

## 6. Regra de ownership do estado frontend

```text
Server State          → query/cache layer existente
Workspace State       → Portal Workspace Context owner
Conversation State    → chat/copilot state
Local UI State        → component/hook
Durable Business State→ backend canônico
```

Case, Workflow, Decision Gate, Watch ou Business Graph não podem ter React como authority.

## 7. Pattern Decision Matrix

| Problema | Pattern padrão | Condição/limite |
|---|---|---|
| dependência externa | Port + Adapter | default para boundary externo |
| operação de aplicação | Use Case / Application Service | uma intenção operacional clara |
| persistência de aggregate/estado próprio | Repository | não usar para simples proxy HTTP |
| lifecycle complexo | State Machine | transições explícitas/invariantes |
| regras determinísticas combináveis | Policy / Specification | quando combinação/reuso justificar |
| escolha entre algoritmos reais | Strategy | não criar se existe só uma implementação sem variação provável |
| integração legada/shape incompatível | Adapter + Anti-Corruption Layer | preservar novo modelo limpo |
| migração gradual de legado | Strangler Fig | adapter temporário + exit criteria |
| comando visual/plataforma | Command + Handler | registry genérico; sem handler por app |
| evento confiável junto de transação DB | Transactional Outbox | quando atomicidade state+event for requisito |
| write reexecutável/retry/resume | Idempotency Pattern | preferir suporte nativo do domínio |
| comunicação assíncrona | Event-Driven | somente com evento owner/contrato real |
| transação distribuída com compensações | Saga | somente quando houver compensações de domínio reais |
| integração instável | Timeout + Retry Policy + Circuit Breaker quando aplicável | write nunca recebe retry cego |
| boundary HTTP/event | DTO + Mapper | não expor ORM model como contrato |
| wiring concreto | Dependency Injection via Composition Root | DI simples, sem framework mágico obrigatório |
| criação dependente de configuração | Factory | só quando criação realmente varia |
| criação complexa com invariantes | Builder/Factory Method | somente quando constructor simples não basta |
| leitura e escrita com modelos muito distintos | CQRS leve | sem duplicar domínio por padrão |

## 8. Use Case / Application Service

Default para ação da aplicação:

```text
Controller/Event Handler
→ Use Case
→ Domain/Policies
→ Ports
→ Adapters
```

Exemplos possíveis, sujeitos ao inventário real:

- `CreateCopilotTask`;
- `ResumeWorkflow`;
- `TraverseBusinessGraph`;
- `EvaluateDecisionGate`;
- `PublishExpertisePack`;
- `CreateWatch`.

Não criar um `CopilotService` monolítico com responsabilidades heterogêneas.

## 9. Ports & Adapters

Aplicar especialmente em:

```text
LLM/provider
OpenAPI/actions
Business Graph
Knowledge/RAG
Vector store
Database
Event bus
Notifications
File/object storage
Multimodal/OCR/Vision
Domain APIs
```

Exemplo:

```text
Application
   ↓
BusinessGraphPort
   ↑
APITraversalAdapter | MaterializedGraphAdapter
```

O nome final deve seguir convenções reais do repositório encontradas em C0.S0.

## 10. Repository Pattern

Usar para estado/aggregate cujo lifecycle pertence ao Copilot/plataforma.

Candidatos conceituais:

- Expertise/Playbook quando authority persistida for comprovada;
- Workflow;
- Task/Case;
- Watch;
- materialização do Graph quando comprovada.

Não criar repository no Copilot para cada recurso que já possui domain API owner.

```text
ERRADO
PurchaseOrderRepository no Copilot apenas para chamar purchase-api

CORRETO
Business Action/API Adapter → domain API owner
```

## 11. Adapter e Anti-Corruption Layer

### 11.1 Iframe/MFE/external systems

- `IframeBridgeAdapter`;
- Workspace Context adapters;
- OpenAPI adapters;
- provider adapters.

### 11.2 Migração de agents

O novo domínio não deve carregar `agent_id`, `chat_mode` ou soft handoff como conceitos centrais.

```text
Legacy Agent Model
→ Anti-Corruption Layer / Migration Adapter
→ Expertise / Project Context / Capability Policy
```

A ACL é temporária e precisa de exit criteria.

## 12. Strangler Fig para migração

Migrações relevantes do legado devem preferir:

```text
legacy runtime
→ compatibility adapter
→ new canonical behavior
→ telemetry/evals
→ canary
→ cutover
→ residual search
→ remove legacy
```

Não fazer big-bang sem necessidade.

Não manter dual-read/dual-write indefinidamente.

## 13. State Machine Pattern

Obrigatório quando status possui transições válidas, waits, expiry, reabertura ou invariantes.

### Workflow

```text
PLANNED
→ RUNNING
→ WAITING_USER | WAITING_EVENT | WAITING_APPROVAL | WAITING_TIME
→ RUNNING
→ SUCCEEDED | PARTIALLY_SUCCEEDED | FAILED | CANCELLED | EXPIRED
```

### Decision Gate

```text
PENDING
→ APPROVED | REJECTED | EXPIRED | INVALIDATED
```

### Case/Task/Expertise lifecycle

Usar o lifecycle canônico definido em C0 e specs correspondentes; não criar `if status == ...` disperso como regra de transição.

Transição deve ocorrer em owner/use case explícito.

## 14. Policy e Specification

### Policy Object

Preferir para decisão determinística:

```text
DecisionGatePolicy
AutonomyPolicy
RetryPolicy
RetentionPolicy
CapabilityAvailabilityPolicy
ComputePolicy
```

Forma:

```text
structured input
→ structured decision
```

Policy não é prompt livre.

### Specification

Usar quando regras combináveis/reutilizáveis justificarem:

```text
UserHasPermission
AND CapabilityAvailable
AND ContextValid
```

Não criar uma classe Specification por condição trivial.

## 15. Command + Handler

Adequado para Platform Actions e comandos tipados.

```text
PlatformCommand
→ Generic Handler Registry
→ handler por tipo de comando
```

Permitido:

- `OpenAppCommandHandler`;
- `OpenRouteCommandHandler`;
- `SetViewCommandHandler`.

Proibido no core genérico:

- `OpenCommercialPortalHandler`;
- `OpenSuppliesPortalHandler`;
- handlers por app/cliente/provider.

## 16. Event-Driven Architecture

Eventos são usados quando há desacoplamento temporal ou reação a fato ocorrido.

Não transformar chamada síncrona simples em evento sem motivo.

### Domain Event

Fato interno do bounded context.

### Integration Event

Contrato versionado publicado para outros contexts.

```text
Domain fact
→ Integration Event adapter/outbox quando necessário
→ EventEnvelope canônico
```

Watch e `wait_event` consomem o mesmo envelope/event semantics congelado em C0.

## 17. Transactional Outbox

Usar quando for requisito garantir:

```text
state persisted
E
integration event eventually published
```

Fluxo:

```text
DB transaction
├─ state change
└─ outbox record
commit
→ publisher/worker
→ broker
```

Não introduzir Outbox se o owner atual já garante atomicidade por mecanismo equivalente.

## 18. Idempotency

Obrigatório para writes sujeitos a retry/replay/resume quando o domínio suportar ou a plataforma precisar coordenar segurança.

Preferência:

1. contrato idempotente nativo da domain API;
2. use case do domínio com idempotency key;
3. orchestration guard somente quando necessário e explicitamente limitado.

Nunca assumir `POST`, `PUT`, `PATCH` ou `DELETE` seguros para retry apenas pelo método HTTP.

## 19. Saga Pattern

Usar somente quando:

- existem múltiplos writes em sistemas distintos;
- há necessidade real de consistência processual;
- cada compensação possui operação real e semântica de domínio.

Não usar Saga para reads, análise ou workflow simples.

Não inventar rollback universal.

## 20. Resilience Patterns

Toda integração externa deve definir conforme risco:

```text
timeout
retry eligibility
backoff
circuit breaker quando útil
bulkhead/concurrency limit quando necessário
ambiguous outcome handling
```

### Reads

Podem usar retry controlado quando seguro.

### Writes

Retry somente com idempotência/verification adequados.

Timeout ambíguo após write exige verificar outcome antes de nova tentativa.

## 21. Result / Error Model

Application layer deve trabalhar com taxonomia estável de outcomes/errors, reaproveitando o padrão real do repo quando existir.

Semântica mínima:

```text
Validation
Unauthorized
Forbidden
NotFound
Conflict
PolicyBlocked
DecisionRequired
ProviderUnavailable
Timeout
BusinessRuleViolation
Internal
```

Infra exception não deve vazar diretamente para UI/LLM.

Não criar uma taxonomia diferente por feature.

## 22. DTO + Mapper

Não expor ORM entity/model diretamente como contrato externo.

```text
Transport DTO
↕ mapper
Application/Domain Model
↕ repository mapper quando necessário
Persistence Model
```

Evitar mappers artificiais quando shapes são realmente idênticos e não há boundary semântico, mas preservar separação de ownership.

## 23. Dependency Injection

Usar DI simples por composição.

```text
bootstrap/create_app/composition root
→ concrete adapters
→ ports/use cases
→ controllers/handlers
```

Proibido:

```text
class DomainService:
    repo = PostgresRepository()
```

ou service instanciando client/provider concreto internamente sem boundary.

## 24. Factory e Builder

### Factory

Somente quando criação depende materialmente de runtime/config/provider.

Exemplos possíveis:

- model/provider adapter factory;
- document extractor factory.

### Builder

Somente para objeto realmente complexo com etapas/invariantes.

Não criar Builder para DTO simples.

## 25. CQRS leve

Pode separar Command/Query quando:

- read model e write model têm requirements muito diferentes;
- há benefício material de performance/segurança/shape;
- a separação simplifica, não duplica, o domínio.

Não criar dois bancos/modelos por padrão.

## 26. Bounded Contexts conceituais

C0.S1 deve revalidar nomes/owners reais, mas a separação alvo é:

```text
Copilot Intelligence
Capability & Action Integration
Expertise & Playbooks
Knowledge
Evidence & Provenance
Work Management
Policy & Decision
Platform Experience
Business Graph
Observability & Evals
```

Compartilhar contracts deliberadamente; não compartilhar models internos indiscriminadamente.

## 27. Padrões por componente do Copilot

| Componente | Arquitetura/patterns preferidos |
|---|---|
| Capability/Action integration | Port + Adapter; projection; policy |
| Platform Actions | Command + Handler + Adapter |
| Workspace Context | Adapter + bounded immutable contract |
| Iframe Bridge | Adapter + Anti-Corruption Layer + typed messages |
| Expertise | Repository se authority persistida; retrieval Strategy somente quando variações reais; Policy |
| Domain Playbooks | versioned domain content + repository/port |
| Multimodal | Pipeline + Adapter; extraction strategies quando comprovadas |
| Evidence | Value Object/validated factory + provenance composition |
| Business Graph | Ports & Adapters; repository/index somente se materializado; permission Policy/Specification |
| Decision Gates | Policy + State Machine |
| Workflow | Application orchestration + State Machine + Idempotency |
| Task/Case | Aggregate/lifecycle quando comprovado + Repository + Workflow refs |
| Rooms/Inbox | adapters/materialized views sobre authorities existentes |
| Watch | Event-driven + State Machine + dedupe/idempotency |
| Organizational Knowledge | versioned lifecycle + Repository + review policy |
| Expertise Studio | Use Cases + State Machine + RBAC admin |
| Model Router | Strategy/Policy apenas após baseline C7 |
| Legacy agents | Anti-Corruption Layer + Adapter + Strangler |

## 28. Abstraction Gate — quando NÃO abstrair

Antes de criar:

```text
interface
port
base class
factory
strategy
registry
framework
generic engine
repository
```

responder:

1. Existe boundary real?
2. Existe mais de uma implementação/consumer ou uma variação concretamente provável?
3. Precisamos de test double em boundary externo?
4. O conceito possui owner/lifecycle próprio?
5. A abstração reduz acoplamento ou apenas adiciona indireção?
6. Já existe abstração equivalente no repo?

Se a justificativa for apenas “pode ser útil no futuro”, não criar.

### Rule of Three

Para abstrações puramente internas e não-boundary, preferir implementação simples até repetição/variação real justificar extração.

Boundary externo é exceção: Port pode ser correto desde a primeira implementação porque protege a regra de dependência.

## 29. Anti-patterns proibidos

- `Manager`, `Helper`, `Utils` ou `Service` genérico acumulando responsabilidades;
- repository como wrapper de qualquer HTTP;
- base class profunda para compartilhar duas linhas;
- service locator global;
- singleton com mutable business state;
- framework types atravessando Domain/Application;
- ORM model como API contract;
- exception concreta de infra como contrato de produto;
- event bus sem schema/owner;
- Strategy com uma implementação sem boundary/variação justificável;
- Factory para constructor trivial;
- Saga sem compensação real;
- CQRS/Event Sourcing por moda;
- feature criando seus próprios Entity/Evidence/Decision/Event primitives;
- pattern que introduz segunda authority.

## 30. Testing Pattern por camada

### Domain

- unit puro;
- invariantes;
- value objects;
- state transitions/policies.

### Application

- use case unit com ports fake/stub;
- policy interaction;
- positive/sibling/negative;
- no framework requerido.

### Adapters/Infrastructure

- contract tests;
- integration com DB/API/broker/provider quando material;
- serialization/mapping;
- timeout/error translation.

### Interface

- request/response schema;
- auth/RBAC boundary;
- error mapping;
- transport semantics.

### Frontend

- component behavior;
- hooks/state transitions;
- adapter/contract tests;
- integration da feature;
- accessibility/keyboard para fluxos críticos.

Mocks não podem substituir o owner real justamente no teste que pretende provar integration/outcome.

## 31. Migration patterns

### Banco/contrato

```text
EXPAND
→ deploy compatible readers
→ deploy writer
→ backfill se necessário
→ CUTOVER
→ residual scan
→ CONTRACT em release posterior
```

### Runtime legado

```text
Strangler
+ Anti-Corruption Layer
+ telemetry
+ canary
+ exit criteria
```

Dual-read/dual-write só quando inevitável e sempre temporário.

## 32. ADR / Architectural Exception Gate

Se uma implementação precisar divergir deste padrão:

1. demonstrar por que o pattern canônico não atende;
2. registrar alternativas consideradas;
3. documentar trade-offs e impacto futuro;
4. provar que não cria segunda authority;
5. criar ADR/decisão arquitetural no local padrão do repo, se existente;
6. atualizar `49` se a exceção virar novo padrão.

Não criar exceção silenciosa dentro de PR.

## 33. FOUNDATION_FREEZE — requisitos arquiteturais

Antes de `C1.S1`, C0 precisa comprovar:

```text
ARCHITECTURE_STYLE = PASS
LAYER_RESPONSIBILITIES = PASS
DEPENDENCY_RULES = PASS
BOUNDED_CONTEXTS = PASS
PATTERN_DECISION_MATRIX = PASS
ERROR_MODEL = PASS
EVENT_MODEL = PASS
STATE_MACHINE_RULES = PASS
PERSISTENCE_RULES = PASS
FRONTEND_STATE_RULES = PASS
RESILIENCE_RULES = PASS
TESTING_PATTERN = PASS
MIGRATION_PATTERNS = PASS
ABSTRACTION_GATE = PASS
ARCHITECTURAL_EXCEPTION_PROCESS = PASS
```

Esses gates complementam, não substituem, os contratos/owners definidos no `16`/`17`.

## 34. Checklist obrigatório por subetapa

Antes de codificar:

```text
[ ] owner e camada definidos
[ ] pattern selecionado pela matrix
[ ] primitive compartilhado reutilizado
[ ] port só existe se boundary/abstraction gate justificar
[ ] state machine usada se lifecycle não trivial
[ ] persistence não virou authority paralela
[ ] external dependency está atrás de adapter
[ ] DI ocorre no composition root
[ ] error model canônico preservado
[ ] retry/idempotency coerentes com read/write
[ ] event/outbox somente se requisito justificar
[ ] frontend não ganhou business authority
[ ] migration/legacy usa padrão canônico
[ ] tests seguem camada/contrato
[ ] sibling/unknown não exigem hardcode
[ ] não há refatoração futura já previsível pela próxima fase
```

## 35. Regra final para Cursor/IA

Quando houver dúvida entre dois patterns:

```text
1. reutilize o padrão já comprovado no repo;
2. aplique a matrix deste documento;
3. escolha a solução mais simples que preserve boundaries;
4. não invente framework/abstração local;
5. se a decisão for materialmente ambígua, registre como architecture decision antes de codificar.
```

O objetivo não é maximizar número de patterns. É maximizar **consistência, legibilidade, testabilidade, previsibilidade e capacidade de evolução sem refatoração estrutural**.