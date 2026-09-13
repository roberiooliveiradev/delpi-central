# Minha DELPI Copilot — Event-Driven Autonomous Operations e Automation & Execution Hub

**Status:** thematic architecture/product/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**External sources:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Teams:** [`56-microsoft-teams-integration.md`](./56-microsoft-teams-integration.md)

## 1. Decisão de produto

O Minha DELPI Copilot não deve ser somente uma interface reativa de `pergunta → RAG → resposta`.

O target é uma camada de **Continuous Operational Intelligence** capaz de observar sinais autorizados da empresa, contextualizar o que está acontecendo, decidir dentro de policies explícitas, coordenar execução e verificar o resultado.

Fluxo canônico:

```text
EVENT / SIGNAL
→ OBSERVE
→ CONTEXTUALIZE
→ DECIDE
→ ACT / PREPARE
→ VERIFY OUTCOME
→ NOTIFY
→ LEARN CANDIDATE
```

O usuário continua sendo uma fonte de intenção, mas não é a única fonte de disparo.

Eventos podem vir, conforme contratos reais, de:

```text
Domain APIs
ERP / TOTVS
MES / produção
qualidade
manutenção
estoque / logística
Core / Portal
Teams / Outlook / Gmail / WhatsApp Business
Interaction Rooms
Watch timers/schedules
IoT / telemetry approved read paths
RPA/automation outcomes
```

## 2. Separação fundamental: inteligência versus execução

O desenho recomendado separa:

```text
MINHA DELPI COPILOT
= inteligência, contexto, planejamento, policy, decisão e orquestração

AUTOMATION & EXECUTION HUB
= execução operacional por executors governados

DOMAIN APIs
= business authority e validação final das regras do domínio

EVENT / SIGNAL PLANE
= percepção de mudanças e fatos observáveis

HUMAN WORK
= aprovação, exceção, responsabilidade e tarefas quando exigidas
```

O Hub não cria uma segunda inteligência. O Copilot não implementa clicks/seletores/telas de RPA no planner.

## 3. Não construir apenas um “Hub de RPAs”

RPA é apenas um executor possível.

Nome conceitual recomendado:

> **Minha DELPI Automation & Execution Hub**

Executor preference:

```text
1. API oficial / Domain Action
2. integração/evento nativo com write contract suportado
3. função/script determinístico governado
4. RPA
5. computer-use/UI automation governada
6. Human Task
```

RPA é preferido para legado sem contrato melhor, não como primeiro mecanismo quando uma API está disponível.

## 4. Executor contract

O Copilot trabalha com capability semântica, não com detalhes de implementação.

Exemplo:

```text
billing.invoice.issue
```

Input conceitual:

```text
orderRef
companyRef
invoiceContextRef
policyContext
correlationContext
```

O Automation & Execution Hub resolve o executor adequado:

```text
billing.invoice.issue
→ API executor
```

ou, se o legado comprovadamente exigir:

```text
billing.invoice.issue
→ RPA executor
```

Proibido no planner:

```text
click(x, y)
wait(2)
type(...)
selector específico de ERP
```

Esses detalhes pertencem exclusivamente ao executor/adaptor concreto.

## 5. Tipos de executor alvo

O Hub deve suportar progressivamente, conforme C0/C5 provarem necessidade:

```text
HTTP/API Executor
Function/Script Executor
RPA Executor
Computer-Use Executor
Notification Executor
Human Task Executor
```

`Workflow` não é outro executor concorrente: Durable Workflow orquestra capabilities/executors canônicos.

## 6. Event / Signal Plane

O Copilot deve consumir eventos reais quando owners os disponibilizam.

Fluxo:

```text
source event
→ source adapter validates/authenticates
→ EventEnvelope
→ dedupe/correlation
→ event classification/routing
→ Watch / Workflow / decision use case
```

Não criar event bus novo por suposição. C0 inventaria infrastructure/owners existentes e decide `REUSE | EXTEND | ADAPTER | CREATE_REQUIRED`.

Quando um source não oferece evento, polling/scheduler pode ser usado somente como fallback governado, com intervalos, custo, freshness e dedupe explícitos.

