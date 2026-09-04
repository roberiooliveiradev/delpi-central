# Paginação HTTP — api-delpi

Fonte canônica de **defaults, caps e envelopes** de paginação na api-delpi.

> Chat (`minha-delpi-ai-api`) tem catálogo próprio (`operational_pagination.json`) só para **outbound** de tools.  
> Esta página cobre **inbound Query + outbound envelope** da api-delpi. Não misturar as duas fontes.

## Núcleo

| Peça | Onde |
|------|------|
| Catálogo de tiers | `app/content/pagination_tiers.json` |
| Clamp / get | `PaginationTierService` (`app/domain/services/pagination_tier_service.py`) |
| Factories FastAPI | `PAGE_SIZE_QUERY` / `LIMIT_QUERY` / `TOP_LIMIT_QUERY` / `HISTORY_LIMIT_QUERY` em `app/interface/http/pagination_query.py` |
| Envelope de resposta | `PaginationEnvelopeBuilder` (`paged_count` \| `overfetch` \| `has_next` \| `full_tree`) |
| Offset TOTVS | `totvs.pagination.paginate(..., max_page_size=, tier_id=)` |
| Inventário | `pagination_inbound_inventory.json` / `pagination_outbound_inventory.json` · [pagination-inventory.md](../pagination-inventory.md) |
| Gate CI | `python scripts/audit_pagination_tiers.py --check-complete` |

## Rota nova = tier

1. Escolher um tier existente em `pagination_tiers.json` (não inventar `Query(50, le=…)` inline).
2. Se o contrato for novo (default/cap distintos), **adicionar tier nomeado** no JSON + teste no `PaginationTierService`.
3. No router: `page_size: int = PAGE_SIZE_QUERY("page_50_500")` (ou `LIMIT_QUERY` / etc.).
4. No use case / DTO: montar `"pagination"` só via `PaginationEnvelopeBuilder` (ou adapter fino já existente).
5. Rodar `scripts/audit_pagination_tiers.py --check-complete`.

## Shapes de envelope

| Shape | Quando |
|-------|--------|
| `paged_count` | page / page_size / total / total_pages / is_complete |
| `overfetch` | limit / offset / returned / is_complete (TOP N+1) |
| `has_next` | page / page_size / is_complete sem total conhecido |
| `full_tree` | árvore completa (structure/parents omitidos) |

Extras de contrato legado (`has_more`, `total_items`, …) vão em `extra=` ou `{**builder(...), ...}` — não recriar dict ad hoc.

## Anti-padrões

- `Query(50, ge=1, le=500)` literal no router
- `"pagination": { "page": … }` fora do builder
- `DEFAULT_PAGE_SIZE = 50` local sem apontar ao tier
- Unificar todos os `le` para 500 sem decisão de contrato
- Domain importar FastAPI

## Ownership vs chat

| Camada | Responsabilidade |
|--------|------------------|
| api-delpi | Contrato HTTP real (Query + envelope) |
| minha-delpi-ai-api | Defaults de tool quando monta params para a api-delpi (`operational_pagination.json`) |

Hierárquico no chat usa **500**; na api-delpi, `page_optional_500` / omitir `page_size` em structure/parents permanece full tree.
