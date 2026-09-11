# Plano 02 — NLU manual -> Turn Understanding + planner estruturado

**Prioridade:** P0  
**Status execução:** Onda C · E2.S1–S7 **ATENDIDO_PARCIAL** (S1–S5 cutovers; S6 harness; S7 JUSTIFIED_KEEP) · Onda C **ATENDIDO_PARCIAL**  
**Evidência:** [`../evidence/e2-s1-heuristic-intent-inventory.md`](../evidence/e2-s1-heuristic-intent-inventory.md) · [`../evidence/e2-s2-understanding-baseline.md`](../evidence/e2-s2-understanding-baseline.md) · [`../evidence/e2-s3-turn-understanding-contract.md`](../evidence/e2-s3-turn-understanding-contract.md) · [`../evidence/e2-s4-authority-shadow.md`](../evidence/e2-s4-authority-shadow.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
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

### E2.S1 — Inventário das árvores heurísticas — **ATENDIDO** (2026-09-10)

**Fazer:** mapear cada `terms/excludeTerms/regex/predicate/pipeline` e o consumer que altera routing, args, presentation ou fast-path.

**Feito:** matriz bundle→classe→consumers em [`../evidence/e2-s1-heuristic-intent-inventory.md`](../evidence/e2-s1-heuristic-intent-inventory.md) (complementa Onda A §6). Sem migração de runtime.

### E2.S2 — Baseline de entendimento — **ATENDIDO** (2026-09-10)

**Fazer:** corpus com requests curtos/longos, 2-4 goals, typos, sinônimos, no-tool, RAG e apresentação-only.

**Feito:** harness `test_e2_s2_understanding_baseline.py` congela authority + shadow TU por família. Evidência: [`../evidence/e2-s2-understanding-baseline.md`](../evidence/e2-s2-understanding-baseline.md).

### E2.S3 — Contrato canônico de Turn Understanding — **ATENDIDO** (2026-09-10)

**Fazer:** definir owner em application/domain apropriado, schema de saída e integração com estado da conversa e planner.

**Feito:** entity + `TURN_UNDERSTANDING_JSON_SCHEMA` + validator/fallback; `analyze` emite contrato validado com `goals`/`entities`/`presentationIntent`/`needsTool`; sem path tokens. Evidência: [`../evidence/e2-s3-turn-understanding-contract.md`](../evidence/e2-s3-turn-understanding-contract.md).

### E2.S4 — Product/production/KPI migration — **MAPPER_FIRST_ALL_FAMILIES** (2026-09-10)

**Fazer:** substituir gradualmente gates… / **Não fazer:** apagar heurística antes de shadow compare.

**Feito:** shadow + dials; product/production/KPI **mapper-first + fallback**. Evidência: [`../evidence/e2-s4-authority-shadow.md`](../evidence/e2-s4-authority-shadow.md).

### E2.S5 — Generic intent/router migration — **CUTOVER_GENERIC_SLICE** (2026-09-10)

**Feito:** dials `no_tool` / `presentation` / `compare_explain` + mapper + overlay em `ChatIntentRouterService.classify`. Sem DELETE de JSON. Evidência: [`../evidence/e2-s5-generic-intent-router.md`](../evidence/e2-s5-generic-intent-router.md).

**Pendente (full):** cascade ClassifyService completo; analysis multi-consumer.

### E2.S6 — Pedidos compostos e dependências — **ATENDIDO_PARCIAL** (2026-09-10)

**Feito:** harness dependsOn/ordem/parallel via TU→TaskPlanner. Evidência: [`../evidence/e2-s6-compound-depends.md`](../evidence/e2-s6-compound-depends.md).

**Pendente:** `taskPlannerEnabled` ON + métricas live.

### E2.S7 — Cleanup — **JUSTIFIED_KEEP** (2026-09-10)

**Feito:** gates atualizados; major heuristics KEEP. Evidência: [`../evidence/e2-s7-cleanup-gates.md`](../evidence/e2-s7-cleanup-gates.md).

**Não feito:** DELETE de catálogos (BLOCKED até gates full).

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