## 7. Continuous Operational Intelligence

O Copilot deve conseguir avaliar continuamente condições explicitamente registradas, por exemplo:

```text
pedido pronto para faturar
máquina parada além do threshold
apontamento improvável
estoque crítico
fornecedor atrasado
OP parada aguardando material
qualidade desviando do padrão
prazo/approval expirando
resposta externa recebida
```

Isso se materializa sobre `Watch`, `EventEnvelope`, Domain reads, Business Graph, Policy, Decision Gate e Durable Workflow — não em um engine paralelo de automação.

## 8. Três velocidades de decisão

Nem todo evento deve chamar um LLM.

### 8.1 FAST PATH

Para condições determinísticas, de baixa ambiguidade e latência mínima:

```text
event
→ deterministic rule/policy/state machine
→ governed action or escalation
```

Safety-critical machine protection continua no owner industrial/safety PLC e nunca depende do Copilot.

### 8.2 OPERATIONAL PATH

Para decisões estruturadas de segundos:

```text
event
→ bounded context reads
→ deterministic rules/policies
→ optional classifier/small model
→ action/preparation
```

### 8.3 REASONING PATH

Para investigação complexa:

```text
event/user goal
→ Business Graph
→ APIs
→ documents/external sources
→ Expertise/Playbook
→ LLM reasoning
→ structured decision candidate
→ Policy/Decision Gate
```

O Copilot escolhe o menor caminho suficiente para o problema, respeitando policy e quality thresholds.

## 9. Decision Intelligence: deterministic first where material

Uma decisão operacional crítica não pode depender apenas da opinião textual do modelo.

Exemplo de readiness para faturamento:

```text
READY_TO_INVOICE =
  order_released
  AND shipment_ready
  AND customer_not_blocked
  AND fiscal_preconditions_valid
  AND required_documents_present
  AND no_blocking_occurrence
```

A IA pode investigar inconsistência, interpretar documento, explicar conflito e recomendar resolução; a business readiness final usa facts/rules/authorities verificáveis.

## 10. Exemplo — faturamento automático

```text
order/shipment event
→ Watch
→ read order/customer/shipment/fiscal context
→ deterministic readiness policy
→ READY_TO_INVOICE?
     ├─ NO  → Evidence + exception/inbox
     └─ YES → AutonomyPolicy
                 ├─ PREPARE/CONFIRM → Decision Gate
                 └─ ACT allowed     → billing.invoice.issue
                                         ↓
                                   Automation Hub
                                   API or RPA executor
                                         ↓
                                   verify Outcome
                                         ↓
                             Evidence/Audit/Notification
```

Notificações podem usar Minha DELPI, email, Teams, WhatsApp Business ou outros connectors autorizados.

Nunca narrar `faturado com sucesso` sem verified Outcome.

## 11. Exemplo — validação de apontamento

```text
production report event
→ load OP/operation/machine/standard cycle/shift/stoppages/scrap
→ deterministic plausibility calculations
→ anomaly threshold/policy
→ Evidence
→ ACCEPT | ASK_CONFIRMATION | BLOCK_AND_REVIEW
```

Exemplo:

```text
available_time = 60 min
standard_cycle = 10 s
reported_qty = 500
expected theoretical max ≈ 360
```

Resultado correto:

```text
POSSIBLE_INCONSISTENCY
```

Não inferir automaticamente fraude, intenção ou qualidade do trabalhador.

## 12. Exemplo — máquina parada / manutenção

```text
approved machine/MES event
→ machine.status = DOWN
→ correlate alarm/history/last maintenance/affected OP
→ classify maintenance need
→ select governed maintenance capability
→ create maintenance occurrence/task
→ route to eligible technician/team
→ notify
→ Watch acknowledgement/SLA
→ escalate if needed
```

O Copilot pode chamar manutenção; não substitui interlocks nem envia comando físico arbitrário para a máquina.

## 13. Autonomia por capability e contexto

Não existe um único `Copilot = L4` global.

Autonomia é resolvida por:

```text
capability
+ actor/user/service identity
+ source/event trust
+ business context
+ risk/sensitivity
+ financial/material limits
+ environment
+ policy
+ reversibility
```

Exemplo conceitual:

```text
inventory.read                  → L5 candidate
Task.create                     → L5 candidate
maintenance.request.create      → L4/L5 candidate
internal.notification.send      → L4/L5 candidate
billing.invoice.issue           → L3/L4 candidate
payment.approve                 → L1/L2 candidate
payroll.modify                  → L1 candidate
physical machine actuation      → outside enterprise-autonomy gate by default
```

Níveis finais são policy/configuration decisions, não hardcode do planner.

## 14. Autonomy ladder

Usar semanticamente:

```text
L0 — explain only
L1 — observe/analyze
L2 — advise
L3 — prepare
L4 — execute after required governance
L5 — execute autonomously inside explicit allowlist/policy/budgets
```

L5 permanece OFF por default e é habilitado por capability/escopo específico.

## 15. Watch modes

Evolução recomendada:

```text
OBSERVE
→ detect/record

ADVISE
→ detect/analyze/notify

PREPARE
→ prepare action/draft/work plan

ACT
→ execute only under C7 autonomy gate
```

`PREPARE` deve ser formalmente separado de `ACT` para evitar que raciocínio/evento vire write implicitamente.

## 16. Automation registration / catalog

Cada automation/executor mapping deve possuir contrato versionado, no mínimo:

```text
automationId
version
capabilityRef
executorType
environment
inputSchema
outputSchema
preconditions
postconditions/idempotency semantics
timeout
retryPolicyRef
worker/queue requirements?
owner
status
```

Opcional conforme executor:

```text
runbookRef
artifact/image/version
credentialRef
selector/package version
```

Credenciais nunca ficam no prompt/planner.

## 17. Execution state

Uma execução precisa ser rastreável:

```text
executionId
correlationContext
capabilityRef
executorRef/version
workflowStepRef?
triggerEventRef?
status
startedAt/endedAt
attempt
inputHash
resultRef/errorCode
outcomeVerificationRef?
```

Estados candidatos:

```text
QUEUED
→ RUNNING
→ SUCCEEDED | FAILED | AMBIGUOUS | CANCELLED | TIMED_OUT
```

`SUCCEEDED` técnico não equivale automaticamente a business outcome correto; postcondition/outcome verification pode ser necessária.

## 18. RPA worker/queue model

Se RPA entrar no scope:

- worker pool e capabilities explícitos;
- queue/priority/concurrency;
- environment separation;
- worker heartbeat/health;
- lease/lock para evitar dupla execução;
- timeout/cancel;
- retry classificado;
- screenshot/artifact Evidence apenas quando permitido;
- secrets via protected credential injection;
- RPA package/version traceable;
- no desktop session reuse across unauthorized users;
- observability per execution.

Não assumir ferramenta RPA específica em C0.

## 19. Computer Use boundary

Computer-use/UI automation é fallback avançado, não substituto automático de API/RPA determinístico.

Requer:

```text
sandbox/session isolation
application/domain allowlist
credential isolation
screen/output data classification
bounded actions
same Policy/Decision semantics
human takeover/stop
full audit
```

Nunca permitir navegação irrestrita pela rede corporativa apenas porque o modelo consegue operar uma tela.

## 20. Outcome verification

Toda ação material precisa responder:

```text
EXECUTED?
AND
EXPECTED BUSINESS POSTCONDITION OBSERVED?
```

Exemplos:

```text
invoice call returned 200
!= invoice issued and persisted correctly

RPA clicked Save
!= transaction committed

message send request accepted
!= message confirmed by provider
```

Preferir verificação via owner API/event/record authoritative.

## 21. Notification orchestration

Notification é consequência governada do outcome, não prova do outcome.

Channels podem incluir:

```text
Minha DELPI notification/inbox
email
Teams
WhatsApp Business
Interaction Room
other approved connector
```

Rules definem recipients, severity, dedupe, escalation, quiet hours/urgency quando aplicável.

## 22. Human-in-the-loop e exceções

