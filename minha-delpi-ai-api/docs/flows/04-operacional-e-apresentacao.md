# 04 — Actions operacionais e apresentação

## Objetivo

Mapear o fluxo vigente de linguagem natural até execução e apresentação de Actions OpenAPI.

```text
mensagem
→ decomposição/contexto
→ allowed actions
→ Action Catalog
→ retrieval top-K
→ structured planner
→ OpenAPI argument validation
→ RBAC/policy/confirmation
→ ExecuteExternalActionUseCase
→ HTTP provider
→ schema-driven presentation
→ renderPlan
→ MFE render-only
```

---

## 1. Descoberta e seleção

A fonte técnica é OpenAPI + Action Catalog.

| Etapa | Responsabilidade |
|-------|------------------|
| Import | normalizar operation/schema |
| Index | documento semântico/embedding/metadata |
| Governança | provider/action binding + `allowed_action_ids` |
| Retrieval | reduzir para top-K candidates |
| Planner | selecionar action(s) e propor argumentos |
| Validator | conferir args contra OpenAPI |

Não cadastrar rota em catálogo técnico paralelo para torná-la selecionável.

---

## 2. Argumentos

O validator cobre, conforme schema:

```text
path
query
body
required
type
enum
format
additional properties
```

Missing required sem valor grounded → clarify específico.

---

## 3. Execução

```text
selected action
→ enabled/allowed check
→ RBAC/policy/sensitivity
→ confirmation quando exigida
→ HTTP gateway
→ normalized result
```

URL é derivada do provider/action persistidos; o LLM não produz URL executável arbitrária.

---

## 4. Pedidos compostos

Uma mensagem pode produzir múltiplas actions:

```text
subtarefas
→ dependencies
→ reads paralelas quando independentes/seguras
→ writes seriais/policy
→ partial-failure handling
→ síntese final completa
```

---

## 5. Multi-turn

Follow-ups usam estado estruturado da action/resultado anterior:

```text
entities
arguments
result references
pending fields
pagination/time range
presentation preference
```

Não usar substring do path como memória conversacional.

---

## 6. Apresentação

```text
responseSchema + payload runtime + metadata
→ ChatSchemaDrivenPresentationService
→ presentationDecision
→ renderPlan
→ plugin render-only
```

Perfil dedicado é opcional. API externa sem metadata DELPI deve continuar apresentável pelo fallback genérico.

---

## 7. Refinamento de formato

Pedidos como:

```text
mostre em tabela
gere um gráfico
só texto
mostre em árvore
```

reapresentam dados existentes quando possível, sem disparar nova Action operacional aleatória.

---

## 8. Evals

Mudanças neste fluxo seguem [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md):

- R1 routing;
- R2 trajectory;
- R3 arguments;
- R4 utility/faithfulness;
- R5 presentation;
- R6 follow-up;
- R7 parity;
- R8 latency;
- R9 outcome;
- R10 safety;
- R11 efficiency.

Mudança no motor de Actions exige API externa desconhecida + teste metamórfico.

---

## Referências

- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
- [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)
- [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md)
- [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)
