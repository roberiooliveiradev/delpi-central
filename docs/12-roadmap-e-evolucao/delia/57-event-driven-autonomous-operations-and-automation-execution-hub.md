# Minha DELPI Copilot — Event-Driven Autonomous Operations e Automation & Execution Hub

**Status:** thematic architecture/product/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**External sources:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)

## 1. Decisão de produto

O Minha DELPI Copilot não deve ser somente uma interface reativa de `pergunta → RAG → resposta`.

O target é uma camada de **Continuous Operational Intelligence** capaz de observar sinais autorizados, contextualizar o que está acontecendo, decidir dentro de policies explícitas, coordenar execução, verificar o resultado, comunicar e aprender de forma governada.

```text
EVENT / SIGNAL
→ OBSERVE
→ CONTEXTUALIZE
→ DECIDE
→ PREPARE / ACT
→ VERIFY OUTCOME
→ NOTIFY
→ LEARN CANDIDATE
```

O usuário é uma fonte de intenção, mas não é a única fonte de disparo.

## 2. Inteligência versus execução

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

O Hub não cria uma segunda inteligência, segundo planner ou segundo Workflow engine.

## 3. Não construir apenas um “Hub de RPAs”

RPA é apenas um executor possível.

Nome conceitual recomendado:

> **Minha DELPI Automation & Execution Hub**

Executor preference:

```text
1. API oficial / Domain Action
2. integração nativa suportada
3. função/script determinístico governado
4. RPA
5. computer-use/UI automation governada
6. Human Task
```

RPA é preferido para legado sem contrato melhor, não como primeiro mecanismo quando uma API autoritativa está disponível.

## 4. Semantic capability contract

O Copilot trabalha com capability semântica, não com detalhes de implementação.

Exemplos:

```text
billing.invoice.issue
maintenance.request.create
production.report.validate
communication.email.send
inventory.read
```

O Hub resolve:

```text
capability
→ executor mapping/version
→ executor contract
```

Proibido no planner:

```text
click(x, y)
wait(2)
type(...)
CSS/XPath selector
screen coordinate
RPA package internals
```

Uma capability pode migrar de RPA para API sem patch no planner/workflow.

## 5. Tipos de executor alvo

Progressivamente, conforme C0/C5 provarem necessidade:

```text
HTTP/API Executor
Function/Script Executor
RPA Executor
Computer-Use Executor
Notification Executor
Human Task Executor
```

Durable Workflow continua sendo o orquestrador canônico das capabilities/executors.

## 6. Event / Signal Plane

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
IoT / approved telemetry read paths
RPA/automation outcomes
```

Fluxo:

```text
source event
→ source adapter validates/authenticates
→ EventEnvelope
→ dedupe/order/correlation
→ Watch / Workflow / Decision use case
```

Não criar event bus novo por suposição. Polling/scheduler é apenas fallback bounded quando não existe evento suportado.

Event payload nunca concede permission ou ACT authority.

## 7. Continuous Operational Intelligence

Exemplos de condições:

```text
pedido pronto para faturar
máquina parada além do threshold
apontamento improvável
estoque crítico
fornecedor atrasado
OP parada aguardando material
qualidade desviando
prazo/approval expirando
resposta externa recebida
```

Isso se materializa sobre `Watch`, `EventEnvelope`, Domain reads, Business Graph, Policy, Decision Gate e Durable Workflow — não em engine paralelo de agentes.

## 8. Três velocidades de decisão

Nem todo evento chama LLM.

### FAST

```text
event
→ deterministic Policy/Specification/State Machine
→ finding/action candidate
```

### OPERATIONAL

```text
event
→ bounded context reads
→ deterministic rules/policies
→ optional classifier/small model
→ decision candidate
```

### REASONING

```text
event/user goal
→ Business Graph
→ APIs
→ documents/external sources
→ Expertise/Playbook
→ LLM reasoning
→ structured decision candidate
```

O Copilot escolhe o menor caminho suficiente para o problema.

## 9. Deterministic-first para readiness material

Uma decisão operacional crítica não deve depender apenas da opinião textual do modelo quando critérios verificáveis existem.

Exemplo:

```text
READY_TO_INVOICE =
  order_released
  AND shipment_ready
  AND customer_not_blocked
  AND fiscal_preconditions_valid
  AND required_documents_present
  AND no_blocking_occurrence
