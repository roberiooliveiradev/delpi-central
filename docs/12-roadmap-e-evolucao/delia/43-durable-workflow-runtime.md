# DÉLIA — Durable Workflow Runtime

**Status:** thematic spec / TARGET até implementação comprovada  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Foundation:** Workflow/Step/wait semantics são decisões a congelar em C0; runtime/persistência entram em C5 somente após os gates; Task/Case/Room/Inbox consomem esse runtime em C6.

## 1. Objetivo

Suportar trabalho que atravessa minutos, horas ou dias, incluindo waits, eventos, decisões humanas, restart e retomada segura.

## 2. Princípio

```text
DÉLIA Planner
→ WorkflowPlan compartilhado
→ DÉLIA Durable Workflow Runtime
   ├─ coordinate semantic capability
   ├─ checkpoint
   ├─ wait_user
   ├─ wait_approval
   ├─ wait_event
   ├─ wait_time
   ├─ resume
   ├─ retry_safe
   └─ complete/fail/cancel
```

O runtime **não cria outro technical executor**. Para side effects ele usa o contrato aprovado do owner correto:

```text
DÉLIA Work
→ Domain API direct contract, quando essa for a ação autoritativa
ou
→ Automation Hub execution contract, quando houver execução técnica sob esse boundary
ou
→ approved external/provider adapter, conforme contrato e owner
→ technical result
→ authoritative Outcome verification
```

Automation Hub pode manter lifecycle técnico próprio de execution/worker/queue; esse state não é duplicado como source of truth da DÉLIA.

## 3. Estados

Usar o lifecycle compartilhado do `21-data-and-state-model.md`, somente após contrato congelado:

```text
planned
running
waiting_user
waiting_approval
waiting_event
waiting_time
waiting_execution
verifying_outcome
succeeded
partially_succeeded
failed
cancelled
expired
```

`blocked` pode existir como error/work status se o contract C0 final assim definir; não criar enum diferente apenas neste runtime.

## 4. Workflow instance

Campos conceituais:

```text
workflowId
subject/correlation refs
planVersion
status
currentCheckpoint
Task/Case refs quando aplicável
budgets/limits
timestamps
```

Goal/steps/result/evidence/decision refs vêm dos contracts compartilhados.

Não persistir CoT.

## 5. Step

Usar `WorkflowStep` foundation somente se C0 a congelar:

```text
stepId
capabilityRef
actionSourceRef?
dependsOn[]
status
attemptCount
idempotencyKey?
resultRef/errorCode
decisionRef?
executionRef?
```

Não criar `confirmationBoundary`; Decision Gate é o modelo compartilhado. `executionRef` é correlação/projeção, não cópia do state técnico do executor.

## 6. Checkpoint

Checkpoint armazena somente o necessário para retomada segura:

- plan/version;
- completed/current steps;
- result/outcome/evidence refs;
- resolved arguments necessários;
- pending requirements;
- Decision/wait refs;
- execution correlation refs;
- idempotency/concurrency data;
- critical source versions quando necessário.

## 7. Waits

### `wait_user`
Dado/escolha realmente necessária.

### `wait_approval`
Decision Gate/approval pendente.

### `wait_event`
Evento correlacionado via `EventEnvelope`.

### `wait_time`
Deadline/cooldown agendado com owner claro.

### `waiting_execution`
Aguarda resultado/callback/poll reconciliado de execução técnica sem transformar o workflow em worker/executor runtime.

Todo wait precisa expiry/timeout semantics ou justificativa explícita.

## 8. Resume

```text
load checkpoint
→ validate schema/plan compatibility
→ revalidate identity/RBAC/policy
→ refresh critical stale facts
→ re-evaluate Decision validity
→ acquire lock/lease when needed
→ continue
```

Permissão válida na criação não autoriza execução futura após revogação.

## 9. Retry/idempotency

- reads: retry/backoff conforme policy;
- writes: somente idempotent/protected;
- timeout ambíguo: reconcile outcome antes de retry;
- duplicate event/resume deduped;
- bounded retries/loops;
- DÉLIA não reexecuta technical side effect cegamente porque perdeu callback do Hub/provider.

