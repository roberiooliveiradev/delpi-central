# E3.S2 — Baseline de follow-up / refinement / referência

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** D (plano 03)  
**Harness:** `tests/unit/domain/services/test_e3_s2_follow_up_baseline.py` (5 passed)

## Veredito

```text
BASELINE_FOLLOW_UP_FAMILIES = PASS
SHIPPING_SEGMENT_AUTHORITY = PASS
PAGINATION_DELTA_FROZEN = PASS
GROUP_BY_PATH_COUPLING_FROZEN = PASS
ORDINAL_RESOLVE_STRUCTURED = PASS
AMBIGUITY_COMPARE_PREVIOUS = PASS
NO_CUTOVER = PASS
```

## Famílias congeladas

| Family | Mensagem | Sinais HEAD (authority) |
|--------|----------|-------------------------|
| shipping_followup | e a expedição? | `routeSegment=shipping-status`, `followUpType=shipping`, playbook date gate |
| branch_filter | agora só filial 02 | `stock_refinement` branch=02 sobre lastAction stock |
| next_page | próxima página | `pagination_refinement` page=2 |
| page_size_100 | traga 100 linhas | `pagination_refinement` page_size=100 |
| group_by_branch | agrupe por filial | `operational_group_by_refinement` group_by=`branch_summary` **só** com path `/production/consumption/top-items` |
| compare_month | compare com o mês anterior | intent `text_task`/`compare`, followUpType `entity_reuse` |
| same_product | use o mesmo produto | `product_lookup` (sem refinement estruturado ainda) |
| topic_switch_rag | política de férias | `rag_question` (troca de domínio) |
| ordinal_resolve | estoque do segundo | resolve code `10080002` via `resultSets` |
| ambiguous_compare_previous | compare com o anterior | `detect_ambiguity` reason=`compare_previous` com 2+ códigos |

## Casos irmão / negativo

- Shipping sibling: `should_block_semantic_fallback("e a expedição?")` = true.
- Group-by negativo: mesma frase sobre stock path → lista vazia (acoplamento `pathContains`).
- Ordinal negativo: sem `resultSets` → códigos vazios.

## Notas de drift observável (não corrigir neste freeze)

- `next_page` cai em `llm_general` no intent router — paginação é refinement, não intent.
- `page_size_100` classifica `product_search` enquanto o delta útil é pagination.
- `same_product` não emite refinement estruturado; continuidade depende de focus/lastAction downstream.
- Group-by “filial” no corpus do plano só ativa com action de consumo produção — confirma authority `pathContains`.

## Invariante

Sem cutover de `operational_follow_up_routing` / group_by / parameter binder. Baseline mede R3/R6–R9 sinais atuais para comparação futura (E3.S3+).

## Próximo

**E3.S3** — contrato canônico de refinement (argument delta / presentation delta / clarification).