```

A IA pode investigar inconsistências, interpretar documentos e explicar conflitos; readiness formal usa facts/rules/authorities verificáveis.

## 10. Exemplo — faturamento automático

```text
order/shipment event
→ Watch
→ read order/customer/shipment/fiscal context
→ deterministic readiness policy
→ READY_TO_INVOICE?
     ├─ NO  → Evidence + exception/Inbox
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

Uma anomalia é `POSSIBLE_INCONSISTENCY`, não inferência automática de fraude/intenção do trabalhador.

## 12. Exemplo — máquina parada / manutenção

```text
approved machine/MES event
→ machine.status = DOWN
→ correlate alarm/history/last maintenance/affected OP
→ classify maintenance need
→ maintenance.request.create
→ route to eligible technician/team
→ notify
→ Watch acknowledgement/SLA
→ escalate if needed
```

O Copilot pode chamar manutenção; não substitui interlocks nem envia comando físico arbitrário para a máquina.

## 13. Autonomia por capability/contexto

Não existe um único `Copilot = L4/L5` global.

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

```text
L0 — explain only
L1 — observe/analyze
L2 — advise
L3 — prepare
L4 — execute after required governance
L5 — execute autonomously inside explicit allowlist/policy/budgets
```

L5 permanece OFF por default.

## 15. Watch modes

```text
OBSERVE → detect/record
ADVISE  → detect/analyze/notify
PREPARE → prepare action/draft/work plan without side effect
ACT     → execute only under C7 autonomy gate
```

`PREPARE != ACT`.

## 16. Automation registration / catalog

Cada mapping deve ser versionado:

```text
automationId
version
capabilityRef
executorType
executorRef
environment
inputSchema
outputSchema
preconditions
postconditions
idempotency semantics
timeout/retry policy
owner
status
```

Credenciais nunca ficam no prompt/planner.

## 17. AutomationExecution state

```text
executionId
correlationContext
capabilityRef
executorRef/version
workflowStepRef?
triggerEventRef?
actorRef
status
startedAt/endedAt
attempt
inputHash
idempotencyKey?
resultRef/errorCode
outcomeVerificationRef?
```

Lifecycle:

```text
QUEUED
→ RUNNING
→ SUCCEEDED | FAILED | AMBIGUOUS | CANCELLED | TIMED_OUT
```

`SUCCEEDED` técnico não equivale automaticamente a business outcome correto.

## 18. RPA worker/queue model

Se RPA entrar no scope:

- worker pool/capabilities explícitos;
- queue/priority/concurrency;
- worker heartbeat/health;
- lease/lock contra dupla execução;
- environment separation;
- package/version traceability;
- timeout/cancel/retry eligibility;
- screenshot/artifact retention/classification;
- protected credential injection;
- desktop/session isolation;
- execution observability.

Não assumir ferramenta RPA específica em C0.

## 19. Computer Use boundary

Computer-use/UI automation é fallback avançado, não substituto automático de API/RPA determinístico.

