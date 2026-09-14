# DÉLIA — Event-Driven Operations e Automation Hub

**Status:** `TARGET` — thematic architecture/product/security spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Architecture/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**External sources:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)

## 1. Decisão de produto

A DÉLIA não é apenas `pergunta → RAG → resposta`.

O target é Continuous Operational Intelligence capaz de observar sinais autorizados, contextualizar, decidir sob policies, PREPARE/ACT quando permitido, verificar outcome, comunicar e gerar learning candidates.

```text
EVENT / SIGNAL
→ OBSERVE
→ CONTEXTUALIZE
→ DECIDE
→ PREPARE / ACT
→ VERIFY OUTCOME
→ NOTIFY
→ LEARNING CANDIDATE
```

Nem todo evento usa LLM.

## 2. Inteligência versus execução

```text
DÉLIA
= inteligência + contexto + Evidence + Policy + Decision + Work/orquestração + Outcome coordination

AUTOMATION HUB
= execução técnica governada

DOMAIN APIs
= dados/regras/business authority final

KEYCLOAK
= identidade/SSO

CORE
= apps/rotas/RBAC/governança

OT/SAFETY
= máquina e segurança industrial
```

Automation Hub **não** é segundo planner, segundo Policy engine, segunda business authority ou owner do Work da DÉLIA.

## 3. Automation Hub não é “Hub de RPA”

RPA é apenas um executor possível.

Preference:

```text
1. API oficial / Domain Action
2. integração nativa suportada
3. função/script determinístico governado
4. RPA
5. computer-use governado
6. Human Task
```

O nome físico, deployment model e owner técnico do Automation Hub são `TO_INVENTORY` até C0 provar a fonte canônica. A documentação alvo não autoriza criar um novo Hub se já existir owner/plataforma equivalente.

## 4. Semantic capability contract

A DÉLIA trabalha com capability semântica, não com detalhes de execução.

Exemplos candidatos:

```text
billing.invoice.issue
maintenance.request.create
production.report.validate
communication.email.send
inventory.read
```

O executor owner resolve:

```text
semantic capability
→ approved execution contract/mapping
→ technical executor
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

Migração RPA→API não deve exigir patch no planner.

## 5. Tipos de executor alvo

Possíveis executor families, somente se C0/C5 comprovarem necessidade e owner:

```text
HTTP/API
native integration
function/script
RPA
computer-use
notification
Human Task
```

DÉLIA Work coordena semantic steps; technical execution lifecycle pertence ao Automation Hub/provider/domain executor owner apropriado.

## 6. Event / Signal Plane

Eventos podem vir de Domain APIs, ERP/MES, qualidade, manutenção, estoque/logística, Core/Portal, external providers, timers/schedules, approved telemetry e executor outcomes — somente quando contrato real existir.

```text
source event
→ source adapter validates/authenticates
→ EventEnvelope
→ dedupe/order/correlation
→ DÉLIA Watch/Work/Decision evaluation
```

Não criar event bus novo por suposição. Polling/scheduler é bounded fallback quando necessário.

Event payload nunca concede permission, Policy change ou ACT authority.

## 7. Continuous Operational Intelligence

Condições como pedido pronto, máquina parada, estoque crítico, fornecedor atrasado, OP aguardando material, desvio de qualidade, approval expirando ou resposta externa recebida podem gerar avaliação somente após owner/source/event contracts serem comprovados.

Não criar engine paralelo de agentes.

## 8. Três velocidades de decisão

### FAST

```text
event
→ deterministic Policy/Specification/State Machine
→ finding/action candidate
```

### OPERATIONAL

```text
event
→ bounded structured context
→ deterministic rules/policies
→ optional approved small model
→ decision candidate
```

### REASONING

```text
event/user goal
→ Graph/APIs/Knowledge/docs/external sources
→ Expertise/Playbook
→ LLM reasoning
→ structured decision candidate
```

Usar o menor caminho suficiente.

## 9. Deterministic-first para readiness material

Critério operacional verificável não deve depender apenas de opinião textual do modelo.

Readiness formal usa facts/rules/authorities verificáveis; IA pode investigar, explicar e estruturar gaps.

## 10. Exemplo — faturamento

Exemplo target, não prova de capability/domain contract existente:

```text
order/shipment signal
→ Watch evaluation
→ authorized domain reads
→ deterministic readiness policy
→ not ready → Evidence + exception
→ ready → autonomy/policy evaluation
          → PREPARE or L4 ACT
          → live AuthZ + Decision when required
          → approved executor/domain action
          → authoritative postcondition verification
          → Outcome/Evidence/Audit/Notification
