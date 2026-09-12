# 02 — Arquitetura do Minha DELPI Copilot

**Status:** arquitetura alvo canônica  
**Boundary de produto:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Baseline da plataforma:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Estrutura física:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Decisão arquitetural principal

O Minha DELPI Copilot é uma **nova aplicação da plataforma** com API e MFE próprios.

```text
NÃO
Copilot → extensão do Minha DELPI Chat
Copilot → código dentro de minha-delpi-ai-api
Copilot → código dentro de plugins/minha-delpi-chat
Copilot → feature implementada dentro do Portal
Copilot → backend separado por Meeting/Frontline

SIM
Portal/Core/Gateway/Keycloak/Domain APIs = plataforma
Copilot API + Copilot MFE = novo produto standalone
Global/Workspace/Meeting/Frontline = surfaces do mesmo produto
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

Detalhes de voice/realtime/devices/OT ainda são `TO_INVENTORY` até C0.S0, conforme `51`.

## 3. Componentes novos

### 3.1 Copilot API

Owner recomendado: `minha-delpi-copilot-api/`.

É o runtime inteligente completo:

```text
HTTP/stream/media interfaces
→ Application Use Cases
→ Understanding/Context
→ Capability Discovery
→ Expertise/Knowledge/Evidence
→ Structured Planner
→ Policy/Decision Gate
→ Action/Platform adapters
→ Outcome
→ Workflow/Task/Case/Watch state
→ Meeting/Frontline session semantics
```

### 3.2 Copilot MFE

Owner recomendado: `plugins/minha-delpi-copilot/`.

React/Vite/Module Federation, usando `@delpi/plugin-ui`.

Surfaces:

```text
GLOBAL      panel contextual
WORKSPACE   full-page
MEETING     collaborative multimodal session
FRONTLINE   operator/device-oriented assistance
```

Todas consomem a mesma Copilot API e o mesmo product state autorizado.

## 4. Arquitetura macro do produto

```text
                                  USER
                                   │
                 ┌─────────────────┼──────────────────┐
                 ▼                 ▼                  ▼
             desktop           meeting room      frontline device
                 │                 │                  │
                 └─────────────────┼──────────────────┘
                                   ▼
                          Portal / Copilot Host
                                   │
                                   ▼
                         Copilot Federated MFE
                    Global | Workspace | Meeting | Frontline
                                   │
                             typed API/media
                                   │
                                   ▼
                            Gateway / Nginx
                                   │
                                   ▼
                          Copilot Standalone API
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
   Core API                    Domain APIs                 AI/Media Infra
apps/routes/RBAC         OpenAPI/use cases/data       LLM/RAG/STT/Vision
      │                            │                            │
      └────────────────────────────┼────────────────────────────┘
                                   ▼
                           Copilot-owned state
