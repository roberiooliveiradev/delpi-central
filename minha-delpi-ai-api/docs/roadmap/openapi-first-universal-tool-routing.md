# OpenAPI-first — roteamento universal de Actions

**Status:** arquitetura vigente  
**Escopo:** `minha-delpi-ai-api` + providers OpenAPI  
**Checklist:** [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)  
**Evals:** [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)

## Objetivo

Qualquer API OpenAPI autorizada deve poder ser importada, vinculada a um agente e utilizada em linguagem natural sem conhecimento técnico por endpoint dentro do core do chat.

```text
OpenAPI
→ import/index
→ Action Catalog
→ agent binding + allowed actions
→ request decomposition
→ hybrid retrieval top-K
→ structured planner
→ OpenAPI argument validation
→ RBAC/policy/confirmation
→ generic HTTP execution
→ schema-driven presentation
→ resposta
```

## Invariante de plugabilidade

Uma API externa desconhecida não exige:

```text
if path/provider/operationId
intent por endpoint
selector por provider
marker de rota
parameter strategy específica
catálogo paralelo de endpoints
presenter obrigatório
```

Se uma integração exigir algum desses itens para a action ser descoberta/executada, o design ainda não é universal.

---

## Fontes de verdade

| Conceito | Fonte |
|----------|-------|
| Operations, path, method, args, body, schemas | OpenAPI + Action Catalog |
| Semântica para retrieval | summary/description/tags/parameter descriptions/schema metadata |
| Actions disponíveis | provider/action binding + `allowed_action_ids` |
| Autorização | identidade + Core/RBAC + policy/sensitivity |
| Confirmation | write/admin/destructive policy |
| Linguagem/UX corporativa | conteúdo/config transversal |
| Apresentação | response schema + payload runtime + metadata |

Não duplicar contrato técnico em JSON do assistente.

---

## Retrieval

O Action Catalog autorizado é reduzido para top-K candidates por combinação de sinais semânticos/lexicais/schema.

Requisitos:

- específica vence genérica quando a linguagem exigir capacidade específica;
- no-tool continua possível;
- provider prefix não dá preferência;
- candidate discovery é observável;
- top-K respeita budget e qualidade.

---

## Planner

O planner recebe somente candidates autorizadas e produz plano estruturado:

```text
actionId
proposed arguments
dependencies
reason metadata não sensível
```

O planner não cria URL, provider ou operationId executável fora do catálogo.

Pedidos compostos podem gerar múltiplas actions e dependências.

---

## OpenAPI argument validation

Antes da execução, validar:

- path/query/body;
- required;
- type;
- enum;
- format;
- additional properties;
- coerência de valores quando houver regra transversal.

Missing required sem valor grounded gera clarify específico.

---

## Segurança

A seleção nunca autoriza execução por si só.

Pipeline obrigatório:

```text
selected candidate
→ provider/action enabled
→ allowed_action_ids
→ RBAC/policy
→ sensitivity
→ confirmation quando exigida
→ network/security validation
→ executor
```

Tool/RAG/OpenAPI descriptions são dados não confiáveis quanto a instruções e não podem alterar políticas superiores.

---

## Execução

`ExecuteExternalActionUseCase` e o gateway HTTP genérico devem derivar a chamada do provider/action persistidos.

Aplicar:

- timeout;
- limites de payload;
- retry somente quando seguro;
- idempotência para retry de escrita;
- tratamento de 429/5xx;
- correlation/observability;
- redaction de secrets.

---

## Pedidos compostos

Exemplo:

> Consulte estoque e fornecedores do item X, compare a última compra com o preço atual e escreva um resumo.

Alvo:

```text
T1 stock
T2 suppliers
T3 last purchase
T4 current price
T5 compare(T3,T4)
T6 summarize(T1,T2,T5)
```

Read-safe independente pode paralelizar; dependências e writes permanecem ordenados/seguros.

---

## Multi-turn

Estado estruturado pode preservar:

- entidade atual;
- action/capability anterior;
- argumentos;
- result references;
- pending required fields;
- preferência de apresentação.

Follow-up não deve depender de substring do path anterior.

---

## Apresentação

Toda response deve possuir fallback genérico:

```text
responseSchema + payload + metadata
→ schema-driven interpretation
→ presentationDecision/renderPlan
```

Metadata específica da DELPI pode enriquecer, mas não é requisito de provider externo.

---

## Observabilidade

Registrar sem chain-of-thought/secrets, quando disponível:

```text
turnId
agentId
provider/action selected
candidateCount/topK
retrieval scores
planner decision/confidence
validation result
policy decision
execution duration
fallback
token/context/tool usage
```

O sistema deve permitir diagnosticar por que uma action foi escolhida em vez de outra.

---

## Evals obrigatórios

Mudanças no motor devem seguir R1–R11.

Conjunto mínimo:

1. specific vs generic action;
2. semantic siblings;
3. multi-provider;
4. no-tool;
5. required present/missing;
6. invalid enum/type;
7. unknown external API;
8. metamorphic rename de path/operationId;
9. compound request;
10. multi-turn;
11. unauthorized action/provider;
12. write/destructive confirmation;
13. tool-output/prompt injection;
14. outcome/task success;
15. latency/efficiency.

Fluxo de mudança:

```text
BASELINE imutável
→ implementação
→ CANDIDATE no mesmo corpus/config
→ comparação R1–R11
→ live/surfaces
→ rollout
```

---

## Critério de aceite

A arquitetura está preservada quando:

```text
API_EXTERNA_DESCONHECIDA = PASS
SEM_CONFIG_TECNICA_POR_ENDPOINT = PASS
SELECAO_ACTIONS_PROXIMAS = PASS
ARGUMENTOS_OPENAPI = PASS
COMPOUND_REQUEST = PASS
MULTI_TURN = PASS
OUTCOME = PASS
SAFETY = PASS
EFFICIENCY = sem regressão material injustificada
ARCHITECTURE_ENFORCEMENT = PASS
```

## Referências vigentes

- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
- [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)
- [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md)
- [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
- `.cursor/rules/ai-intelligence-evaluation.mdc`