```

Nunca narrar sucesso apenas por retorno técnico.

## 11. Exemplo — apontamento

```text
production report signal
→ authorized context
→ deterministic plausibility calculation
→ anomaly policy
→ Evidence
→ ACCEPT | ASK_CONFIRMATION | BLOCK_AND_REVIEW
```

Anomalia não implica fraude, intenção ou valor profissional.

## 12. Exemplo — manutenção

```text
approved machine/MES signal
→ authorized context
→ deterministic/approved classification
→ PREPARE maintenance request
→ governed ACT if explicitly authorized
→ technical execution by approved executor/domain API
→ verify Outcome
```

DÉLIA não substitui interlocks e não envia comando físico arbitrário a máquina.

## 13. Autonomia por capability/contexto

Autonomia depende de:

```text
capability
+ actor/service identity
+ source/event trust
+ business context
+ risk/sensitivity
+ materiality/limits
+ environment
+ reversibility
+ Policy
```

Níveis são policy decisions; não hardcode do planner.

## 14. Autonomy ladder

```text
L0 explain
L1 observe
L2 advise
L3 prepare
L4 governed execute
L5 allowlisted autonomous execute within explicit limits
```

L4 pode existir em C5 para capability explicitamente autorizada. L5 entra apenas em C7 e permanece OFF por default.

## 15. Watch modes

```text
OBSERVE → detect/record
ADVISE  → analyze/notify
PREPARE → prepare draft/action/work plan; no side effect
ACT     → governed execution mode; C5-capable through explicit authorized flow
```

Em **C6**, Watch por default permanece `OBSERVE|ADVISE|PREPARE` e **não dispara ACT autonomamente**. Selected Watch autonomous ACT é C7/L5.

```text
PREPARE != ACT
C5 governed ACT != C7 autonomous ACT
```

## 16. Automation capability projection

DÉLIA pode manter uma projeção semântica de capabilities/execution contracts aprovados, sem se tornar registry técnico autoritativo.

Campos candidates:

```text
capabilityRef
executionContractRef
risk/sensitivity
preconditions/postconditions
idempotency semantics
owner/status/version refs
```

Executor package, queue, worker, credentials e technical mapping permanecem no Automation Hub/executor owner.

## 17. Technical execution state

Se houver Automation Hub, o estado técnico de execução pertence ao Hub/executor owner, não ao domain state da DÉLIA.

Exemplo conceitual do executor owner:

```text
executionId
capability/executor refs
status
attempt
inputHash/idempotencyKey
result/error refs
startedAt/endedAt
```

DÉLIA guarda apenas refs/status necessários à Work orchestration, Evidence, Decision e Outcome coordination, evitando duplicar executor truth.

Technical `SUCCEEDED` nunca equivale automaticamente a business Outcome correto.

## 18. RPA worker/queue model

Worker pools, queues, heartbeats, leases, package versions, credentials, screenshots e desktop sessions são responsabilidade do Automation Hub/RPA platform owner.

DÉLIA não cria cópia paralela desses estados.

## 19. Computer-use boundary

Computer-use é fallback avançado, governado e sandboxed. Requer app/domain/network allowlists, credential isolation, bounded actions, live Policy/Decision/AuthZ, audit e human stop/takeover quando aplicável.

## 20. Outcome verification

Toda ação material distingue:

```text
TECHNICAL EXECUTION
!=
VERIFIED BUSINESS OUTCOME
```

DÉLIA coordena verificação usando fonte autoritativa apropriada. Postcondition source deve ser owner/domain/provider evidence, não autoafirmação do executor.

## 21. Notification orchestration

Notification é consequência do state/outcome, nunca prova do outcome. Recipients/severity/dedupe/escalation seguem policy.

## 22. Human-in-the-loop

```text
DÉLIA Work
→ Task/Inbox/Decision/Human Task
→ human action
→ resume same Work
```

Não criar workflow manual paralelo.

## 23. Learning

```text
Event + Context + Decision + Action + Outcome
→ Evidence
→ candidate
→ owner/review
→ eval
→ version
→ publish
```

Nunca `one successful run → production policy change`.

## 24. Architecture target

```text
SOURCES / SIGNALS
        ↓
