# E2.S2 — Baseline de entendimento (authority vs shadow TU)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** C (plano 02)  
**Harness:** `tests/unit/domain/services/test_e2_s2_understanding_baseline.py` (5 passed)

## Veredito

```text
BASELINE_CORPUS_FAMILIES = PASS
AUTHORITY_INTENT_FROZEN = PASS
SHADOW_TU_FROZEN = PASS
COMPOUND_DECOMPOSITION_RECALL = PASS
NO_TOOL_NEGATIVE = PASS
TYPO_SIBLING_STOCK = PASS
TU_NOT_AUTHORITY = PASS
```

## Famílias congeladas

| Family | Mensagem (resumo) | Authority intent/sub | Product | Production | TU subtasks |
|--------|-------------------|----------------------|---------|------------|-------------|
| stock_short | estoque 10080001 | operational_query/stock_lookup | stock | — | 1 lookup |
| stock_typo | estoqe 10080001 | idem | stock | — | 1 lookup |
| synonym_balance | saldo disponível | stock_lookup | stock | — | 1 unknown |
| compound_enum | 3 itens numerados | mixed_task/operational_then_text | multi_scope | — | 3 |
| compound_semi | `;` join | operational_query/supplier_lookup | multi_scope | — | 2 |
| no_tool_smalltalk | oi | small_talk / requiresTool=false | full | — | 1 |
| presentation_table | em tabela | follow_up/format_refinement | full | — | 1 |
| rag_policy | política de compras | rag_question | full | — | 1 |
| production_schedule | programação de produção hoje | schedule_today_lookup | full | SCHEDULE_TODAY | 1 |
| compare_insight | compara estoque mês | analysis + is_compare | stock | — | 1 reasoning |

## Notas de drift observável (não corrigir neste freeze)

- `compound_semi`: authority classifica `supplier_lookup` (último foco) enquanto TU já split em 2 goals — candidato natural a promoção TU (E2.S4+).
- `production_schedule`: phrasing “agenda de produção” **não** resolve kind; baseline usa “programação de produção hoje”.
- TU types ainda ruidosos (`unknown`) em vários casos — contrato canônico = E2.S3.

## Invariante

Turn Understanding permanece **shadow**; authority = intent_router + product/production/analysis heuristics.

## Próximo

**E2.S3** — contrato canônico de Turn Understanding (schema/DTO + consumers sem path token).