Quando policy, ambiguidade ou risco exigirem:

```text
Copilot
→ Task/Inbox/Decision
→ responsible human
→ decision/correction
→ resume same Workflow
```

Não criar workflow paralelo para “manual exception”.

## 23. Learning

Execution history pode gerar candidato de melhoria:

```text
Event + Context + Decision + Action + Outcome
→ Evidence
→ candidate pattern/optimization
→ review/eval
→ Policy/Playbook/Automation update
```

Nunca:

```text
one successful run
→ autonomous permanent policy change
```

## 24. Architecture target

```text
                          SOURCES
        Domain APIs / ERP / MES / External / IoT
                             │
                             ▼
                      EVENT / SIGNAL PLANE
                             │
                             ▼
                     Minha DELPI Copilot
        ┌──────────────────────────────────────┐
        │ Context / Graph / Evidence           │
        │ Deterministic Policies / Rules       │
        │ Expertise / Knowledge                │
        │ Planner / Reasoning                  │
        │ Decision Gate / Autonomy Policy      │
        └──────────────────┬───────────────────┘
                           ▼
                    Durable Workflow
                           │
                 ┌─────────┼─────────┐
                 ▼         ▼         ▼
            Domain API  Automation  Human Task
                         & Execution
                            Hub
                 ┌────────┼─────────┐
                 ▼        ▼         ▼
               RPA     Function  Computer Use
                 │
                 ▼
             legacy apps
                 │
                 └──────────────┐
                                ▼
                         Outcome Verification
                                │
                   Evidence / Audit / Notification
                                │
                         Learning Candidate
```

## 25. Bounded contexts / ownership

Copilot owns:

- event correlation semantics used by its Watches/Workflows;
- decision/orchestration;
- autonomy/policy application;
- execution request lifecycle and correlation when Hub is Copilot-owned;
- outcome verification orchestration;
- automation capability projection;
- automation admin/observability semantics.

Automation & Execution Hub may be a Copilot-owned bounded context/service/module or neutral platform service only after C0 ownership analysis. Do not split a new microservice merely because it has the word `Hub`.

Domain APIs remain business authorities. External providers remain their own authorities. OT safety remains external authority.

## 26. Architecture patterns

Preferred:

```text
Event Adapter → EventEnvelope
Watch/Condition → Policy/Specification
Decision → structured Policy + optional reasoning
Execution request → Command/Use Case
Executor → Port + Adapter
Automation mapping → capability registry/projection backed by contracts
Execution lifecycle → State Machine
Durable orchestration → existing Workflow runtime
Reliable state/event → Outbox where atomicity is required
Retry → explicit idempotency/resilience policy
Outcome → verifier adapter + OutcomeRef/EvidenceRef
```

Avoid god `AutomationService` / `RpaManager` / `AgentOrchestrator` with mixed responsibilities.

## 27. Security / safety

Required:

- Core/domain authorization revalidation before material action;
- service identities explicit for background actions;
- capability/event source allowlists;
- secrets outside prompt/LLM/log/MFE;
- no event payload can modify policy;
- no blind retry of material writes;
- no duplicate execution after workflow resume;
- kill switch per automation/capability/executor/provider;
- human emergency stop;
- complete audit/correlation;
- RPA/computer-use screenshots/data follow classification/retention;
- no biometric/person-analysis permission bypass;
- no free-form LLM → PLC/CNC/robot/machine.

## 28. Observability

Minimum metrics:

```text
events received/validated/deduped
watch detections
decision path: FAST|OPERATIONAL|REASONING
decision latency
prepared vs executed actions
execution success/failure/ambiguous/cancelled
queue latency
worker availability/utilization when applicable
retry/idempotency conflicts
outcome verification failures
human intervention rate
notification delivery status
time-to-resolution
cost per decision/execution when applicable
```

KPIs must distinguish technical execution from verified business outcome.

## 29. Admin UX target

A futura administração pode apresentar:

```text
AUTOMATION & EXECUTION HUB

Automations
- capability
- owner
- executor
- version
- autonomy policy
- status
- success/outcome rate

Executions
- running/queued/failed/ambiguous
- correlation
- Task/Case/Workflow
- evidence/outcome

Workers
- health/capability/environment

Exceptions
- waiting decision
- blocked by policy
- failed/ambiguous outcome
```

Não é requisito de C0/C1; é target de produto posterior.

## 30. Phase mapping

### C0 — Foundation

Inventariar/freeze:

- event sources/buses/webhooks/schedulers/workers existentes;
- RPA tools/platforms/licenses/bots/orchestrators existentes;
- automation scripts/jobs atuais;
- service accounts/credential owners;
- queues/workers/desktop execution infrastructure;
- existing process/rule engines;
- polling/scheduler patterns;
- business postcondition/outcome sources;
- notification channels;
- automation ownership/governance;
- executor contracts/idempotency/security;
- service/background identity model;
- kill switches/emergency stop;
- OT boundary.

### C1 — Standalone bootstrap

Nenhum RPA Hub runtime ainda. Apenas preparar configuration/health/contracts necessários se C0 freeze exigir.

### C2 — Context/commands

Operational context e Platform Commands; nenhuma automation authority nova.

### C3 — Intelligence foundation

- event/decision understanding contracts;
- FAST/OPERATIONAL/REASONING routing policy foundation;
- deterministic Policy/Specification patterns;
- no autonomous material ACT.

### C4 — Reads/context

- business/external reads;
- Graph/Evidence;
- readiness/anomaly calculations;
- no write side effect.

### C5 — Governed execution foundation

- executor ports/adapters;
- Automation Capability Registry/Projection;
- API/function/RPA executor support only as prioritized;
- execution lifecycle/state;
- outcome verification;
- idempotency/resilience;
- human-confirmed/governed writes.

### C6 — Operational Watches + Automation product

- event-driven Watch OBSERVE/ADVISE/PREPARE;
- automation admin/observability;
- Tasks/Cases/Inbox/exceptions;
- notifications/escalations;
- RPA worker/queue visibility if RPA is in scope;
- learning candidates.

### C7 — Autonomous Operations

- selected Watch ACT;
- capability-scoped L5 under explicit allowlist/budgets;
- proactive autonomous workflows;
- automation kill switches;
- advanced computer-use only where justified;
- scale/cost/performance;
- OT actuation remains blocked unless separate industrial safety initiative passes its own gate.

## 31. Acceptance outcomes

A arquitetura está correta quando:

```text
Copilot can react to authorized events without a user prompt
not every event invokes an LLM
rules/policies can make deterministic decisions
planner never contains RPA clicks/selectors
API is preferred over RPA where authoritative contract exists
RPA is a replaceable executor behind semantic capability
execution is idempotent/correlated/audited
technical success is verified against business outcome
notifications happen after/with truthful outcome state
autonomy is capability/context/risk scoped
L5 is OFF by default
background actions use explicit service/user authority
Watch PREPARE is distinct from ACT
human exception resumes same durable workflow
learning changes policy only through governance
machine safety is never delegated to free-form Copilot reasoning
```

## 32. Market direction used as benchmark

The design intentionally aligns with current market direction in which AI agents reason/orchestrate while deterministic automation, APIs, RPA and people execute/govern work. Reference classes to revalidate during implementation include:

```text
UiPath Maestro / agentic orchestration
Automation Anywhere agentic process automation
Microsoft Copilot Studio + Power Automate
ServiceNow AI Agent Orchestrator
SAP Joule / agent orchestration
Siemens industrial copilot / shopfloor intelligence
Palantir operational ontology / real-time decision workflows
```

These are benchmark references, not DELPI architecture authorities. Provider/product details must be revalidated when implementation reaches the relevant phase.

## 33. North Star

> **A Minha DELPI evolui de um portal de aplicações para um sistema operacional inteligente da empresa: observa eventos autorizados, entende o contexto operacional, combina regras determinísticas e raciocínio de IA, toma decisões governadas, coordena APIs, automações/RPAs e pessoas, verifica resultados, comunica os envolvidos e transforma resultados em aprendizado governado.**