```

OT/domain systems permanecem externos como owners de machine/process truth e industrial safety.

## 5. Authority Matrix

| Conceito | Authority |
|---|---|
| autenticação | Keycloak |
| usuário/apps/rotas/permissões | Core API |
| navegação real | Portal Router/AppHost |
| design system MFE | plugin-ui |
| regras/dados de negócio | respectivas Domain APIs |
| integrações TOTVS/DELPI | api-delpi quando owner |
| Copilot conversations | Copilot API |
| capabilities projection | Copilot API derivada de authorities |
| planner/orchestration | Copilot API |
| Expertise/Playbooks | Copilot API |
| Knowledge index | Copilot API, respeitando source ACL |
| Evidence/Provenance | Copilot API + source authorities |
| Business Graph projection | Copilot API; source data continua nos owners |
| Decision Gates | Copilot API + Domain API final authorization |
| Workflow/Task/Case/Watch | Copilot API |
| Meeting semantics/artifacts | Copilot API |
| Frontline assistance semantics | Copilot API |
| media capture UI | Copilot MFE + browser/device permission |
| media perception | Copilot media adapters |
| raw media storage | storage owner aprovado, somente quando policy exigir |
| consent/retention | privacy/security owner + Copilot enforcement |
| device identity | platform/device owner quando existir; nunca user authority |
| machine/process truth | OT/domain owner |
| industrial safety/interlocks | industrial/OT safety owner |
| notification delivery | Core/Portal quando apropriado |
| provider/model selection | Copilot Compute Policy |
| Copilot audit/evals | Copilot observability |

## 6. Regra de dependência com Chat

```text
Copilot API   ─X→ minha-delpi-ai-api runtime
Copilot MFE   ─X→ minha-delpi-chat source
Copilot DB    ─X→ Chat tables as authority
Copilot Media ─X→ Chat media runtime as required dependency
```

Permitido:

```text
C0 lê Chat para aprender padrões/erros
Copilot e Chat usam plugin-ui
Copilot e Chat usam Core/Keycloak/Gateway
futuro package neutro pode ter ambos como consumidores se extraído corretamente
```

Não existe fase de migração do Chat para o Copilot nesta iniciativa.

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
- Value Objects e aggregates Copilot-owned;
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
- Evidence coordination;
- Meeting/Frontline/media session orchestration via ports.

### Interfaces
- REST;
- streaming/SSE quando escolhido;
- realtime/media transport boundaries quando comprovados;
- event consumers;
- DTOs/schemas.

### Infrastructure
- PostgreSQL;
- Core API adapter;
- generic Domain API/OpenAPI adapter;
- LLM/embedding provider;
- vector/search store;
- OCR/Vision/STT/TTS;
- realtime media transport;
- file/object/media storage;
- device context;
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
media UI state      → MFE/browser session; durable refs only if needed
local UI state      → component/hooks
durable work state  → Copilot API
```

MFE não vira owner de Workflow/Case/Decision/Watch nem de machine truth.

## 9. Portal integration

### Registered app

Core manifesto registra Copilot como `microfrontend`/`federated`.

Portal não precisa de catálogo manual porque AppLauncher/AppHost usam `apps/routes` do Core.

### Federated lifecycle

MFE segue convenções `plugins/vite/federation.shared.ts` com React singleton, `@delpi/plugin-ui`, `remoteEntry.js` e `mount()/unmount()`.

### Global/Meeting/Frontline hosts

Portal deve permanecer thin host:

```text
CopilotGlobalHost/Surface Host
→ monta o mesmo Copilot MFE
→ fornece host props/context/device capabilities
→ recebe typed PlatformCommands
```

Sem AI/media intelligence no Portal.

## 10. Workspace Context

Portal/MFEs/device adapters produzem contexto limitado e tipado:

```text
appId
routeId
EntityRef[]
filters
selection
dateRange
visibleDataRefs
bounded device/session metadata
```

Em produção, OP/máquina/produto/operação/lote/posto usam `EntityRef` quando houver owner/ID real.

Não criar `FrontlineContext` paralelo por default.

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

PlatformCommand não é usado como caminho genérico para comando físico de máquina.

## 12. Business Action architecture — nativa do Copilot

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

Texto, voz, Meeting e Frontline convergem para essa mesma cadeia.

Isso não depende de `minha-delpi-ai-api`.

## 13. Core/RBAC integration

Copilot API:

1. valida JWT;
2. resolve Core current user/context;
3. consulta apps/routes/permissions;
4. restringe capability candidates;
5. encaminha identity/token conforme contrato seguro;
6. Domain API revalida regra/permissão.

Invariante:

```text
Copilot effective capabilities ⊆ user effective capabilities
```

Device identity nunca substitui user authorization.

## 14. Evidence and Business Graph

Shared primitives:

```text
EntityRef
RelationshipRef
SourceRef
EvidenceRef
OutcomeRef
CorrelationContext
MediaRef? only if C0 proves transversal need
```

Business Graph guarda relações/referências/provenance, não cópias mestres.

Mídia aponta para Evidence/MediaRef, não vira master data.

## 15. Intelligence Core e multimodalidade

Depois de C1/C2:

```text
input + workspace + attachments/media
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

Progressão:

```text
document/image
→ speech
→ short video/screen
→ advanced realtime only after evidence
```

## 16. Meeting Mode architecture

Meeting é aplicação/use cases dentro do mesmo Copilot runtime:

```text
explicit media session
→ transcript/Evidence
→ authorized business reads
→ decisions/pending topics
→ candidate actions
→ ata artifact
→ Task/Case/Room/Workflow
```

Sem executor de negócio próprio.

Semântica obrigatória:

```text
transcript != summary != human decision != candidate action != executed action
```

## 17. Frontline architecture

```text
user identity
+ shared/private device
+ WorkspaceContext(EntityRefs)
+ voice/camera
→ Copilot API
→ Knowledge/API/Graph/Evidence
→ guidance
→ governed escalation/action
```

Frontline não cria outro planner, RBAC, Evidence ou Workflow runtime.

## 18. Media/privacy architecture

Capture precisa ser explícita. Diferenciar:

```text
transient capture
transcript
raw audio
raw video
screen capture
derived Evidence
meeting artifact
frontline record
```

Cada classe pode ter retention/access distintos.

Data minimization é default; raw media persistence é opt-in por purpose/policy, não consequência da feature.

## 19. Durable Work

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

Meeting/Frontline podem criar/referenciar essas unidades, sem engines paralelas.

## 20. Interaction Rooms

C0 mapeia salas existentes antes de criar nova sala:

```text
REUSE | EXTEND | ADAPTER | CREATE_REQUIRED
```

## 21. Industrial/OT safety boundary

Copilot não é safety controller.

Target default:

```text
OT telemetry/read
→ approved Adapter
→ EntityRef/Evidence
→ analysis/recommendation
```

Proibido por default:

```text
free-form LLM
→ generic executor
→ PLC/CNC/robot/machine
```

Qualquer future actuation exige architecture/gate separado com deterministic typed commands, allowlist, machine-state/preconditions, industrial owner, independent safety PLC/interlocks, human authorization as required, simulation/test environment, fail-safe e audit.

L5 do Copilot empresarial não concede OT.

## 22. Quality/computer vision boundary

Visual finding é Evidence/Hypothesis por default.

Quando processo oficial exige medição/tolerância/equipment/inspector:

```text
visual finding
→ official inspection source/rule
→ authorized quality decision
```

Somente capability explicitamente validada pode automatizar decisão de inspeção.

## 23. Deploy/infra

Copilot possui independentemente:

- Dockerfiles;
- dependencies;
- migration chain;
- health;
- Gateway dev/prod route;
- Compose service;
- env settings;
- manifest;
- registration script;
- test suites;
- logs/metrics;
- rollback.

Realtime/media pode exigir tuning/storage externo, mas não cria outro product runtime.

## 24. Architecture patterns

Aplica `49` integralmente:

- Ports & Adapters para Core/Domain APIs/LLMs/media/stores;
- Use Cases na Application;
- Repository somente para Copilot-owned persistence;
- Media Pipeline para ingest/extraction/evidence;
- Realtime Session pattern apenas quando necessário;
- State Machines para lifecycle;
- Policy para Decision/Retention/Consent;
- Outbox/idempotency quando necessário;
- no speculative abstraction.

## 25. Generalization

Target precisa suportar sem core patch específico:

- nova API/OpenAPI provider;
- novo app/route;
- novo Expertise Pack;
- novo Playbook;
- novo entity/relationship type;
- novo iframe compatível;
- novo media/provider adapter quando contract equivalente;
- novo model/provider por Compute Policy.

## 26. Sequência arquitetural

```text
C0 platform/application/media/privacy/OT foundations
↓
C1 standalone bootstrap
↓
C2 workspace/operational context + platform commands
↓
C3 intelligence + multimodal foundations
↓
C4 reads + graph
↓
C5 writes + durable foundation
↓
C6 product work + Meeting/Frontline + proactivity/ecosystem
↓
C7 advanced realtime + autonomy/optimization/rollout
```

## 27. Critério de sucesso estrutural

O Copilot está corretamente arquitetado quando podemos desligar `minha-delpi-ai-api` e `plugins/minha-delpi-chat` e ele continua funcional, e quando Meeting/Frontline podem evoluir sem criar novo RBAC/planner/executor/Evidence runtime.

Adicionalmente:

```text
voice/image/video ≠ permission escalation
shared device ≠ shared user state
process observation ≠ automatic learning
visual finding ≠ official quality fact by default
Copilot autonomy ≠ industrial safety authority
```

Esses testes conceituais são obrigatórios.