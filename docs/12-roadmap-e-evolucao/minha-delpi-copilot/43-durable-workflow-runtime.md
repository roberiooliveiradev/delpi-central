# Minha DELPI Copilot — Durable Workflow Runtime

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** Workflow/Step/wait semantics nascem em C0; runtime/persistência em C5.

## 1. Objetivo

Suportar trabalho que atravessa minutos, horas ou dias, incluindo waits, eventos, decisões humanas, restart e retomada segura.

## 2. Princípio

```text
Planner
→ WorkflowPlan compartilhado
→ Durable Workflow Runtime
   ├─ execute canonical capability
   ├─ checkpoint
   ├─ wait_user
   ├─ wait_approval
   ├─ wait_event
   ├─ wait_time
   ├─ resume
   ├─ retry_safe
   └─ complete/fail/cancel
```

O runtime **não cria outro HTTP/tool executor**.

## 3. Estados

Usar o lifecycle compartilhado do `21-data-and-state-model.md`:

```text
planned
running
waiting_user
waiting_approval
waiting_event
waiting_time
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

Usar `WorkflowStep` foundation:

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
```

Não criar `confirmationBoundary`; Decision Gate é o modelo compartilhado.

## 6. Checkpoint

Checkpoint armazena somente o necessário para retomada segura:

- plan/version;
- completed/current steps;
- result/outcome/evidence refs;
- resolved arguments necessários;
- pending requirements;
- Decision/wait refs;
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
- bounded retries/loops.

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
Workflow = execução operacional
Task = unidade de produto curta/média
Case = investigação/trabalho longo
Room = colaboração
Inbox = materialização de atenção/estado
```

Nenhum deles cria executor paralelo.

## 15. Infrastructure

Escolher após C0 inventory:

- persistence;
- queue/worker;
- scheduler;
- event transport;
- lease/locking;
- dead-letter/failure handling.

Reutilizar infraestrutura existente quando compatível. Engine externa nova precisa gap/ADR.

## 16. Scalability

- workers stateless entre checkpoints quando possível;
- locking/lease anti-double execution;
- idempotent event consumption;
- bounded retry;
- partition/queue strategy se necessário;
- observability por workflow/step;
- retention/archive.

## 17. Tests

- simple workflow;
- wait_user;
- wait_approval approve/reject/expire;
- wait_event;
- restart;
- duplicate event;
- concurrent resume;
- permission/policy revoked;
- Decision invalidated;
- crash after write before checkpoint;
- ambiguous outcome;
- partial failure;
- cancel/expiry;
- budget exhaustion;
- no duplicate write.

## 18. Implementation mapping

Não executar `DW*` como roadmap separado.

```text
C0 → Workflow/Step/wait contracts + infra inventory
C5.S1 → persistence/checkpoint runtime
C5.S2 → waits
C5.S3 → DAG runner
C5.S4–S7 → Task/Case/Room/Inbox consumers
C5.S8 → restart/resume gate
C6 → Watch OBSERVE/ADVISE event integration
C7 → selected Watch ACT/autonomy
```

## 19. Gate

Não declarar long-running workflow se:

- request apenas fica aberto;
- sistema reexecuta prompt inteiro após reload;
- não existe checkpoint estruturado;
- resume pode duplicar write;
- policy não é revalidada;
- Event/Decision contracts paralelos foram criados.