# Minha DELPI Copilot — Durable Workflow Runtime

**Status:** arquitetura proposta  
**Objetivo:** suportar tarefas que atravessam minutos, horas ou dias, incluindo waits, eventos, confirmações e retomada segura.

## 1. Problema

Um request HTTP/LLM não é unidade suficiente para fluxos como:

- “acompanhe até Engenharia liberar a revisão”;
- “aguarde aprovação e depois execute”;
- “investigue este problema, peça dados faltantes e continue quando chegarem”;
- “monitore este pedido até normalizar”.

## 2. Princípio

O planner produz um plano operacional; o runtime durável gerencia estado/tempo/eventos.

```text
Planner
→ WorkflowPlan
→ Durable Workflow Runtime
   ├─ execute step
   ├─ checkpoint
   ├─ wait_event
   ├─ wait_user
   ├─ wait_approval
   ├─ sleep/deadline
   ├─ resume
   ├─ retry_safe
   └─ complete/fail/cancel
```

O runtime não cria um novo HTTP executor; reutiliza capabilities/executors/policies existentes.

## 3. Estados mínimos

```text
PLANNED
RUNNING
WAITING_USER
WAITING_EVENT
WAITING_APPROVAL
WAITING_TIME
BLOCKED
SUCCEEDED
PARTIALLY_SUCCEEDED
FAILED
CANCELLED
EXPIRED
```

## 4. Workflow instance

Campos conceituais:

```text
workflowId
workflowDefinition/version quando aplicável
goal
caseId/taskId
status
step states
entity refs
result refs
pending gate/watch refs
checkpoints
budgets
timestamps
correlation/audit IDs
```

Não persistir chain-of-thought.

## 5. Step contract

```json
{
  "stepId": "s3",
  "capabilityRef": "quality.action_plan.create",
  "dependsOn": ["s1", "s2"],
  "status": "planned",
  "mode": "write",
  "confirmationBoundary": "required",
  "expectedOutcome": "action plan created"
}
```

## 6. Checkpoints

Checkpoint deve armazenar estado suficiente para retomada determinística:

- step concluído e result refs;
- resolved arguments necessários;
- pending requirements;
- pending decision/watch;
- relevant versions/hashes quando necessário;
- idempotency key para writes.

## 7. Waits

### `wait_user`
Falta dado/escolha do usuário.

### `wait_approval`
Decision Gate pendente.

### `wait_event`
Watch/evento de domínio/plataforma.

### `wait_time`
Deadline/cooldown agendado, quando realmente necessário.

Todo wait precisa de timeout/expiry semantics ou justificativa explícita.

## 8. Resume

Ao retomar:

```text
load checkpoint
→ validate workflow/version compatibility
→ revalidate identity/RBAC/policy
→ refresh stale critical facts
→ invalidate stale confirmation if needed
→ continue
```

Permissão válida no início não autoriza execução futura após revogação.

## 9. Retry

- reads: retry conforme policy/backoff;
- writes: somente com idempotência/contrato seguro;
- ambiguous timeout após write: verificar outcome antes de tentar novamente;
- nenhum loop infinito de tool/LLM.

## 10. Compensation

Só usar compensation quando o domínio fornece operação real e semântica clara.

Não inventar rollback universal para ações de negócio.

## 11. Partial failure

Fluxo deve distinguir:

```text
executed
failed
skipped
blocked
waiting
compensated
```

A síntese final não pode afirmar conclusão total se objetivos materiais ficaram pendentes.

## 12. Cancelamento

Usuário/policy/admin pode cancelar quando permitido.

Cancelamento:

- impede novos steps;
- não desfaz automaticamente efeitos já persistidos;
- registra estado final e efeitos existentes;
- pode oferecer compensação real quando disponível.

## 13. Event integration

O runtime se integra a Copilot Watch/Event Bus:

```text
workflow WAITING_EVENT
→ event arrives
→ correlation/match
→ permission/policy revalidation
→ resume
```

## 14. Tasks/Cases/Inbox

- Task/Case é a unidade de produto;
- Workflow é a execução operacional;
- Inbox apresenta waits/approvals/results;
- Room permite colaboração humana;
- Watch retoma/alerta.

## 15. Escalabilidade

Requisitos:

- worker/runtime stateless entre checkpoints quando possível;
- queue/event transport apropriado;
- leases/locking para evitar execução dupla;
- idempotent event consumption;
- bounded retries;
- dead-letter/failure handling;
- observabilidade por workflow/step.

A tecnologia concreta deve ser escolhida após inventário de infraestrutura existente; não introduzir engine externa sem necessidade comprovada.

## 16. Testes obrigatórios

- workflow simples;
- wait_user + resume;
- wait_approval + approval/rejection/expiry;
- wait_event;
- reload/restart de worker;
- duplicate event;
- concurrent resume;
- permission revoked while waiting;
- confirmation args changed;
- write timeout ambiguous;
- partial failure;
- cancellation;
- budget/loop exhaustion;
- no duplicate write after restart.

## 17. Implantação

### DW0
- persistência de WorkflowPlan/steps/checkpoints.

### DW1
- wait_user/confirmation + resume.

### DW2
- event/watch integration.

### DW3
- long-running Cases/Rooms.

### DW4
- scale/resilience/operational tooling.

## 18. Gate

Não declarar “long-running workflow” quando o sistema apenas mantém uma requisição aberta ou reexecuta o prompt inteiro após reload. Retomada deve ser baseada em estado estruturado/checkpoint e preservar segurança/idempotência.