EventEnvelope + authorized context
        ↓
DÉLIA
Context / Evidence / Policy / Decision / Work
        ↓
PREPARE or ACT intent
        ↓
live AuthZ + Decision Gate when required
        ↓
approved execution contract
        ↓
Automation Hub | Domain API | Provider | Human Task
        ↓
technical result
        ↓
authoritative postcondition source
        ↓
Outcome / Evidence / Audit / Notification
        ↓
Learning Candidate
```

## 25. Bounded contexts / ownership

DÉLIA owns intelligence context, Evidence coordination, Policy/Decision application, Work orchestration, semantic capability use and Outcome coordination.

Automation Hub owns technical execution mechanics and technical execution state when such platform/owner is proven.

Domain APIs remain business authorities. Providers remain external resource authorities. OT/Safety remains physical safety authority.

**Não é permitido decidir que Automation Hub é “Copilot/DÉLIA-owned module” apenas por conveniência documental. C0 deve inventariar o owner real.**

## 26. Architecture patterns

Preferred, se gates justificarem:

```text
Event Adapter → EventEnvelope
Watch/Condition → Policy/Specification
Decision → deterministic Policy + bounded reasoning
Work step → semantic command/use case
Execution → external owner contract
Execution lifecycle → executor-owner State Machine
Outcome → authoritative verifier + Outcome/Evidence
```

Evitar god services e registries paralelos.

## 27. Security / safety

Required:

- live Core/domain authorization before material ACT;
- explicit user/service identity;
- source/capability allowlists;
- secrets outside prompt/LLM/log/MFE;
- event payload cannot mutate policy;
- no blind retry of ambiguous writes;
- idempotency/correlation;
- kill switch/revoke/disable;
- human emergency stop where material;
- no provider/executor metadata permission grant;
- no biometric bypass;
- no free-form LLM/RPA/computer-use → PLC/CNC/robot/machine.

## 28. Observability

DÉLIA observability pode registrar event/decision/work/outcome refs, decision path, prepared vs executed actions, outcome-verification failures e human intervention.

Executor queue/worker/package internals permanecem observabilidade do Hub/executor owner, referenciados quando necessário sem duplicação.

## 29. Admin UX target

Uma futura surface de Automation Hub pode expor technical capabilities/executions/workers/exceptions conforme o owner real. Ela não se torna planner ou business authority.

Não é requisito C0/C1.

## 30. Phase mapping

### C0
Inventariar/freeze events, Automation Hub/RPA/tools/scripts/jobs/queues/workers, service identities, credential owners, execution contracts, outcome sources, notification channels, kill switches e OT boundary.

### C1
Standalone bootstrap; nenhum novo Automation Hub/RPA runtime criado sem C0 proof.

### C2
Context/commands only.

### C3
Event/Decision contracts, FAST/OPERATIONAL/REASONING e deterministic Policy foundation. No material ACT.

### C4
Read-only readiness/anomaly calculations com authorized reads/Evidence.

### C5
Primeiro gate para L4 governed ACT: DÉLIA Work/Decision coordena actions; technical execution usa Automation Hub/domain/provider contract comprovado. Idempotency/audit/Outcome verification obrigatórios conforme capability.

### C6
Watch `OBSERVE|ADVISE|PREPARE`, Hub admin/observability quando owner existir, Tasks/Cases/Inbox/exceptions, notifications/escalations e learning candidates. C5-governed ACT continua disponível somente por explicit authorized flow; Watch não o dispara autonomamente.

### C7
Selected Watch autonomous ACT/L5, capability-scoped autonomous workflows e advanced computer-use sob explicit limits. L5 OFF default. OT actuation permanece bloqueada sem gate industrial separado.

## 31. Acceptance outcomes

Quando implementado, provar:

```text
DÉLIA reacts to authorized events without requiring user prompt
not every event invokes LLM
rules/policies can decide deterministically
planner contains no clicks/selectors
API preferred over RPA when authoritative contract exists
executor is replaceable behind semantic capability
DÉLIA does not duplicate technical executor truth
technical success != verified business Outcome
L4 governed ACT works under C5 gates
C6 Watch has no autonomous ACT
L5/selected autonomous Watch ACT only in C7 and OFF default
background ACT uses explicit authority
learning changes production knowledge/policy only through governance
machine safety never delegated to free-form reasoning
```

Sem evidence obrigatória: `PENDING`/`INCONCLUSIVE`, nunca PASS.

## 32. Benchmark direction

Qualquer comparação de mercado é reference-only e deve ser revalidada com fonte recente quando usada. Benchmark nunca prova owner, capability ou runtime DELPI.

## 33. North Star

> **A DÉLIA observa sinais autorizados, contextualiza, combina políticas determinísticas e raciocínio quando necessário, coordena trabalho governado, delega execução técnica ao owner correto, verifica outcomes em fontes autoritativas, comunica e transforma resultados em learning candidates sem criar autoridade paralela.**

## 34. Recurring Governed Work / scheduling

### 34.1 Decisão de produto

**Recurring Governed Work é capability `TARGET` de primeira classe da DÉLIA.** Um usuário autorizado deve poder definir trabalho recorrente persistente, independente de sessão de chat, por exemplo:

```text
“Todos os dias às 09:00 gere o relatório de produção do dia anterior e envie por email para a diretoria.”
```

Isso não significa que a DÉLIA “lembra de acordar”. O trigger deve ser determinístico e persistente, usando infraestrutura cujo owner físico será provado em C0.

### 34.2 Quatro camadas que não podem ser confundidas

```text
PRODUCT CAPABILITY
= Recurring Governed Work é TARGET

