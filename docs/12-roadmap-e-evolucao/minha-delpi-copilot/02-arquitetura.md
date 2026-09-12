# 02 — Arquitetura do Minha DELPI Copilot

**Status:** arquitetura alvo canônica  
**Boundary de produto:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline da plataforma:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Estrutura física:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Decisão arquitetural principal

O Minha DELPI Copilot é uma **nova aplicação da plataforma** com API e MFE próprios.

```text
NÃO
Copilot → extensão do Minha DELPI Chat
Copilot → código dentro de minha-delpi-ai-api
Copilot → código dentro de plugins/minha-delpi-chat
Copilot → feature implementada dentro do Portal

SIM
Portal/Core/Gateway/Keycloak/Domain APIs = plataforma
Copilot API + Copilot MFE = novo produto standalone
```

O Chat permanece sistema vizinho. Nenhum refactor ou bug do Chat é pré-requisito para o Copilot.

## 2. Arquitetura da plataforma observada

```text
                         Gateway
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Portal           Core API        Domain APIs
          │                │                │
          │            Keycloak/RBAC        │
          │                                 │
          └──────── apps/MFEs ──────────────┘
```

Fatos relevantes do repositório:

- Portal é Shell React/Vite;
- Core fornece apps/rotas/permissões;
- AppHost suporta `embedded`, `external`, `federated`;
- MFEs federados expõem `mount()`;
- Portal passa `getAccessToken` e props de host;
- `plugin-ui` é remote compartilhado;
- APIs dedicadas convivem como serviços pares;
- Gateway roteia `/apps/<service>/...`;
- Keycloak fornece SSO;
- APIs de domínio mantêm dados/regras de negócio.

## 3. Componentes novos

### 3.1 Copilot API

Owner recomendado: `minha-delpi-copilot-api/`.

É o runtime inteligente completo:

```text
HTTP/stream interface
→ Application Use Cases
→ Understanding/Context
→ Capability Discovery
→ Expertise/Knowledge/Evidence
→ Structured Planner
→ Policy/Decision Gate
→ Action/Platform adapters
→ Outcome
→ Workflow/Task/Case/Watch state
```

### 3.2 Copilot MFE

Owner recomendado: `plugins/minha-delpi-copilot/`.

React/Vite/Module Federation, usando `@delpi/plugin-ui`.

Surfaces:

```text
full-page app
+ global Portal panel
```

Ambas consomem a mesma Copilot API e o mesmo product state.

## 4. Arquitetura macro do produto

```text
                                 USER
                                  │
                                  ▼
                         Portal React Shell
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
             full-page                        side-panel
                  └───────────────┬───────────────┘
                                  ▼
                         Copilot Federated MFE
                                  │
                            typed API client
                                  │
                                  ▼
                           Gateway / Nginx
                                  │
                                  ▼
                         Copilot Standalone API
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     ▼                            ▼                            ▼
  Core API                    Domain APIs                  AI Infra
apps/routes/RBAC        OpenAPI/use cases/data        LLM/RAG/Vision
     │                            │                            │
     └────────────────────────────┼────────────────────────────┘
                                  ▼
                           Copilot-owned DB
```

## 5. Authority Matrix

| Conceito | Authority |
|---|---|
| autenticação | Keycloak |
| usuário/apps/rotas/permissões da plataforma | Core API |
| navegação real | Portal Router/AppHost |
| design system MFE | plugin-ui |
| regras/dados Comercial | commercial-api/API owner |
| integrações TOTVS/DELPI | api-delpi |
| demais negócios | respectivas Domain APIs |
| Copilot conversations | Copilot API |
| Copilot capabilities projection | Copilot API derivada de authorities |
| planner/orchestration | Copilot API |
| Expertise/Playbooks | Copilot API |
| Copilot Knowledge index | Copilot API, respeitando source ACL |
| Evidence/Provenance | Copilot API + source authorities |
| Business Graph projection | Copilot API; source data continua nos owners |
| Decision Gates | Copilot API + Domain API final authorization |
| Workflow/Task/Case/Watch | Copilot API |
| notification delivery compartilhada | Core/Portal quando apropriado |
| provider/model selection | Copilot API Compute Policy |
| Copilot audit/evals | Copilot API/observability |

## 6. Regra de dependência com Chat

```text
Copilot API  ─X→ minha-delpi-ai-api runtime
Copilot MFE  ─X→ minha-delpi-chat source
Copilot DB   ─X→ Chat tables as authority
```

Permitido:

```text
C0 lê Chat para aprender padrões/erros
Copilot e Chat usam plugin-ui
Copilot e Chat usam Core/Keycloak/Gateway
futuro package neutro pode ter ambos como consumidores se extraído corretamente
```

Não existe fase de migração do Chat para o Copilot no roadmap desta iniciativa.

## 7. Clean Architecture da Copilot API

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure

Composition Root conecta implementações aos ports.
```

### Domain

- Value Objects (`EntityRef`, lifecycle values etc. quando realmente domain-owned);
- invariantes;
- pure policies;
- state machines;
- domain errors/events internos.

### Application

- use cases;
- ports;
- planner orchestration;
- capability/expertise/knowledge composition;
- workflow orchestration;
- evidence coordination.

### Interfaces

- REST;
- streaming/SSE quando escolhido;
- event consumers quando existirem;
- DTOs/schemas.

### Infrastructure

- PostgreSQL;
- Core API adapter;
- generic Domain API/OpenAPI adapter;
- LLM/embedding provider;
- vector/search store;
- OCR/Vision;
- object/file storage;
- event/notification adapters;
- telemetry.

## 8. Frontend architecture

```text
ui/
state/
data/
features/
contracts/
adapters/
```

State ownership:

```text
server state        → query/cache layer
workspace state     → Portal/Copilot context adapter
conversation UI     → MFE state + server state
local UI state      → component/hooks
durable work state  → Copilot API
```

MFE não vira owner de Workflow/Case/Decision/Watch.

## 9. Portal integration

### 9.1 Registered app

Core manifesto registra Copilot como `microfrontend`/`federated`.

Portal não precisa de catálogo manual porque AppLauncher/AppHost usam `apps/routes` do Core.

### 9.2 Federated lifecycle

MFE segue convenções `plugins/vite/federation.shared.ts`:

- React singleton;
- `@delpi/plugin-ui` remote;
- `remoteEntry.js`;
- `mount()`/`unmount()` conforme padrão vigente.

### 9.3 Global panel

Portal terá somente uma integração thin-host:

```text
CopilotGlobalHost
→ monta Copilot MFE panel export
→ fornece host props/context
→ recebe typed platform commands
```

Sem AI logic no Portal.

## 10. Workspace Context

Portal/MFEs produzem contexto limitado e tipado:

```text
appId
routeId
EntityRef[]
filters
selection
dateRange
visibleDataRefs
```

O contexto é enviado ao Copilot por bridge/host contract.

Contexto **não** concede permissão.

## 11. Platform Commands

Copilot não gera URL arbitrária.

```text
semantic target
→ PlatformCommand
→ Portal validator/authorized route resolution
→ Router/MFE/Iframe adapter
→ typed result
```

Exemplos:

- `portal.open_app`;
- `portal.open_route`;
- `portal.open_entity`;
- view commands declarados.

## 12. Business Action architecture — nativa do Copilot

A cadeia OpenAPI-first é construída dentro da nova Copilot API desde o início da fase de inteligência/actions.

```text
OpenAPI sources
→ import/normalize/index
→ Action Catalog interno do Copilot
→ permission-aware availability
→ semantic retrieval
→ structured planner
→ schema argument binding
→ policy/Decision Gate
→ generic HTTP executor
→ Domain API
→ verify outcome
→ Evidence/Audit
```

Isso **não depende** de `minha-delpi-ai-api` estar corrigida ou pronta.

Se C0 encontrar código realmente genérico útil no Chat, ele só pode ser reutilizado após extração para owner neutro ou reimplementação limpa no Copilot; nunca via dependency de runtime.

## 13. Core/RBAC integration

Copilot API:

1. valida JWT (issuer/audience/signature/exp);
2. resolve Core current user/context;
3. consulta apps/routes/permissions quando necessário;
4. restringe capability candidates;
5. encaminha identity/token conforme contrato seguro à Domain API;
6. Domain API revalida regra/permissão da ação.

Invariante:

```text
Copilot effective capabilities ⊆ user effective capabilities
```

## 14. Evidence and Business Graph

Shared Copilot primitives são definidos antes das features:

```text
EntityRef
RelationshipRef
SourceRef
EvidenceRef
OutcomeRef
CorrelationContext
```

Business Graph guarda relações/referências/provenance, não cópias mestres de pedidos/produtos/estoques.

## 15. Intelligence Core

Depois de C1/C2 platform bootstrap/context:

```text
input
+ workspace
+ attachments
→ safety/input normalization
→ understanding
→ capability retrieval
→ expertise/playbook retrieval
→ knowledge/multimodal retrieval
→ bounded context
→ structured plan
→ policy
→ execute/read/wait
→ evidence/outcome
→ synthesis
```

## 16. Durable Work

Copilot API é owner de:

```text
WorkflowPlan
steps/checkpoints
wait_user
wait_approval
wait_event
Task
Case
Watch
Inbox state
```

Core notification infrastructure pode ser adapter de delivery, mas não owner do workflow semantics.

## 17. Interaction Rooms

O Portal Comercial já possui conceito/rota de sala de interação. Antes de criar nova sala, C0 deve mapear API, MFE, storage, websocket e authorization existentes.

Decisão depois do inventário:

```text
REUSE | EXTEND | ADAPTER | CREATE_REQUIRED
```

## 18. Deploy/infra

Copilot possui independentemente:

- Dockerfiles;
- requirements/package-lock;
- migration chain;
- health endpoint;
- Gateway dev/prod route;
- Compose dev/prod service;
- env settings;
- manifest;
- registration script;
- test suites;
- logs/metrics;
- rollback.

Nenhum `depends_on` lógico do Chat.

## 19. Architecture patterns

Aplica `49` integralmente:

- Ports & Adapters para Core/Domain APIs/LLMs/stores;
- Use Cases na Application;
- Repository somente para Copilot-owned persistence;
- State Machines para lifecycle;
- Policy/Specification para regras determinísticas;
- Outbox/idempotency onde atomicidade/replay justificar;
- Strategy para providers apenas com variação real;
- no speculative abstraction.

## 20. Generalization

Target precisa suportar sem core patch específico:

- nova API/OpenAPI provider;
- novo app/route;
- novo Expertise Pack;
- novo Playbook;
- novo entity/relationship type;
- novo iframe compatível;
- novo model/provider por Compute Policy.

## 21. Sequência arquitetural

```text
C0 platform/application foundations
↓
C1 standalone bootstrap + Portal/Core/Gateway/SSO
↓
C2 workspace context + platform commands
↓
C3 intelligence core
↓
C4 reads + graph
↓
C5 writes + durable foundation
↓
C6 product work/proactivity/ecosystem
↓
C7 advanced autonomy/optimization/rollout
```

## 22. Critério de sucesso estrutural

O Copilot está corretamente arquitetado quando podemos desligar `minha-delpi-ai-api` e `plugins/minha-delpi-chat` e **o Copilot continua funcional**, exceto por qualquer infraestrutura neutra compartilhada que também seja usada por outros apps.

Esse teste conceitual de independência é obrigatório.