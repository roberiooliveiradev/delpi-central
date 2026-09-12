# Minha DELPI Copilot — Inbox, Watch e Trabalho Proativo

**Status:** arquitetura de produto proposta  
**Objetivo:** evoluir do modelo exclusivamente reativo para acompanhamento governado de eventos, condições e pendências.

## 1. Copilot Inbox

A Inbox centraliza o que requer atenção do usuário.

Categorias mínimas:

```text
AGUARDANDO VOCÊ
→ confirmações, approvals, dados faltantes, escolhas

TRABALHANDO
→ tasks/cases/workflows em execução ou espera

CONCLUÍDO
→ resultados recentes relevantes

ALERTAS
→ condições monitoradas atingidas, riscos e exceções
```

Cada item deve apontar para Task/Case/Workflow/EntityRef correspondente.

## 2. Copilot Watch

`Watch` representa uma condição futura monitorada pelo Copilot.

Exemplos:

- pedido entrar em atraso;
- estoque cair abaixo do limite;
- Engenharia liberar revisão de desenho;
- fornecedor ultrapassar SLA;
- resposta chegar numa sala/caso;
- ação ficar vencida;
- indicador ultrapassar threshold;
- documento/registro mudar de estado.

## 3. Event-first

Preferência arquitetural:

```text
domain/platform event
→ event bus/handler
→ watch matching
→ policy
→ observe | advise | act
```

Polling só quando não existir evento ou integração melhor, com frequência e custo controlados.

## 4. Três modos de resposta

```text
OBSERVE
→ registra/atualiza estado sem interromper usuário

ADVISE
→ cria alerta/recomendação/inbox item

ACT
→ executa capability permitida dentro de policy explícita
```

`ACT` não significa autonomia irrestrita; segue os níveis L0–L5 e Decision Gates.

## 5. Contrato conceitual de Watch

```json
{
  "watchId": "uuid",
  "ownerUserId": "...",
  "subjectRefs": [{"type":"purchaseOrder","id":"450231"}],
  "condition": {
    "kind": "status_changed",
    "target": "late"
  },
  "responseMode": "advise",
  "policyRef": "...",
  "status": "active"
}
```

Condição não deve ser armazenada como código arbitrário ou expressão insegura executável.

## 6. Watch + Business Graph

O Watch pode observar uma entidade e, quando disparado, expandir relações autorizadas para análise.

Exemplo:

```text
pedido atrasou
→ produto
→ estoque
→ OP
→ compras
→ risco consolidado
→ alerta grounded
```

## 7. Watch + Cases

Um Case pode possuir watchers internos:

- aguardar evidência;
- aguardar aprovação;
- aguardar status externo;
- prazo de ação;
- deadline de investigação.

Evento retoma o Durable Workflow correspondente.

## 8. UX

Um item de Inbox deve responder:

```text
o que aconteceu?
por que isso importa?
qual evidence suporta?
qual ação está disponível?
é obrigatório decidir agora?
```

Nunca mostrar alerta genérico sem contexto acionável quando o sistema possui dados para explicar.

## 9. Dedupe e ruído

Obrigatório evitar fadiga de alertas:

- dedupe por watch/subject/event;
- cooldown quando aplicável;
- agrupamento de ocorrências semelhantes;
- severidade;
- quiet hours/preferences quando permitido;
- resolução automática de alerta quando condição deixa de existir, se semântica permitir.

## 10. Segurança

- watch pertence a usuário/grupo/policy claramente definidos;
- permissão é revalidada no disparo, não apenas na criação;
- dados revogados não permanecem acessíveis via Inbox;
- evento externo é tratado como dado não confiável;
- `ACT` revalida policy/confirmation/idempotency.

## 11. Auditoria

Registrar:

```text
watch created/updated/disabled
condition matched
source event
policy outcome
advice emitted
action prepared/executed/rejected
user acknowledged/dismissed
```

## 12. Implantação

### PW0
- inbox contract e UI read-only;

### PW1
- Watch read-only/ADVISE com eventos existentes;

### PW2
- ligação com Task/Case e Durable Workflow;

### PW3
- ACT apenas para capabilities explicitamente allowlisted e após gates de autonomia.

## 13. Não fazer

- criar cron/polling específico por app no core;
- armazenar prompt livre como condição executável;
- enviar alertas sem dedupe/budget;
- executar write porque o Watch existia antes de uma revogação de permission;
- confundir Watch com scheduler genérico sem contexto de negócio.