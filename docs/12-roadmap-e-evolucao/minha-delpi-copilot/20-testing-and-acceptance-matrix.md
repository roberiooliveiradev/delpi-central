# Minha DELPI Copilot — Matriz Canônica de Testes e Aceitação

**Status:** gate transversal canônico  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Base:** regras `.cursor` + protocolo R1–R11 da Minha DELPI AI.

> Este documento absorve os gates funcionais da antiga extensão `45-operational-intelligence-testing-gates.md`. Se houver divergência, este arquivo prevalece.

## 1. Regra de evidence

Todo PASS material deve registrar, quando aplicável:

```text
gitSha
config/model/provider hash
dataset/corpus hash
OpenAPI hash
Action Catalog hash
Expertise Pack key/version/hash
Domain Playbook key/version/hash
multimodal extractor/model hash
schema/contract version
environment
runner/test version
timestamp
```

Mudança material posterior invalida evidence afetada.

## 2. Gate C0 — Foundations

### Authorities/ownership

Provar:

- um owner canônico por responsabilidade;
- cache/index não tratado como authority;
- nenhum duplicate catalog/state owner material;
- contracts existentes reutilizados quando equivalentes.

### Shared primitives

Positive/sibling/negative para, quando no escopo:

- `CorrelationContext`;
- `EntityRef`;
- `RelationshipRef`;
- `SourceRef`;
- `EvidenceRef`;
- `OutcomeRef`;
- `CapabilityProjection`;
- `PlatformCommand`;
- `WorkspaceContext`;
- `ExpertisePack/Selection/Context`;
- `DomainPlaybook`;
- `DecisionGate`;
- `WorkflowPlan/Step`;
- `TaskRef`;
- `CaseRef`;
- `EventEnvelope`;
- `IframeBridgeEnvelope`.

Negative obrigatório:

```text
invalid version/schema
technical endpoint authority dentro de expertise/playbook
permission override por pack/context
Evidence sem source/provenance quando required
Decision payload hash divergente
Event duplicado/replay inválido
secret/JWT em context/state/bridge
Entity/Relationship sem permission leakage protection
```

### FOUNDATION_FREEZE

C1 só libera se:

```text
INVENTORY = PASS
AUTHORITIES = PASS
PRIMITIVES = PASS
PERSISTENCE_BOUNDARIES = PASS
CROSS_CUTTING_SEMANTICS = PASS
CONTRACT_HARNESS = PASS
DUPLICATE_FOUNDATION = 0 material
```

## 3. Gate C1 — Platform/Context

Testar:

- `portal.open_app` autorizado;
- `portal.open_route` autorizado;
- `portal.open_entity` quando suportado;
- app/route/entity não autorizado;
- target inexistente;
- permission revogada entre plan/execute;
- URL arbitrária rejeitada;
- payload adulterado;
- send/stream parity;
- F5/back/forward;
- deep link inválido;
- Workspace Context bounded/sanitized;
- troca de app/entity/filter/date range;
- stale context;
- logout;
- contexto explícito novo vence inferência antiga;
- MFE sibling sem patch central.

### Iframe

- `PORTAL_ONLY` abre sem SDK interno;
- handshake válido;
- invalid origin/source/appId/version/session;
- context publish normalizado;
- visual command declarado;
- capability não declarada rejeitada;
- nenhum JWT/secret;
- tentativa de business write via visual command rejeitada;
- segundo iframe compatível funciona sem `if appId == ...`.

## 4. Gate C2 — Intelligence Core

### Single Copilot

- nova sessão sem `agent_id` obrigatório;
- sessão legada compatível durante migração;
- nenhuma tarefa normal exige troca de agente;
- project preference não cria outro runtime.

### Expertise

Positive:
- qualidade seleciona expertise relevante;
- desenho seleciona engenharia + multimodal;
- pedido cross-domain compõe packs.

Sibling:
- novo pack válido entra por contrato;
- segundo domínio sem planner patch.

Negative:
- pack irrelevante não ativa;
- pack não concede capability;
- pack não amplia Knowledge ACL;
- project preference não força expertise incompatível;
- pack não altera policy/system.