Crash após write antes do checkpoint é caso obrigatório de teste.

## 10. Compensation

Só existe quando o domínio possui operação real com semântica adequada.

Não inventar rollback universal.

## 11. Partial failure

Representar truthfulmente:

```text
executed
failed
skipped
waiting
blocked by precondition/policy
compensated quando real
```

Workflow final pode ser `partially_succeeded` quando objetivos materiais não completaram.

## 12. Cancel/expiry

Cancelamento:

- impede novos steps;
- solicita cancelamento técnico ao owner somente quando o contrato suportar;
- não desfaz efeitos persistidos automaticamente;
- registra outcomes existentes;
- pode sugerir compensation real.

Expiry segue policy/lifecycle definido.

## 13. Event integration

```text
WAITING_EVENT
→ EventEnvelope arrives
→ schema/dedupe/correlation
→ current permission/policy
→ resume
```

Watch usa o mesmo event model.

## 14. Tasks/Cases/Inbox/Rooms

```text
Workflow = execução/orquestração operacional da DÉLIA
Task = unidade de produto curta/média
Case = investigação/trabalho longo
Room = colaboração
Inbox = materialização de atenção/estado
```

Task/Case/Room/Inbox entram em C6 e **não criam planner, technical executor ou workflow engine próprios**.

## 15. Infrastructure

Escolher após C0 inventory:

- persistence;
- queue/worker para o próprio Work runtime, se necessário;
- scheduler;
- event transport;
- lease/locking;
- dead-letter/failure handling;
- Automation Hub/client adapter contract for technical execution, if applicable.

Reutilizar infraestrutura neutra existente quando compatível. Engine externa nova precisa gap/ADR. Infra específica do Minha DELPI Chat não é dependency válida.

Worker do DÉLIA Work runtime não é automaticamente worker de RPA/executor; technical-execution workers pertencem ao Automation Hub/owner correspondente.

## 16. Scalability

- Work workers stateless entre checkpoints quando possível;
- locking/lease anti-double orchestration;
- idempotent event consumption;
- bounded retry;
- partition/queue strategy se necessário;
- observability por workflow/step;
- retention/archive;
- execution correlation without duplicating Hub technical state.

## 17. Tests

- simple workflow;
- wait_user;
- wait_approval approve/reject/expire;
- wait_event;
- wait_execution;
- restart;
- duplicate event;
- concurrent resume;
- permission/policy revoked;
- Decision invalidated;
- crash after write before checkpoint;
- lost/duplicate executor callback;
- ambiguous outcome;
- partial failure;
- cancel/expiry;
- budget exhaustion;
- no duplicate write;
- technical success without business postcondition remains unverified;
- executor substitution does not patch planner;
- restart da DÉLIA API sem Chat disponível.

## 18. Implementation mapping

Não executar `DW*` como roadmap separado.

```text
C0 → Workflow/Step/wait contracts + infra inventory
C5 → Durable Workflow runtime somente conforme substeps canônicos de 16
C6 → Task/Case/Room/Inbox/Watch consumers conforme substeps canônicos de 16
C7 → selected Watch autonomous ACT conforme 16/20/25
```

Este documento não redefine numeração atômica de substeps; `16` é authority exclusiva.

## 19. Independence

Durable Workflow pertence ao runtime standalone da DÉLIA; o namespace técnico físico permanece sujeito ao C0.S1. Não reutiliza session, job orchestration, agent state ou persistence do Minha DELPI Chat como runtime authority.

Também não incorpora internals do Automation Hub: integra por contrato e preserva separação Work/orchestration vs technical execution.

## 20. Gate

Não declarar long-running workflow se:

- request apenas fica aberto;
- sistema reexecuta prompt inteiro após reload;
- não existe checkpoint estruturado;
- resume pode duplicar write;
- policy não é revalidada;
- Event/Decision contracts paralelos foram criados;
- technical execution state foi duplicado como DÉLIA authority;
- DÉLIA bypassa Automation Hub quando esse é o owner técnico;
- runtime depende do Minha DELPI Chat estar ativo.
