# 07 — Agentic Workflows

## 1. Objetivo

Permitir que o Copilot execute objetivos compostos envolvendo múltiplas capabilities, apps e fontes, com controle explícito de dependências, segurança, custo e progresso.

## 2. Modelo de execução

```text
GOAL
→ DECOMPOSE
→ PLAN DAG
→ CHECK POLICY
→ EXECUTE READY STEPS
→ OBSERVE
→ UPDATE STATE
→ REPLAN IF NEEDED
→ COMPLETE | CLARIFY | BLOCK
```

## 3. Task Graph

Cada plano deve representar:

- `goalId`;
- subtarefas;
- dependências;
- capability candidates;
- argumentos resolvidos;
- argumentos pendentes;
- status;
- result references;
- policy/confirmation state.

Exemplo:

```text
G1 analisar atraso do produto
  ├─ S1 estoque
  ├─ S2 pedidos em aberto
  ├─ S3 produção
  ├─ S4 compras
  └─ S5 sintetizar causas ← depende S1..S4

G2 abrir contexto no Portal
  └─ S6 abrir Portal Suprimentos ← depende entidade resolvida

G3 criar solicitação
  └─ S7 criar request ← depende S5 + confirmação
```

## 4. Paralelismo

Reads independentes e seguros podem executar em paralelo.

Writes, destructive actions e steps com dependência causal não devem ser paralelizados sem contrato explícito.

## 5. Replanejamento

Replanejar quando:

- action indisponível;
- required argument não resolvido;
- resultado muda premissa;
- provider falha;
- usuário altera objetivo;
- policy bloqueia um step;
- partial failure permite caminho alternativo.

Replanejamento não pode reduzir safety para “dar certo”.

## 6. Clarify

Perguntar somente o necessário.

```text
required ausente
+ não existe valor grounded em mensagem/context/memória
→ clarify específico
```

Não perguntar novamente dados já conhecidos e confiáveis.

## 7. Checkpoints

Workflows com múltiplos passos devem registrar checkpoints:

- plano criado;
- steps concluídos;
- confirmações;
- resultados referenciados;
- falha/retry;
- completion state.

Isso permite F5/reload e retomada segura.

## 8. Partial failure

O resultado final deve distinguir:

```text
COMPLETED
PARTIALLY_COMPLETED
BLOCKED
FAILED
CANCELLED_BY_USER
AWAITING_CONFIRMATION
AWAITING_INPUT
```

Se 3 de 4 fontes responderam, o Copilot pode analisar as três, mas deve declarar a limitação.

## 9. Workflows de exemplo

### Investigação operacional

> “Descubra por que este item está atrasado e me diga o que fazer.”

Consulta múltiplas fontes → análise → recomendação.

### Ação após análise

> “Agora crie uma solicitação para Compras com esse diagnóstico.”

Usa fatos/result refs do turno anterior → prepara write → confirmação → execução.

### Navegação contextual

> “Abra o pedido que mais contribuiu para esse atraso.”

Resolve entity ref → Platform Action.

### Comunicação

> “Avise o comprador responsável.”

Resolve responsável → compõe mensagem → policy → action de comunicação.

## 10. Loops e limites

Configurar budgets:

- máximo de planner rounds;
- máximo de tools por turno;
- máximo de retries;
- timeout global;
- limite de tokens/custo;
- limite de fan-out.

Ao atingir budget, retornar estado parcial e pedir decisão do usuário quando necessário.

## 11. Writes encadeados

Nunca executar uma sequência de writes baseada apenas em uma intenção vaga.

Antes da confirmação, apresentar resumo operacional:

```text
Vou:
1. criar a solicitação X;
2. relacionar o produto Y;
3. atribuir ao grupo Compras;
4. anexar o diagnóstico Z.
```

## 12. Auditoria

Cada step executado deve possuir:

- actor userId;
- conversation/turn/workflow id;
- capabilityId/actionId;
- policy decision;
- confirmation reference quando aplicável;
- outcome;
- timestamps;
- correlation id do sistema alvo.

Sem armazenar chain-of-thought.