DÉLIA-OWNED DEFINITION
= definição/versionamento/lifecycle do Work recorrente e correlação das ocorrências

PHYSICAL TIMER/SCHEDULER
= plataforma/serviço que materializa o trigger temporal; owner = TO_INVENTORY em C0

TECHNICAL EXECUTION
= Automation Hub | Domain API | Provider | outro executor aprovado conforme capability
```

`TO_INVENTORY` do scheduler físico não rebaixa a capability de produto para “não prevista”.

### 34.3 Lifecycle mínimo

Quando implementado, o usuário/owner autorizado deve conseguir:

```text
CREATE
INSPECT/LIST
PAUSE
RESUME
CANCEL
```

Update/reschedule só entra se contrato explícito preservar versionamento, idempotência e audit; caso contrário, usar cancel + create de nova versão.

Estados candidates:

```text
ACTIVE
PAUSED
CANCELLED
EXPIRED
DISABLED_BY_POLICY
```

### 34.4 Definição persistente candidata

A modelagem final pertence a `21` e deve ser congelada em C0 antes de migration. Campos semânticos mínimos candidatos:

```text
recurringWorkId
ownerRef
createdByActorRef
workTemplateRef / workflowDefinitionRef
scheduleSpec
scheduleTimezone
startAt?
endAt?
status
capabilityRefs[]
scopeRefs[]
connectionRefs[]?
recipient/target refs bounded
policyRef
misfirePolicy
failurePolicy
createdAt/updatedAt
version
```

`nextRunAt` pode ser projection/derived state se necessário; não deve criar segundo source of truth do scheduler físico.

### 34.5 Recurrence e timezone

Contrato de recurrence deve ser determinístico e versionado. Deve definir explicitamente:

```text
timezone IANA
calendar/recurrence expression
start/end bounds
daylight-saving behavior quando aplicável
missed-run/misfire semantics
concurrency/overlap policy
```

Não usar timezone implícito do servidor ou do browser como regra empresarial.

### 34.6 Occurrence

Cada materialização temporal gera uma ocorrência correlacionável e idempotente, candidate:

```text
occurrenceId
recurringWorkRef + definitionVersion
scheduledFor
triggeredAt?
correlationContext
idempotencyKey
actor/service identity ref
status
workflow/execution/outcome refs
```

A mesma ocorrência não pode produzir side effect duplicado por duplicate tick, retry, restart ou reconciliation.

### 34.7 Trigger não é autorização

Invariantes obrigatórios:

```text
schedule != permission
stored intent != eternal authorization
timer tick != ACT authority
recurrence definition != provider scope
```

Em cada ocorrência material, revalidar conforme capability:

```text
current user/service identity
→ live Core AuthZ
→ live Domain/business authority
→ current Policy/Decision
→ current connection/provider availability/scope
→ current data/source permissions
→ PREPARE or ACT
```

Se creator/user perder acesso, sair da empresa, connection for revogada, recipient/scope ficar inválido ou Policy mudar, a execução deve bloquear/degradar/pausar de forma truthful; nunca reutilizar autorização stale silenciosamente.

### 34.8 Recurring Work não é Watch autônomo

Recurring Work temporal e Watch são triggers distintos.

```text
Recurring Work
= usuário/owner define previamente uma recorrência bounded para um Work específico

