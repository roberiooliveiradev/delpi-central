# Minha DELPI Copilot — Plano Mestre Executável

**Status:** planejamento executável canônico  
**Owner arquitetural:** plataforma Minha DELPI  
**Autoridade de ordem:** **este documento é a única fonte de verdade para a sequência de implementação**  
**Próxima etapa:** `C0.S0`  
**Arquitetura/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**DoD:** [`14-definition-of-done.md`](./14-definition-of-done.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Objetivo

Construir o Minha DELPI Copilot em ordem **foundation-first**, estabilizando authorities, contratos, estados, ports, arquitetura de código, design patterns e gates antes de funcionalidades que dependem deles.

O objetivo explícito é evitar:

- refatoração previsível por contrato criado tarde;
- duas abstrações para a mesma responsabilidade;
- migrations sucessivas para o mesmo conceito;
- implementação piloto que depois precisa ser generalizada;
- catálogos paralelos;
- design patterns escolhidos de forma inconsistente por etapa;
- infra/framework vazando para camadas internas;
- overengineering especulativo;
- retrabalho de prompts, schemas e testes;
- gasto desnecessário de tokens do Cursor por execução fora de ordem.

```text
FOUNDATIONS
→ PLATFORM/CONTEXT
→ INTELLIGENCE CORE
→ BUSINESS READS + GRAPH
→ GOVERNED WRITES
→ DURABLE WORK
→ PROACTIVITY + ECOSYSTEM
→ OPTIMIZATION + ROLLOUT
```

## 2. Regra de autoridade documental

A ordem é definida somente aqui.

A arquitetura de código e escolha de design patterns é definida em:

```text
49-architecture-and-design-patterns-standard.md
```

Documentos como:

- `32-expertise-runtime-implementation-plan.md`;
- `44-operational-intelligence-implementation-plan.md`;
- `45-operational-intelligence-testing-gates.md`;
- `46-operational-intelligence-requirements.md`;
- `47-cursor-operational-intelligence-extension.md`;

são **detalhes temáticos** e não podem liberar uma implementação antes da fase `C*` correspondente estar desbloqueada neste plano.

Se qualquer documento divergir da ordem abaixo:

```text
16-execution-master-plan.md vence.
```

Se uma implementação divergir do style/layers/patterns normativos sem decisão arquitetural explícita:

```text
49-architecture-and-design-patterns-standard.md vence.
```

## 3. Invariantes

1. Um único Copilot de produto; departamentos especializam por expertise/playbooks, não por runtimes separados.
2. Não criar segundo planner/tool executor fora de `minha-delpi-ai-api`.
3. Business Actions usam OpenAPI + Action Catalog + executor genérico canônico.
4. Capability Projection é índice/projeção, nunca segunda authority técnica.
5. Expertise e Playbooks orientam; não concedem permission nem carregam endpoint técnico como authority.
6. Core API continua authority de apps/rotas/permissões.
7. Workspace Context é contexto, nunca autorização.
8. Entity/Evidence/Workflow/Task/Case/Decision/Event usam contratos compartilhados antes de features especializadas.
9. Business Graph referencia entidades/sources; não replica bancos operacionais.
10. Platform Actions usam IDs tipados e Portal resolve/revalida targets; LLM não inventa URL.
11. Iframe usa bridge tipado para experiência; Business Action não é DOM automation.
12. Writes passam por RBAC/policy/Decision Gate/idempotency/audit conforme risco.
13. Workflow durável não pode duplicar write em retry/resume.
14. Watch não cria autoridade nova e revalida permission/policy no disparo.
15. Não persistir chain-of-thought.
16. Qualquer feature nova deve reutilizar os primitives C0; criar contrato paralelo é FAIL arquitetural.
17. Runtime segue Clean Architecture + Ports & Adapters + DDD pragmático conforme `49`; patterns adicionais só entram quando a matriz/Abstraction Gate justificar.
18. Domain/Application não dependem de framework/provider concreto; wiring concreto ocorre no Composition Root.
19. Estado durável de negócio permanece no backend; frontend não se torna authority de Workflow/Case/Decision/Watch/Graph.
20. Migração legada usa Adapter/Anti-Corruption Layer/Strangler quando aplicável, sempre com exit criteria.
21. `PARTIAL`, `INCONCLUSIVE`, `LEGACY_FALLBACK` material, `TEST_NOT_RUN` e evidence stale bloqueiam fechamento.

## 4. Dependência crítica da Minha DELPI AI

A correção OpenAPI-first/LLM-decoupling permanece uma dependência externa enquanto os gates relevantes não estiverem `PASS` no candidate vigente.

Consequência:

```text
C0–C2
→ podem avançar sem Business Action production-ready

C3+ que dependa de Business Actions reais
→ bloqueado até gates OpenAPI-first/tool-routing/argument-binding/evals aplicáveis PASS
```

Não recriar a Onda J dentro do Copilot.

## 5. Grafo canônico

```text
C0 — Fundação arquitetural, patterns e contratos universais
 |
 v
C1 — Portal, navegação, entidades e Workspace Context
 |
 v
C2 — Intelligence Core: Copilot único, expertise, knowledge, multimodal e evidence
 |
 v
C3 — Business Reads + DELPI Business Graph + análise cross-domain
 |
 v
C4 — Governed Writes + Decision Gates + idempotência
 |
 v
C5 — Durable Work: Workflows + Tasks + Cases + Rooms + Inbox
 |
 v
C6 — Proatividade + AI-ready Ecosystem + Governed Learning
 |
 v
C7 — Autonomia avançada + Simulation + Model Routing + Rollout + cleanup
```

Nenhuma fase dependente começa porque “já existe código parcial”. Só começa quando o gate anterior exigido estiver `PASS`.

---

# C0 — Fundação arquitetural, patterns e contratos universais

## C0.S0 — Rebaseline e inventário total

Antes de runtime diff, inventariar com arquivo/símbolo/owner/consumer:

### Plataforma
- Portal Router/AuthContext/AppHost/AppLauncher;
- Core `/me`, `/me/apps`, `/me/routes`;
- manifesto/routes/permissions;
- MFE/iframe/external lifecycle;
- salas de interação existentes;
- notifications/inbox existentes.

### AI
- turn understanding;
- planner;
- Action Catalog/importer/index;
- generic executor;
- confirmation/policy;
- RAG/knowledge ACL;
- persistence/session/turn metadata;
- send/stream/simulate;
- document vision/drawing analysis;
- model/provider abstractions;
- tracing/evals.

### Agents/skills legados
- agent entities/repositories/controllers/admin;
- `AgentSpecializationService`;
- `ChatWorkspaceAgentActivationService`;
- `ChatSoftAgentHandoffService`;
- `ChatSkillRegistry`;
- `agent_id`, `chat_mode`, project default agent;
- knowledge/actions/tools condicionados a agent;
- UI de agent/handoff.

### Operação corporativa
- canonical entity IDs por domínio;
- relações cross-domain existentes;
- event bus/event types;
- workers/queues/background jobs;
- approvals;
- audit/provenance;
- workflows persistentes;
- requests/cases existentes que possam ser generalizados;
- idempotency support;
- knowledge lifecycle.

### Arquitetura e padrões do código atual
- camadas/packages `domain/application/interfaces/infrastructure` ou equivalentes;
- use cases/application services;
- ports/adapters/gateways/repositories;
- DI/composition root;
- DTO/mappers e boundary schemas;
- error/result taxonomy;
- state machines/lifecycle patterns;
- domain events/integration events/event envelopes;
- outbox/event publication;
- retry/timeout/circuit-breaker/idempotency;
- transaction/unit-of-work conventions;
- migrations/compatibility/strangler patterns;
- organização frontend `ui/state/data`;
- query/cache, Workspace state, Conversation state e Local UI state;
- conventions para hooks/reducers/stores/adapters;
- testing doubles/contract/integration patterns.

Classificar cada conceito existente:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
DEPRECATE
REMOVE
NOT_PROVEN
```

**Saídas obrigatórias:**
- `18-app-onboarding-matrix.md` atualizado;
- `17-component-and-contract-map.md` atualizado com fatos;
- matriz de migração agent→expertise;
- mapa entity/event/workflow/room/notification;
- `49-architecture-and-design-patterns-standard.md` revalidado contra patterns reais do repositório;
- divergências entre `49` e padrão real classificadas como `ALIGN_DOC`, `MIGRATE_CODE`, `ADR_REQUIRED` ou `NOT_PROVEN`;
- ledger com `HEAD_BEFORE` e evidence.

**Proibido:** runtime diff de Copilot antes de C0.S0 fechar.

## C0.S1 — Freeze de authorities e bounded contexts

Definir owner canônico para:

```text
identity
permissions
app/route navigation
business action contract
capability projection
workspace context
entity identity
relationship identity
knowledge visibility
expertise
playbook
evidence/provenance
policy/sensitivity
decision gate
workflow/task/case
room/inbox
watch/event
model/compute policy
audit/observability
```

Toda responsabilidade deve possuir um owner; caches/indexes são derivados.

Também congelar/revalidar os bounded contexts conceituais do `49`, sem obrigar package artificial quando o código real já possui owner equivalente:

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

## C0.S2 — Freeze de primitives e envelopes compartilhados

Antes de implementar features dependentes, definir/reutilizar semanticamente os contratos abaixo. Nomes finais dependem do inventário real.

### Identidade e correlação
- `CorrelationContextV1` / request-turn-workflow correlation;
- subject/user reference seguro.

### Entidades e fontes
- `EntityRefV1`;
- `RelationshipRefV1`;
- `SourceRefV1`;
- `OutcomeRefV1`.

### Evidence/provenance
- `EvidenceRefV1`;
- `MultimodalEvidenceRefV1`;
- freshness/confidence/provenance semantics;
- epistemic class: `FACT | CALCULATION | HYPOTHESIS | CONCLUSION | RECOMMENDATION`.

### Capabilities/plataforma
- `CapabilityProjectionV1`;
- `PlatformCommandV1`;
- `PlatformCommandResultV1`;
- `WorkspaceContextV1`;
- `IframeBridgeEnvelopeV1`.

### Especialização
- `ExpertisePackV1`;
- `ExpertiseSelectionV1`;
- `ExpertiseContextV1`;
- `DomainPlaybookV1`.

### Policy/decisão
- `DecisionGateRequestV1`;
- `DecisionGateDecisionV1`;
- níveis mínimos: `NO_GATE | ACKNOWLEDGE | CONFIRM | REVIEW_AND_CONFIRM | APPROVAL_WORKFLOW | BLOCK`.

### Trabalho durável
- `WorkflowPlanV1`;
- `WorkflowStepV1`;
- `TaskRefV1` + lifecycle enum;
- `CaseRefV1` + lifecycle enum;
- checkpoint/wait-state semantics.

### Eventos
- `EventEnvelopeV1` com source/type/entity refs/eventId/occurredAt/payloadRef;
- dedupe/correlation semantics.

### Auditoria
- `AuditEventV1` ou integração explícita com contrato canônico existente.

C0 define **contratos e semântica**, não precisa criar todas as tabelas/runtime correspondentes.

## C0.S3 — Ports, persistence boundaries e schema strategy

Antes de migrations, definir portas e owner de persistência:

- capability/expertise/playbook catalogs;
- evidence/provenance store somente se necessário;
- workflow/task/case repositories;
- graph relationship repository/index;
- event/watch repository;
- decision/approval persistence;
- audit integration.

Regra:

```text
reuse existing storage > extend existing owner > new storage only with proven gap
```

Definir desde já:
- IDs estáveis;
- versionamento;
- optimistic/concurrency rules;
- retention/LGPD;
- expand/cutover/cleanup migration pattern;
- index requirements;
- idempotency boundaries.

Patterns obrigatórios conforme `49`:

```text
external boundary → Port + Adapter
owned aggregate/lifecycle persistence → Repository
legacy incompatible model → Adapter + Anti-Corruption Layer
legacy gradual cutover → Strangler Fig
durable write/retry boundary → Idempotency
state + event atomicity → Transactional Outbox somente se requisito real
```

Não criar Repository para simples proxy HTTP nem nova storage authority por conveniência.

## C0.S4 — Cross-cutting semantics + architecture/pattern freeze

Congelar antes das features:

### Semântica transversal
- versioning compatibility;
- correlation IDs;
- provenance/freshness;
- error taxonomy;
- permission revalidation;
- retry/idempotency semantics;
- timeout/cancellation;
- payload size/budget;
- audit/redaction;
- feature flag ownership/exit criteria;
- no-CoT observability.

### Architecture style

```text
Clean Architecture
+ Ports & Adapters / Hexagonal
+ DDD pragmático
+ Event-Driven somente onde houver eventos reais
+ State Machines para lifecycle não trivial
+ CQRS leve somente quando houver assimetria material
```

### Layer responsibilities

Backend:

```text
Domain         → entities/value objects/invariantes/policies puras
Application    → use cases/orchestration/ports
Interfaces     → controllers/DTOs/event boundaries/mappers
Infrastructure → DB/HTTP/OpenAPI/LLM/RAG/Vision/Event adapters
Composition    → DI/wiring concreto
```

Frontend:

```text
ui
state
data
```

Owners de estado:

```text
server state           → query/cache layer existente
workspace state        → Portal Workspace Context
conversation state     → chat/copilot state
local UI state         → component/hook
durable business state → backend canônico
```

### Dependency rules

- Domain/Application não importam framework/client/provider concreto;
- infrastructure implementa ports;
- business rules server-side não são duplicadas no frontend;
- concrete wiring ocorre no Composition Root;
- ORM/persistence model não vira API contract automaticamente.

### Pattern Decision Matrix

Congelar/revalidar a matriz do `49` para:

- Port + Adapter;
- Use Case/Application Service;
- Repository;
- State Machine;
- Policy/Specification;
- Strategy;
- Adapter/Anti-Corruption Layer;
- Strangler Fig;
- Command + Handler;
- Transactional Outbox;
- Idempotency;
- Event-Driven;
- Saga somente com compensação real;
- resilience patterns;
- DTO + Mapper;
- Dependency Injection/Composition Root;
- Factory/Builder quando justificadas;
- CQRS leve quando necessário.

### Abstraction Gate

Antes de criar `interface/port/repository/factory/strategy/registry/base class/generic engine`, provar boundary/lifecycle/variação/consumer/testability e inexistência de equivalente no repo.

Abstração puramente especulativa = FAIL.

### Exception process

Divergência material do `49` exige decisão arquitetural/ADR no padrão real do repo antes do código.

## C0.S5 — Contract + architecture conformance harness e RED gates

Criar/reutilizar testes de contrato para os primitives materiais:

- invalid schema/version;
- unauthorized target;
- evidence sem provenance quando exigida;
- pack/playbook tentando conceder permission;
- Decision Gate com arguments hash divergente;
- workflow resume sem idempotency protection;
- duplicate event;
- entity/relationship permission leakage;
- iframe invalid origin/source/session;
- secret/JWT em context/bridge/state;
- send/stream parity do envelope comum.

Criar/reutilizar checks de conformidade arquitetural quando tecnicamente viáveis:

- Domain/Application sem imports proibidos de framework/infra;
- dependency direction preservada;
- frontend durable business state ausente;
- no duplicate primitive/contracts;
- adapter/port contract tests;
- state transition tests para lifecycle complexo;
- error translation tests;
- write retry/idempotency negatives;
- migration compatibility/residual checks quando aplicável.

## C0.S6 — FOUNDATION_FREEZE

Só desbloqueia C1 se:

```text
INVENTORY = PASS
AUTHORITIES = PASS
SHARED_PRIMITIVES = PASS
PERSISTENCE_BOUNDARIES = PASS
CROSS_CUTTING_SEMANTICS = PASS
CONTRACT_HARNESS = PASS
FOUNDATION_DUPLICATION = 0 material

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

---

# C1 — Portal, navegação, entidades e Workspace Context

Objetivo: estabelecer a interação segura com a plataforma antes de Business Actions.

## C1.S1 — Authorized Portal Capability Projection
`/me/apps` → authorized app/route capabilities, sem lista manual.

Pattern esperado: projection + Port/Adapter quando houver boundary + use case/application orchestration; não criar catalog owner paralelo.

## C1.S2 — CopilotBridge
Validator + revalidation + handlers genéricos + typed result + trace.

Pattern esperado: Command + Handler + Adapter; registry por tipo genérico, nunca por app.

## C1.S3 — Navegação mínima
- `portal.open_app`;
- `portal.open_route`;
- depois `portal.open_entity` usando `EntityRefV1`/route metadata.

## C1.S4 — Transport AI ↔ Portal
Paridade send/stream; Chat MFE transporta, não autoriza.

## C1.S5 — Workspace Context Store
Implementar contrato C0, lifecycle app/route/entity/filter/selection/dateRange.

## C1.S6 — MFE Context/Deep-link adapter
Helper compartilhado para contexto e entity refs; sem business logic.

## C1.S7 — Iframe Bridge
`PORTAL_ONLY` universal + handshake seguro para classes superiores.

Pattern esperado: Adapter + Anti-Corruption Layer + typed message boundary.

## C1.S8 — Contextual UX
Context chips, abrir app/entidade, explicar view, remover contexto.

## C1.S9 — Security/generalization gate
TOCTOU, unauthorized, stale context, F5/logout, unknown app/iframe, URL arbitrary negative.

---

# C2 — Intelligence Core

Objetivo: estabilizar a inteligência transversal **antes** de conectá-la massivamente a Business Actions.

## C2.S1 — Single Copilot session model
- sessão nova sem `agent_id` obrigatório;
- compatibilidade legada explicitamente temporária;
- projeto/contexto separado de identidade do Copilot.

Migração: Adapter + Anti-Corruption Layer + Strangler, não dual-runtime permanente.

## C2.S2 — Expertise Catalog/Repository
Implementar authority versionada conforme contrato C0.

Repository somente se C0 provar authority/lifecycle persistido próprio.

## C2.S3 — Expertise retrieval/composition
Top-K semântico + policy/ACL + bounded context; unknown pack sem core patch.

Strategy somente se existirem estratégias reais/intercambiáveis; não criar Strategy só para embrulhar uma implementação.

## C2.S4 — Domain Playbook Catalog/retrieval
Método → stages/evidence/criteria; não endpoint.

## C2.S5 — Knowledge ACL integration
Expertise/project preference nunca amplia knowledge visibility.

## C2.S6 — Multimodal Evidence Adapter
Reaproveitar document vision/drawing analysis e produzir `EvidenceRef`/provenance/confidence.

Extraction strategies são permitidas quando a variação native/OCR/VLM for real e o boundary justificar.

## C2.S7 — Evidence/epistemic synthesis foundation
Normalizar facts/calculations/hypotheses/conclusions/recommendations e source refs.

## C2.S8 — Agent migration shadow mode
Comparar expertise retrieval com comportamento legado sem usar shadow como fallback permanente.

## C2.S9 — Operational activity/observability
Mostrar etapas operacionais, expertise aplicada, sources e limitações; nunca CoT.

## C2.S10 — Intelligence gate
Positive/sibling/negative, unknown expertise, metamorphic expertise, multimodal injection, session-without-agent, unauthorized knowledge/capability.

---

# C3 — Business Reads + DELPI Business Graph

**Gate:** OpenAPI-first/Action Catalog relevante precisa estar `PASS` para produção.

## C3.S1 — Business Capability Projection
Allowed Action Catalog → projection; executor sempre resolve source canônico.

## C3.S2 — Operational metadata
read/write/risk/sensitivity/decision/idempotency/policy derivados por owner canônico.

## C3.S3 — Generic read parity
UI/Copilot usam o mesmo use case/API; known/sibling/unknown provider/metamorphic.

## C3.S4 — Normalized read result + Evidence
Resultado autorizado produz `OutcomeRef`/`EvidenceRef` quando aplicável, com freshness/provenance.

## C3.S5 — Business Graph minimal runtime
Implementar somente após `EntityRef`/`RelationshipRef` C0:
- registry/index de relações;
- permission-aware traversal;
- source API fetch após traversal;
- cycle/depth budget;
- authoritative vs inferred relationship provenance.

Arquitetura esperada: Ports & Adapters; Repository/index apenas se houver materialização própria comprovada; permission traversal em Policy/Specification quando combinação justificar.

Piloto recomendado:

```text
reclamação → produto → OP/lote → material → fornecedor
```

## C3.S6 — Cross-domain read analysis
Business Graph + APIs + expertise + evidence; sem write.

## C3.S7 — Read/evidence/graph gate
RBAC, stale source, conflicting evidence, unknown relation sibling, no planner hardcode, R1–R11 aplicáveis.

---

# C4 — Governed Writes + Decision Gates

Objetivo: somente depois dos reads estarem estáveis, liberar alterações com governança proporcional ao risco.

## C4.S1 — Decision Gate Engine
Implementar os níveis definidos em C0 com deterministic policy owner.

Pattern esperado: Policy + State Machine; prompt livre não é policy.

## C4.S2 — Impact Preview
Arguments finais + evidence relevante + sensitivity + effect summary + hash.

## C4.S3 — Human decision/approval
confirm/reject/expire/invalidate; approval workflow quando policy exigir.

## C4.S4 — Idempotency/concurrency
Chave nativa do domínio preferida; locking/dedupe para retry/resume quando necessário.

## C4.S5 — Generic write execution
Policy/RBAC revalidation imediatamente antes de execute; no DOM write.

Writes não idempotentes não recebem retry cego.

## C4.S6 — Outcome verification
Verificar resultado real, gerar outcome/evidence/audit e deep link.

## C4.S7 — Decouple action availability from legacy agent activation
Remover gate material `userActivatedAgent` somente após capability/policy tests.

Migração via Strangler/ACL; não copiar allowed tools para nova authority.

## C4.S8 — Replace soft handoff
Retrieval/replan/clarify; não trocar agente departamental.

## C4.S9 — Write gate
Unauthorized, payload changed, stale approval, duplicate request, backend conflict, partial/ambiguous outcome, send/stream parity.

---

# C5 — Durable Work

Objetivo: transformar execução de turno em trabalho persistente sem duplicar planner/executors.

## C5.S1 — Durable Workflow Runtime
Persistência de workflow/steps/checkpoints + crash/restart semantics.

Pattern esperado: Application orchestration + State Machine + Idempotency; external dependencies via ports/adapters.

## C5.S2 — Wait states
- `wait_user`;
- `wait_approval`;
- `wait_event`;
- timeout/cancel.

## C5.S3 — DAG runner
Dependências, parallel safe reads, writes serializados quando necessário, budget/loop limit.

Saga somente quando houver múltiplos writes distribuídos e compensações reais.

## C5.S4 — Copilot Task
Task é unidade operacional curta/média vinculada a workflow e evidence/outcomes.

## C5.S5 — Copilot Case + Evidence Board
Case é unidade de investigação/trabalho prolongado; não duplica sistema existente se C0 identificar owner reutilizável.

Repository/Aggregate apenas se lifecycle/authority própria forem comprovados.

## C5.S6 — Interaction Room integration
Reutilizar sala existente quando possível; Case/Room compartilham refs, nunca ACL implícita.

## C5.S7 — Copilot Inbox
`waiting_for_user | working | completed | alerts`, ligada a Task/Case/Workflow/EntityRef.

Preferir materialized/read model sobre authorities existentes; Inbox não vira workflow engine.

## C5.S8 — Persist/reload/resume gate
Crash após write, duplicate event, concurrent resume, policy change durante wait, F5, cancel, partial failure.

---

# C6 — Proatividade + AI-ready Ecosystem + Governed Learning

## C6.S1 — Watch OBSERVE/ADVISE
Event-driven quando infraestrutura permitir; dedupe/cooldown/expiry + permission revalidation.

Pattern esperado: Event-Driven + State Machine + dedupe/idempotency; polling app-specific não é default.

## C6.S2 — AI-ready SDK/templates
Workspace Context, EntityRef, deep link, iframe bridge, contract fixtures.

## C6.S3 — Readiness scanner/onboarding waves
L1–L5 + iframe classes + capability/evidence/workflow readiness.

## C6.S4 — Project preferences
Preferred expertise/knowledge/templates/guidance sem conceder permission.

## C6.S5 — Organizational Knowledge lifecycle
Reference/Decision/Experience/Solution Pattern com owner/version/provenance/review.

## C6.S6 — Governed Learning Loop
feedback → candidate → eval → review → publish → rollout; nunca aprendizado automático de production behavior.

## C6.S7 — Expertise Studio
Draft/review/eval/publish/rollback/admin RBAC.

Pattern esperado: Use Cases + State Machine + admin RBAC; Studio não é agent builder.

## C6.S8 — Admin/coverage
Capabilities, apps, expertise, playbooks, workflow/case/watch coverage, metrics.

## C6.S9 — Proactivity/ecosystem gate
No unauthorized event action, no auto-publish, unknown app/pack onboarding, coverage evidence.

---

# C7 — Optimization, autonomia e rollout final

## C7.S1 — Autonomia L0–L5 final
L5 OFF por default; allowlist/limits/budgets/kill switch.

## C7.S2 — Watch ACT
Somente capability allowlisted + Decision Gate/autonomy policy + audit.

## C7.S3 — What-if / Simulation pilots
Somente modelos owner/reproduzíveis. `simulate` nunca implica `apply`.

## C7.S4 — Model Router / Compute Policy
Somente depois de baseline de qualidade/latência/custo e provider data-policy.

Pattern esperado: Policy/Strategy somente após variações reais/baseline; não espalhar provider/model names pelo domain/application.

## C7.S5 — Legacy agent-routing cutover
Parar novas dependências de `agent_id`; remover handoff/gates/fallbacks materiais; residual scan.

## C7.S6 — Progressive rollout
internal → cohort → app waves → reads → writes → durable work → watch selected → autonomy selected.

## C7.S7 — Final verification
R1–R11 + CP coverage + unknown app/provider/pack/iframe/relation + security + accessibility + rollback + architecture conformance.

## C7.S8 — Product Complete gate
Só declarar produto completo se requisitos materiais do release estiverem PASS ou `OUT_OF_SCOPE_WITH_DECISION` justificável.

---

## 6. Mapeamento dos planos temáticos

### Expertise (`E*`)

| Track antigo | Fase canônica |
|---|---|
| E0–E1 | C0 |
| E2–E4 | C2 |
| E5–E8 | C4 |
| E9–E10 | C2/C5 conforme função |
| E11–E12 | C6 |
| E13 | C7 |

### Inteligência operacional (`O*`)

| Track antigo | Fase canônica |
|---|---|
| O0 | C0 |
| O1 Evidence contracts | C0; runtime C2/C3 |
| O2 Business Graph | contracts C0; runtime C3 |
| O3 Task | contracts C0; runtime C5 |
| O4 Durable Workflow | contracts C0; runtime C5 |
| O5 Case | contracts C0; runtime C5 |
| O6 Rooms | C5 |
| O7 Inbox | C5 |
| O8 Watch | C6; ACT C7 |
| O9 Decision Gates | contracts C0; runtime C4 |
| O10 Experience Knowledge | C6 |
| O11 Expertise Studio | C6 |
| O12 Simulation | C7 |
| O13 Model Router | C7 |

Esse mapeamento substitui qualquer sequência antiga conflitante nos documentos temáticos.

## 7. Protocolo obrigatório por subetapa

```text
REVALIDATE HEAD + git status
→ read applicable rules/docs
→ identify owner + architecture layer
→ select pattern from 49
→ run Abstraction Gate
→ dependency gate
→ READY_TO_EXECUTE
→ baseline
→ minimal correct owner-level implementation
→ producer/consumer wiring
→ unit/contract
→ integration
→ positive/sibling/negative
→ security/RBAC
→ generalization/metamorphic/unknown quando aplicável
→ architecture conformance review
→ adversarial review
→ semantic residual search
→ postconditions
→ COMPLETE_GATE
→ docs + ledger
→ unlock next
```

## 8. Regra anti-refatoração previsível

Antes de qualquer nova tabela/service/schema/perfil de evento/abstração, responder:

1. O primitive já existe em C0?
2. Já existe owner/repository equivalente no projeto?
3. Qual camada é dona dessa responsabilidade?
4. Qual pattern do `49` se aplica?
5. A abstração passa o Abstraction Gate?
6. Esta feature está tentando redefinir EntityRef/Evidence/Decision/Workflow/Event?
7. Existe segunda authority sendo criada?
8. O próximo estágio conhecido exigiria mudar este contrato?
9. A implementação é genérica para sibling/unknown case?
10. Existe padrão equivalente já comprovado no repositório?

Se 6, 7 ou 8 for “sim”, **não implementar** até corrigir a fundação.

Se 5 for “não”, preferir implementação simples sem abstração especulativa.

## 9. Primeira ordem efetiva

```text
C0.S0
→ C0.S1
→ C0.S2
→ C0.S3
→ C0.S4
→ C0.S5
→ C0.S6 FOUNDATION_FREEZE
→ C1.S1
```

Nenhum runtime feature work do Copilot deve preceder `FOUNDATION_FREEZE=PASS`.