Generalization:
- unknown pack;
- metamorphic rename de key mantendo semântica.

### Playbooks

- applicability correta;
- irrelevante não selecionado;
- evidence checklist gera `MISSING`, não invenção;
- playbook não bypassa Decision Gate;
- endpoint técnico como authority é rejeitado;
- version/hash auditável.

### Multimodal/Evidence

- PDF textual;
- PDF rasterizado;
- imagem/desenho;
- região ilegível;
- page/region provenance;
- confidence/limitations;
- prompt injection em arquivo;
- extractor/model version auditável;
- multimodal funciona sem agente ativo;
- `perception evidence != domain conclusion`.

### Epistemic UX

- FACT possui source quando disponível;
- CALCULATION registra inputs/metodologia;
- HYPOTHESIS permanece rotulada;
- CONCLUSION lista evidence relevante;
- RECOMMENDATION não é tratada como fato;
- conflicting/stale source produz limitação explícita.

## 5. Gate C3 — Business Reads + Graph

### OpenAPI/Actions

- known action;
- semantic sibling;
- no-tool negative;
- unknown external OpenAPI real;
- true metamorphic provider/path/operationId rename;
- path/query/body args;
- required missing;
- enum/type/format;
- multiple providers;
- unauthorized;
- response normalization;
- R9 outcome;
- session-without-agent mantém action autorizada.

### Evidence

- read result gera source/outcome/evidence coerente;
- freshness correta;
- sensitive response redigida em logs;
- claim não sobrevive a permission revocation sem revalidation.

### Business Graph

- traversal autorizado;
- relation inexistente;
- authoritative vs inferred;
- node sem permission não vaza;
- source owner indisponível;
- stale/superseded relation;
- cycle/depth budget;
- novo entity/relationship type sem patch no planner;
- traversal retorna refs e depois busca source; não replica dataset inteiro.

## 6. Gate C4 — Governed Writes

### Decision Gates

- `NO_GATE` apenas quando policy permite;
- ACKNOWLEDGE;
- CONFIRM;
- REVIEW_AND_CONFIRM com impact preview;
- APPROVAL_WORKFLOW;
- BLOCK;
- arguments hash mudou;
- evidence material mudou;
- decision expired;
- approver sem permission;
- RBAC/policy revalidation imediatamente antes do write.

### Write execution

```text
write permitido
write sem permission
reject/expire
idempotency replay
concurrent submission
server conflict
ambiguous timeout
partial backend failure
sensitive redaction
result audit/deep link
```

Nenhum write pode passar somente por mockar o executor sob teste.

### Agent migration

- operational action não depende de `userActivatedAgent` após cutover;
- legacy session continua segura durante janela definida;
- soft handoff não é emitido;
- capability miss → retrieval/replan/clarify/unavailable;
- residual scan de `has_agent`, `switch_agent_and_resend`, `chat_mode == agent`, `agent allowed tools`.

## 7. Gate C5 — Durable Work

### Workflow

- dependent plan;
- parallel safe reads;
- writes serializados quando necessário;
- partial failure truthful;
- wait_user/resume;
- wait_approval approved/rejected/expired;
- wait_event;
- timeout/cancel;
- worker crash;
- crash após write antes de checkpoint;
- concurrent resume;
- duplicate event;
- policy/permission change durante wait;
- budget/loop exhaustion;
- version compatibility;
- no duplicate write.

### Task

- criação a partir de workflow;
- progress reflete estado real;
- reload/restart;
- cancel;
- result/evidence refs consistentes.

### Case/Evidence Board

- lifecycle;
- accepted/contested/missing/superseded evidence;
- reabertura auditada;
- usuário removido perde acesso;
- source entity permission continua necessária;
- Case não promove Experience automaticamente.

### Room

- participants/messages/files;
- room summary grounded;
- injection não altera policy;
- membership não concede source entity access;
- correlation Case↔Room.

### Inbox

- pending decision aparece;
- item resolvido muda de estado;
- dedupe;
- links válidos;
- entity permission revogada sanitiza item;
- leitura não dispara write.

## 8. Gate C6 — Proactivity/Ecosystem/Learning

### Watch OBSERVE/ADVISE