Requer sandbox/session isolation, app/domain/network allowlist, credential isolation, bounded actions, same Policy/Decision semantics, human takeover/stop e full audit.

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
!= final provider outcome when async
```

Preferir owner API/event/record autoritativo para verificação.

## 21. Notification orchestration

Notification é consequência governada do outcome, não prova do outcome.

Canais podem incluir Minha DELPI, email, Teams, WhatsApp Business, Interaction Room e outros connectors aprovados.

Recipients, severity, dedupe, escalation/SLA e acknowledgement seguem policy.

## 22. Human-in-the-loop

```text
Workflow
→ Task/Inbox/Decision
→ responsible human
→ decision/correction
→ resume same Workflow
```

Não criar workflow paralelo para manual exception.

## 23. Learning

```text
Event + Context + Decision + Action + Outcome
→ Evidence
→ candidate pattern/optimization
→ review/eval
→ Policy/Playbook/Automation update
```

Nunca `one successful run → autonomous permanent policy change`.

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

Copilot owns event-correlation semantics used by Watches/Workflows, decision/orchestration, autonomy-policy application, outcome-verification orchestration and automation capability projection.

Automation & Execution Hub may be Copilot-owned bounded module or neutral platform service only after C0 ownership analysis. `Hub` does not imply microservice.

Domain APIs remain business authorities. External providers remain source authorities. OT safety remains external authority.

## 26. Architecture patterns

Preferred:

```text
Event Adapter → EventEnvelope
Watch/Condition → Policy/Specification
Decision → structured Policy + optional reasoning
Execution request → Command/Use Case
Executor → Port + Adapter
Automation mapping → capability registry/projection
Execution lifecycle → State Machine
Durable orchestration → canonical Workflow runtime
Retry → explicit idempotency/resilience
Outcome → verifier adapter + OutcomeRef/EvidenceRef
```

Avoid god `AutomationService`, `RpaManager` or `AgentOrchestrator`.

## 27. Security / safety

Required:

- Core/domain authorization revalidation before material action;
- explicit service/user identity for background actions;
- event source/capability allowlists;
- secrets outside prompt/LLM/log/MFE;
- no event payload policy mutation;
- no blind retry of ambiguous writes;
- no duplicate execution after resume;
- kill switch per automation/capability/executor/provider;
- human emergency stop;
- full audit/correlation;
- RPA/computer-use artifacts follow classification/retention;
- no biometric/person-analysis permission bypass;
- no free-form LLM/RPA/computer-use → PLC/CNC/robot/machine.

## 28. Observability

Minimum metrics:

```text
events received/validated/deduped
watch detections
decision path FAST|OPERATIONAL|REASONING
decision latency
prepared vs executed actions
execution success/failure/ambiguous/cancelled
queue latency
worker availability/utilization when applicable
retry/idempotency conflicts
outcome verification failures
human intervention rate
notification delivery/acknowledgement
time-to-resolution
cost per decision/execution when applicable
```

KPIs distinguish technical execution from verified business outcome.

## 29. Admin UX target

Future admin may expose:

```text
AUTOMATION & EXECUTION HUB

Automations
- capability / owner / executor / version / autonomy policy / status

Executions
- running / queued / failed / ambiguous / outcome

Workers
- health / capability / environment

Exceptions
- waiting decision / policy blocked / failed / ambiguous
```

Não é requisito C0/C1.

## 30. Phase mapping

### C0
Inventariar/freeze events, RPA/tools, scripts/jobs, queues/workers, service identities, credential owners, outcome sources, notification channels, executor/idempotency/security, kill switches e OT boundary.

### C1
Standalone bootstrap. Nenhum Automation Hub/RPA runtime ainda.

### C2
Context/commands only.

### C3
Event/Decision contracts, FAST/OPERATIONAL/REASONING and deterministic Policy foundation. No autonomous material ACT.

### C4
Read-only readiness/anomaly calculations using business/external reads + Graph/Evidence.

### C5
Executor ports/adapters, Automation Capability mapping, execution lifecycle, outcome verification, idempotency/resilience and governed writes.

### C6
Watch OBSERVE/ADVISE/PREPARE, Automation Hub admin/observability, Tasks/Cases/Inbox/exceptions, notifications/escalations and learning candidates.

### C7
Selected Watch ACT, capability-scoped L5, proactive autonomous workflows, kill switches and advanced computer-use only where justified. OT actuation remains blocked unless separate industrial safety initiative passes its own gate.

## 31. Acceptance outcomes

```text
Copilot reacts to authorized events without user prompt
not every event invokes an LLM
rules/policies can make deterministic decisions
planner never contains RPA clicks/selectors
API preferred over RPA where authoritative contract exists
RPA is replaceable executor behind semantic capability
execution is idempotent/correlated/audited
technical success is verified against business outcome
notifications use truthful outcome state
autonomy is capability/context/risk scoped
L5 is OFF by default
background actions use explicit service/user authority
Watch PREPARE is distinct from ACT
human exception resumes same durable workflow
learning changes policy only through governance
machine safety is never delegated to free-form Copilot reasoning
```

## 32. Market benchmark direction

Reference classes to revalidate during implementation:

```text
UiPath Maestro / agentic orchestration
Automation Anywhere agentic process automation
Microsoft Copilot Studio + Power Automate
ServiceNow AI Agent Orchestrator
SAP Joule / agent orchestration
Siemens industrial copilot / shopfloor intelligence
Palantir operational ontology / real-time decision workflows
```

These are benchmark references, not DELPI architecture authorities.

## 33. North Star

> **A Minha DELPI evolui de um portal de aplicações para um sistema operacional inteligente da empresa: observa eventos autorizados, entende o contexto operacional, combina regras determinísticas e raciocínio de IA, toma decisões governadas, coordena APIs, automações/RPAs e pessoas, verifica resultados, comunica os envolvidos e transforma resultados em aprendizado governado.**