Watch
= condição/evento observado que pode OBSERVE|ADVISE|PREPARE e, somente nas fases/policies permitidas, ACT
```

Em C5, uma ocorrência de Recurring Governed Work pode chegar a L4 governed ACT se a capability estiver explicitamente autorizada e todos os gates forem revalidados. Isso **não** habilita Watch autonomous ACT em C6 e **não** equivale a L5.

### 34.9 Exemplo canônico — relatório diário por email

Target:

```text
RecurringWorkDefinition
“daily 09:00 <timezone>”
        ↓
deterministic schedule trigger
        ↓
create occurrence + idempotency/correlation
        ↓
resolve current actor/service identity
        ↓
live AuthZ + Policy/Decision
        ↓
authorized reads for previous-day production data
        ↓
report.generate / Artifact with provenance
        ↓
PREPARE send intent
        ↓
revalidate recipients/connection/write capability
        ↓
communication.email.send
        ↓
provider/executor technical result
        ↓
authoritative/contractual send outcome verification when available
        ↓
Outcome + Evidence + Audit + Notification
```

```text
report generated != email authorized
email API accepted != verified final outcome automatically
```

### 34.10 C0 inventory/freeze

C0 deve responder com evidence:

1. quais schedulers/timers/cron/job systems já existem;
2. owner físico de cada mecanismo e SLA/HA;
3. se Automation Hub/plataforma já materializa timer triggers;
4. se DÉLIA deve persistir apenas RecurringWorkDefinition/occurrence refs ou também algum trigger state bounded;
5. contrato de timezone/DST/recurrence;
6. misfire/missed-run/reconciliation semantics;
7. overlap/concurrency semantics;
8. idempotência por ocorrência;
9. identity/AuthZ/revocation semantics de background execution;
10. pause/cancel/revoke/disable/kill-switch;
11. retention/audit/history;
12. authoritative Outcome sources para capabilities agendáveis.

C0 **não** cria scheduler novo por conveniência. Primeiro aplica Abstraction Gate e inventaria plataforma equivalente.

### 34.11 Phase mapping específico

```text
C0
= inventory + owner + contract + recurrence/timezone/misfire/idempotency/authz freeze

C1–C4
= foundations/reads necessários; nenhum side effect agendado material antecipado

C5
= runtime de Recurring Governed Work e ocorrência; L4 ACT agendado somente quando explicitamente authorized/gated

C6
= UX/admin para inspect/list/pause/resume/cancel/history/outcomes; Watch continua sem autonomous ACT

C7
= não é pré-requisito para recurring L4 governed ACT; L5/selected autonomous Watch ACT continuam separados
```

### 34.12 Acceptance outcomes específicos

Quando implementado, provar no SHA/config avaliado:

```text
recurring definition survives session/restart
timezone/recurrence is deterministic
pause prevents future occurrences
resume does not replay unauthorized history
cancel/revoke prevents future occurrences
duplicate timer signal does not duplicate side effect
retry/restart does not duplicate same occurrence
missed-run policy is explicit and reproducible
overlap/concurrency policy is explicit
live AuthZ/Policy is revalidated per material occurrence
revoked user/connection/capability cannot continue silently
occurrence links Work/Decision/Execution/Outcome/Evidence
material ACT verifies authoritative/contractual postcondition
scheduled report→email anchor works without open chat session
```

Sem evidence obrigatória: `PENDING`/`INCONCLUSIVE`, nunca PASS.
