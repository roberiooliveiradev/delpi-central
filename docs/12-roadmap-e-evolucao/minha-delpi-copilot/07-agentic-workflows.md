# 07 — Workflows Agentic e Durable Work

## 1. Objetivo

Permitir que o Copilot execute objetivos compostos com múltiplas capabilities/apps/fontes, preservando dependências, policy, evidence, Decision Gates, idempotência e continuidade.

“Agentic” descreve o padrão de execução, **não agentes departamentais distintos**.

## 2. Contrato antes do runtime

Os semantics de `WorkflowPlan`, `WorkflowStep`, `TaskRef`, `CaseRef`, wait states e correlation são definidos/reutilizados em C0.

A persistência/engine durável concreta só é implementada em C5 após inventário de infraestrutura existente.

## 3. Modelo de execução

```text
GOAL
→ UNDERSTAND
→ RETRIEVE capabilities/expertise/playbooks
→ PLAN DAG
→ CHECK POLICY
→ EXECUTE READY STEPS
→ OBSERVE Outcome/Evidence
→ CHECKPOINT
→ CONTINUE | REPLAN | WAIT | COMPLETE | BLOCK
```

## 4. WorkflowPlan

Cada plano operacional pode conter:

- goal/subgoals;
- entity refs;
- expertise/playbook refs;
- steps;
- dependencies;
- capability refs;
- preconditions;
- expected outcomes;
- pending requirements;
- Decision Gate boundaries;
- status/budget.

Não persistir chain-of-thought.

## 5. Paralelismo

Reads independentes e seguros podem executar em paralelo.

Writes, destructive actions e dependências causais são serializados salvo contrato explícito e seguro.

## 6. Replanejamento

Permitido quando:

- capability indisponível;
- required argument ausente;
- outcome muda premissa;
- provider falha;
- usuário altera objetivo;
- policy bloqueia step;
- partial failure permite alternativa.

Replan nunca relaxa permission/policy/Decision Gate.

## 7. Clarify

```text
required ausente
+ nenhum valor grounded em mensagem/context/entity/result/evidence
→ pergunta específica
```

Não repetir perguntas respondidas.

## 8. Durable states

Quando workflow atravessa request/reload/tempo:

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

Waits são estados persistíveis, não loops de polling do LLM.

## 9. Checkpoints

Registrar somente estado operacional necessário:

- plan/version;
- completed steps;
- outcome/evidence refs;
- Decision Gate refs;
- wait state;
- attempt/idempotency;
- error classification;
- checkpoint version.

## 10. Retry/idempotency

- read pode retry conforme policy;
- write só retry com garantia idempotente/documentada;
- crash após write e antes de checkpoint deve ser tratável sem efeito duplicado;
- duplicate event/resume deve ser deduplicado;
- ambiguous outcome não vira retry cego.

## 11. Partial failure

Estados finais devem ser truthfully representados:

```text
SUCCEEDED
PARTIALLY_SUCCEEDED
BLOCKED
FAILED
CANCELLED
WAITING_*
```

Se fonte não crítica falha, a análise pode continuar com limitação explícita. Se precondition crítica falha, write dependente não executa.

## 12. Decision boundaries

Antes de write governado, usar o `DecisionGate` compartilhado:

```text
impact preview
+ args hash
+ evidence refs
+ risk/policy
→ Decision Gate
→ revalidate
→ execute
```

Workflow referencia decisão; não cria confirmation schema próprio.

## 13. Task

Task é uma unidade operacional curta/média respaldada pelo workflow.

Não possui planner/executor próprio.

Pode mostrar:

- objective;
- progress;
- steps;
- pending decisions;
- results/evidence;
- links.

## 14. Case

Case organiza trabalho/investigação longa sobre:

- entity refs;
- evidence;
- Tasks/Workflows;
- hypotheses/decisions/actions;
- room/artifacts;
- timeline.

Case não é novo executor nem source de negócio.

## 15. Event-driven resume

`wait_event` usa `EventEnvelope` compartilhado.

Fluxo:

```text
event
→ validate/dedupe/correlate
→ revalidate user/policy
→ resume workflow
```

Watch pode produzir/consumir o mesmo modelo de evento; não criar envelope paralelo.

## 16. Exemplos

### Investigação read-only

> “Descubra por que este item está atrasado.”

Reads + Graph + expertise + evidence → synthesis.

### Governed write

> “Crie uma solicitação para Compras com esse diagnóstico.”

Result/evidence refs → write preview → Decision Gate → execute → verify.

### Long-running

> “Acompanhe até Engenharia liberar a nova revisão e então reanalise.”

Workflow → `wait_event` → Watch/event → resume → reanalysis.

### Cross-domain Case

> “Investigue a reclamação e monte um 8D.”

Case + Graph + multimodal + expertise/playbook + Tasks.

## 17. Budgets

Configurar limites por owner/policy:

- planner rounds;
- tools;
- retries;
- fan-out;
- elapsed time;
- tokens/cost;
- workflow lifetime.

Budget exhaustion gera estado explícito, não loop infinito.

## 18. Auditoria

Cada step material deve ser correlacionável por:

```text
user/subject
request/turn/workflow/task/case ids
capability/action ref
entity refs
policy/Decision Gate ref
outcome/evidence refs
timestamps/duration
error classification
```

Sem chain-of-thought.