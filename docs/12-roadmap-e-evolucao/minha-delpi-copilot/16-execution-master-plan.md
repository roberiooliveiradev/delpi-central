# Minha DELPI Copilot — Plano Mestre Executável

**Status:** planejamento executável canônico  
**Owner arquitetural:** plataforma Minha DELPI  
**Autoridade de ordem:** **este documento é a única fonte de verdade para a sequência de implementação**  
**Próxima etapa:** `C0.S0`  
**DoD:** [`14-definition-of-done.md`](./14-definition-of-done.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Objetivo

Construir o Minha DELPI Copilot em ordem **foundation-first**, estabilizando authorities, contratos, estados, ports e gates antes de funcionalidades que dependem deles.

O objetivo explícito é evitar:

- refatoração previsível por contrato criado tarde;
- duas abstrações para a mesma responsabilidade;
- migrations sucessivas para o mesmo conceito;
- implementação piloto que depois precisa ser generalizada;
- catálogos paralelos;
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
17. `PARTIAL`, `INCONCLUSIVE`, `LEGACY_FALLBACK` material, `TEST_NOT_RUN` e evidence stale bloqueiam fechamento.

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
C0 — Fundação arquitetural e contratos universais
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

# C0 — Fundação arquitetural e contratos universais

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

## C0.S4 — Cross-cutting semantics

Congelar antes das features:

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

## C0.S5 — Contract harness e RED gates

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
```

---

# C1 — Portal, navegação, entidades e Workspace Context

Objetivo: estabelecer a interação segura com a plataforma antes de Business Actions.

## C1.S1 — Authorized Portal Capability Projection
`/me/apps` → authorized app/route capabilities, sem lista manual.

## C1.S2 — CopilotBridge
Validator + revalidation + handlers genéricos + typed result + trace.

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

## C2.S2 — Expertise Catalog/Repository
Implementar authority versionada conforme contrato C0.

## C2.S3 — Expertise retrieval/composition
Top-K semântico + policy/ACL + bounded context; unknown pack sem core patch.

## C2.S4 — Domain Playbook Catalog/retrieval
Método → stages/evidence/criteria; não endpoint.

## C2.S5 — Knowledge ACL integration
Expertise/project preference nunca amplia knowledge visibility.

## C2.S6 — Multimodal Evidence Adapter
Reaproveitar document vision/drawing analysis e produzir `EvidenceRef`/provenance/confidence.

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
read/write/risk/sensitivity/confirmation/idempotency/policy derivados por owner canônico.

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

## C4.S2 — Impact Preview
Arguments finais + evidence relevante + sensitivity + effect summary + hash.

## C4.S3 — Human decision/approval
confirm/reject/expire/invalidate; approval workflow quando policy exigir.

## C4.S4 — Idempotency/concurrency
Chave nativa do domínio preferida; locking/dedupe para retry/resume quando necessário.

## C4.S5 — Generic write execution
Policy/RBAC revalidation imediatamente antes de execute; no DOM write.

## C4.S6 — Outcome verification
Verificar resultado real, gerar outcome/evidence/audit e deep link.

## C4.S7 — Decouple action availability from legacy agent activation
Remover gate material `userActivatedAgent` somente após capability/policy tests.

## C4.S8 — Replace soft handoff
Retrieval/replan/clarify; não trocar agente departamental.

## C4.S9 — Write gate
Unauthorized, payload changed, stale approval, duplicate request, backend conflict, partial/ambiguous outcome, send/stream parity.

---

# C5 — Durable Work

Objetivo: transformar execução de turno em trabalho persistente sem duplicar planner/executors.

## C5.S1 — Durable Workflow Runtime
Persistência de workflow/steps/checkpoints + crash/restart semantics.

## C5.S2 — Wait states
- `wait_user`;
- `wait_approval`;
- `wait_event`;
- timeout/cancel.

## C5.S3 — DAG runner
Dependências, parallel safe reads, writes serializados quando necessário, budget/loop limit.

## C5.S4 — Copilot Task
Task é unidade operacional curta/média vinculada a workflow e evidence/outcomes.

## C5.S5 — Copilot Case + Evidence Board
Case é unidade de investigação/trabalho prolongado; não duplica sistema existente se C0 identificar owner reutilizável.

## C5.S6 — Interaction Room integration
Reutilizar sala existente quando possível; Case/Room compartilham refs, nunca ACL implícita.

## C5.S7 — Copilot Inbox
`waiting_for_user | working | completed | alerts`, ligada a Task/Case/Workflow/EntityRef.

## C5.S8 — Persist/reload/resume gate
Crash após write, duplicate event, concurrent resume, policy change durante wait, F5, cancel, partial failure.

---

# C6 — Proatividade + AI-ready Ecosystem + Governed Learning

## C6.S1 — Watch OBSERVE/ADVISE
Event-driven quando infraestrutura permitir; dedupe/cooldown/expiry + permission revalidation.

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

## C7.S5 — Legacy agent-routing cutover
Parar novas dependências de `agent_id`; remover handoff/gates/fallbacks materiais; residual scan.

## C7.S6 — Progressive rollout
internal → cohort → app waves → reads → writes → durable work → watch selected → autonomy selected.

## C7.S7 — Final verification
R1–R11 + CP coverage + unknown app/provider/pack/iframe/relation + security + accessibility + rollback.

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
→ adversarial review
→ semantic residual search
→ postconditions
→ COMPLETE_GATE
→ docs + ledger
→ unlock next
```

## 8. Regra anti-refatoração previsível

Antes de qualquer nova tabela/service/schema/perfil de evento, responder:

1. O primitive já existe em C0?
2. Já existe owner/repository equivalente no projeto?
3. Esta feature está tentando redefinir EntityRef/Evidence/Decision/Workflow/Event?
4. Existe segunda authority sendo criada?
5. O próximo estágio conhecido exigiria mudar este contrato?
6. A implementação é genérica para sibling/unknown case?

Se a resposta 3, 4 ou 5 for “sim”, **não implementar** até corrigir a fundação.

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