Positive:
- evento válido casa condição;
- ADVISE grounded;
- event retoma workflow correto.

Negative:
- duplicate event;
- wrong subject/entity;
- permission revogada;
- condition inválida;
- hostile payload;
- expired/disabled watch;
- ACT permanece bloqueado sem autonomy policy.

### AI-ready onboarding

- unknown app;
- unknown iframe;
- unknown expertise pack;
- entity/deep-link/context contract;
- no central hardcode;
- readiness scanner baseado em evidence real.

### Organizational Knowledge

- owner/version/source/provenance;
- DecisionRecord sem CoT;
- Experience promotion exige review;
- PII não promovida indevidamente;
- deprecated pattern não vira atual;
- solution pattern passa sibling case;
- feedback não altera production behavior automaticamente.

### Expertise Studio

- draft não entra em produção;
- publish exige schema/evals;
- rollback;
- secret detection;
- admin RBAC;
- endpoint technical catalog proibido em pack/playbook.

## 9. Gate C7 — Optimization/Autonomy/Rollout

### Autonomy/Watch ACT

- L5 OFF por default;
- explicit allowlist;
- limits/budgets;
- Decision Gate quando required;
- policy revocation durante execução;
- kill switch;
- full audit.

### Simulation

- baseline correto;
- assumptions explícitas;
- modelo/cálculo reproduzível;
- unsupported scenario não inventa número;
- simulation não persiste alteração;
- `Apply` é nova Business Action com policy/gate;
- stale baseline invalida quando material.

### Model Router

- FAST/STANDARD/DEEP/MULTIMODAL/LONG_CONTEXT selection conforme compute policy;
- provider unavailable;
- fallback compatível;
- data-policy provider filter;
- latency/cost budget;
- structured output validity;
- baseline vs candidate.

### Legacy cleanup

Residual material deve chegar a zero para:

```text
soft agent handoff
agent-required operational tool gate
unmigrated department agent routing
fallback sem exit criteria
```

### Rollout

- cohort/canary;
- rollback;
- feature flags com owner/exit criteria;
- final R1–R11;
- accessibility;
- incident/metric review.

## 10. Injection/safety transversal

Testar em todas as fases aplicáveis:

- user prompt injection;
- tool result injection;
- RAG injection;
- API payload injection;
- Workspace Context injection;
- iframe injection;
- Expertise Pack malicious content;
- Playbook malicious instruction;
- PDF/image injection;
- event payload injection;
- room message/file injection.

Dados permanecem dados; não alteram system/policy/permissions.

## 11. Surfaces

Paridade material entre:

```text
send
stream
simulate/admin preview
Portal side panel
full page
MFE contextual entry
iframe integrated entry
Task/Case/Inbox surfaces quando existentes
```

Diferença permitida é transporte/UX, não policy/routing/outcome.

## 12. Anchor scenario final

```text
reclamação cliente
→ Case
→ Business Graph identifica produto/OP/material/fornecedor
→ desenho multimodal
→ Evidence Board
→ Engineering + Quality expertise
→ 8D playbook
→ Task/Durable Workflow
→ wait_event nova revisão
→ Watch
→ Inbox
→ reanálise
→ Decision Gate
→ Business Action
→ Outcome/Evidence/Audit
→ candidate Experience (não auto-published)
```

O fluxo deve sobreviver a reload/restart e não exigir troca manual de agente.

## 13. Release blockers

```text
foundation duplicada
claim material sem provenance quando fonte deveria existir
Business Graph bypassando RBAC
write sem Decision Gate/policy quando required
Case/Room vazando source data
Watch ACT sem autonomy policy
resume duplicando write
approval antiga autorizando payload novo
simulation apresentada como fato
Experience auto-published
Model Router usando provider incompatível com data policy
unknown app/provider/pack/relation exigindo hardcode
required safety eval FAIL/INCONCLUSIVE
R8 acima do threshold canônico
evidence stale/não reproduzível
```

## 14. Regra final

```text
qualquer REQUIRED = FAIL | INCONCLUSIVE | PENDING | TEST_NOT_RUN | STALE_EVIDENCE
→ fase não concluída
```

Não enfraquecer teste/threshold para fazer candidate passar.