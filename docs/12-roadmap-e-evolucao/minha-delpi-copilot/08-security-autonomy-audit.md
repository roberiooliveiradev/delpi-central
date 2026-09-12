# 08 — Segurança, autonomia e auditoria

## 1. Invariante principal

```text
Permissões do Copilot ⊆ permissões efetivas do usuário
```

O Copilot nunca opera como superusuário implícito e nunca usa credencial privilegiada para executar algo que o usuário não poderia executar diretamente.

## 2. Autorização

Fluxo recomendado:

```text
identidade
→ permissões efetivas Core API
→ capabilities autorizadas
→ planner restrito
→ policy/sensitivity
→ confirmação quando necessário
→ executor
→ backend revalida autorização
```

O backend continua sendo a autoridade final.

## 3. Níveis de autonomia

### L0 — Explicar

Sem execução operacional.

### L1 — Navegar

Ações de Portal/Shell sem alteração de negócio.

### L2 — Consultar e analisar

Reads e análise grounded.

### L3 — Preparar alteração

O Copilot monta payload/plano, mas não executa ainda.

### L4 — Executar com confirmação

Write/destructive permitido após confirmação explícita conforme policy.

### L5 — Execução automática governada

Somente para fluxos previamente autorizados por policy, escopo e risco. Não é default.

## 4. Sensitivity

Sugestão de classes:

```text
read
write
sensitive_write
admin
destructive
external_communication
financial
personal_data
```

Cada classe define:

- se exige confirmação;
- tipo de confirmação;
- limite de autonomia;
- campos a mascarar em logs;
- necessidade de auditoria reforçada.

## 5. Confirmação

A confirmação deve descrever efeito real.

Bom:

> “Vou cancelar a solicitação SC-00123. Essa ação encerra o fluxo atual e exige nova solicitação para reabertura. Confirmar?”

Ruim:

> “Confirmar ação?”

Confirmation token/reference deve estar associado ao plano/payload que será executado para impedir troca silenciosa entre confirmação e execução.

## 6. Revalidação no momento da execução

Entre planejamento e execução podem mudar:

- permissões;
- estado da entidade;
- versão do registro;
- disponibilidade do provider.

Portanto revalidar imediatamente antes do write.

## 7. Proteção contra prompt/tool injection

Conteúdo vindo de:

- RAG;
- APIs;
- anexos;
- páginas web;
- campos de banco;

é dado, não instrução de sistema.

Nunca permitir que tool output altere RBAC, allowed capabilities ou confirmation policy.

## 8. URLs e execução externa

O modelo não produz URLs arbitrárias para o executor HTTP.

A URL vem do provider/action persistidos e validados no catálogo.

## 9. Auditoria

Eventos mínimos:

```text
copilot.plan.created
copilot.capability.selected
copilot.confirmation.requested
copilot.confirmation.accepted|rejected
copilot.action.started
copilot.action.completed|failed
copilot.workflow.completed|partial|blocked
copilot.navigation.executed
```

Campos úteis:

- actor;
- session/conversation/turn;
- app/context;
- capability/action;
- sensitivity;
- permission decision;
- confirmation reference;
- outcome;
- duration;
- correlation id.

## 10. Dados sensíveis

Não persistir em observabilidade:

- JWT;
- refresh token;
- API key;
- senha;
- secrets;
- chain-of-thought.

Payloads sensíveis devem ser reduzidos/redigidos.

## 11. Idempotência

Writes devem usar idempotency key quando o sistema alvo suportar.

Retries cegos em POST/DELETE são proibidos.

## 12. Autonomia configurável

A política pode combinar:

```text
user/group
capability
sensitivity
app/domain
ambiente
tipo de dado
horário/processo
```

Mas deve permanecer governada e auditável, nunca escondida em prompt.

## 13. Emergency stop

Deve existir mecanismo operacional para:

- desabilitar writes do Copilot;
- desabilitar provider/action;
- colocar capability em read-only;
- desabilitar workflows agentic;
- revogar integração comprometida.

## 14. Princípio de least privilege

O Copilot deve receber somente o subconjunto de capabilities necessário para o usuário/agente/contexto atual, reduzindo superfície de erro e custo de planning.
