# Plano 02 — NLU manual -> Turn Understanding + planner estruturado

**Prioridade:** P0  
**Status execução:** Onda C · inventário Onda A §6 · próxima = baseline TU vs intents authority  
**Evidência:** [`../evidence/onda-a-inventory.md`](../evidence/onda-a-inventory.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** frases longas, sinônimos, linguagem informal, typos e pedidos compostos devem ser compreendidos sem manutenção contínua de `terms`, `excludes`, regex e predicates por domínio.

## CURRENT

Principais fontes:

- `product_query_intent.json`;
- `production_operational_intent.json`;
- `department_kpi_rules.json`;
- `analysis_intent_vocabulary.json`;
- `intent_router.json`;
- `operational_pipeline_vocabulary.json`;
- `turn_understanding.json`;
- services que convertem palavras em intents/path tokens/route predicates.

### EXECUTION_DRIFT (2026-09-10)

`turn_understanding.json` + `ChatTurnUnderstandingService` já existem, mas operam em **shadow** (`turnUnderstandingShadow: true`; task planner execution off). Intents heurísticos continuam **autoridade** de routing/gates. Este plano = promover TU a authority com baseline/candidate — não criar pipeline do zero.

Padrão residual:

```text
mensagem
-> normalização
-> termos/regex/excludes
-> anyOf/allOf/noneOf/customPredicate
-> intent/domain/path hint
-> routing
```

## TARGET

```text
mensagem + contexto estruturado
-> LLM Turn Understanding
-> goals[] + entities + references + dependencies + requestedPresentation
-> retrieval por goal
-> planner estruturado
```

Fast paths pequenos podem permanecer apenas para sinais inequívocos e mensuravelmente úteis.

## Requisitos

| ID | Requisito |
|---|---|
| R02-01 | Mapear toda decisão de intent que hoje influencia routing/tool choice. |
| R02-02 | Separar entity extraction determinística de classificação semântica. |
| R02-03 | Decompor pedidos longos em múltiplos goals. |
| R02-04 | Preservar no-tool, RAG, presentation-only e conversational turns. |
| R02-05 | Cobrir typos/sinônimos sem listas crescentes por caso. |
| R02-06 | Evitar nova chamada LLM quando o planner/turn analysis já puder produzir o contrato. |

## Contrato alvo de entendimento

O plano de implementação deve convergir para DTO/schema explícito, por exemplo conceitual:

```json
{
  "goals": [
    {
      "goalId": "g1",
      "intent": "consultar estoque do produto",
      "entities": {"productCode": "10080001"},
      "dependsOn": []
    }
  ],
  "references": [],
  "presentationIntent": {"view": "table"},
  "needsTool": true,
  "confidence": 0.93
}
```

O campo `intent` é semântico, não enum por endpoint.

## Etapas

### E2.S1 — Inventário das árvores heurísticas

**Fazer:** mapear cada `terms/excludeTerms/regex/predicate/pipeline` e o consumer que altera routing, args, presentation ou fast-path.

**Não fazer:** migrar listas editoriais/help que não decidem execução.

**Pronto quando:** matriz distingue `SEMANTIC_ROUTING_HEURISTIC`, `VOCABULARY`, `FAST_PATH`, `UX_COPY` e `BUSINESS_RULE`.

### E2.S2 — Baseline de entendimento

**Fazer:** corpus com requests curtos/longos, 2-4 goals, coordenação sem “e”, typos, sinônimos, referências, requests no-tool, RAG e apresentação-only.

**Teste:** `task_decomposition_recall`, false tool calls, unnecessary follow-up, multi-request completion.

**Pronto quando:** há baseline por família e exemplos negativos.

### E2.S3 — Contrato canônico de Turn Understanding

**Fazer:** definir owner em application/domain apropriado, schema de saída e integração com estado da conversa e planner.

**Não fazer:** criar enums de intent por endpoint ou domínio novo.

**Teste:** schema validation, malformed model output, missing fields e fallback.

**Pronto quando:** consumers recebem semântica estruturada sem depender de path token.

### E2.S4 — Product/production/KPI migration

**Fazer:** substituir gradualmente gates baseados em `product_query_intent`, `production_operational_intent` e `department_kpi_rules` pelo contrato de understanding + Action Catalog.

**Não fazer:** apagar heurística antes de shadow compare.

**Teste:** semantic siblings, ambiguous KPI, product vs production, purchase vs consumption, typo e informal.

**Pronto quando:** seleção correta não depende de frase presente no JSON.

### E2.S5 — Generic intent/router migration

**Fazer:** reduzir `intent_router`, `analysis_intent_vocabulary` e vocabulários de apresentação a fast paths/config realmente úteis; deixar interpretação complexa para o contrato semântico.

**Teste:** no-tool, compare/explain/summarize, email-from-data, RAG, web intent, table/chart-only.

**Pronto quando:** generalização melhora sem regressão de latência material.

### E2.S6 — Pedidos compostos e dependências

**Fazer:** garantir que goals independentes podem paralelizar e dependentes preservam ordem; transportar referências entre subtarefas.

**Teste:** pedido com 3-4 operações + síntese final; partial failure; repeated entity; presentation-only joiners.

**Pronto quando:** `multi_request_completion_rate` e `task_decomposition_recall` atendem meta definida no baseline.

### E2.S7 — Cleanup

**Fazer:** remover predicates/lists mortas e tests presos a frases específicas; manter somente fast paths justificados.

**Não fazer:** remover datasets de regressão úteis.

**Pronto quando:** code search não encontra decisão crítica dependente dos catálogos aposentados.

## Invariantes

- Código de produto/data/número explícito pode continuar com parser determinístico como hint.
- Parser determinístico não decide sozinho action quando houver ambiguidade semântica.
- Turn Understanding não pode selecionar action arbitrária; action choice continua no retrieval/planner autorizado.
- No-tool deve permanecer possível.

## Aceite

```text
LONG_COMPOUND_REQUEST = PASS
TYPO_SYNONYM_GENERALIZATION = PASS
NO_TOOL = PASS
SEMANTIC_SIBLINGS = PASS
NO_ENDPOINT_INTENT_ENUM = PASS
R1_R2_R6_R9_R11 = PASS
```
