# Lookups canônicos (E17) — inventário e contrato

Objetivo: `requests-api` **não** depende de paths `/invoice-issuance/*` na api-delpi.  
Rotas legadas `/invoice-issuance/parties|…` permanecem até E18 (soak).

## Inventário atual (`ApiDelpiAdapter`)

| Método port | Path legado api-delpi | `operationId` legado | Shape |
|-------------|----------------------|----------------------|-------|
| `search_parties` | `GET /invoice-issuance/parties` | `search_invoice_issuance_parties` | paged_list / party |
| `search_products` | `GET /invoice-issuance/products` | `search_invoice_issuance_products` | paged_list / product |
| `search_carriers` | `GET /invoice-issuance/carriers` | `search_invoice_issuance_carriers` | paged_list / carrier |
| `list_open_sales_orders` | `GET /invoice-issuance/open-sales-orders` | `list_invoice_issuance_open_sales_orders` | paged_list |
| `get_warehouse_01_balance` | `GET /invoice-issuance/products/{code}/warehouse-01-balance` | `get_invoice_issuance_warehouse_01_balance` | scalar |

Código: [`api_delpi_adapter.py`](../../../requests-api/requests_app/infrastructure/gateways/api_delpi_adapter.py)  
Exposição MFE: `GET /apps/requests-api/v1/request-types/invoice-issuance/lookups/*` (inalterado no browser — nunca api-delpi direto).

## Contrato canônico (pós-E17)

| Método port | Path canônico api-delpi | `operationId` |
|-------------|-------------------------|---------------|
| `search_parties` | `GET /request-lookups/parties` | `search_request_lookup_parties` |
| `search_products` | `GET /request-lookups/products` | `search_request_lookup_products` |
| `search_carriers` | `GET /request-lookups/carriers` | `search_request_lookup_carriers` |
| `list_open_sales_orders` | `GET /request-lookups/open-sales-orders` | `list_request_lookup_open_sales_orders` |
| `get_warehouse_01_balance` | `GET /request-lookups/products/{code}/warehouse-01-balance` | `get_request_lookup_warehouse_01_balance` |

- **Mesmos** use cases TOTVS (SA1/SA2/SB1/SB2/SA4 / OV) do módulo invoice-issuance.
- Permissões: `invoice-issuance.create|process|manage` **ou** `my-requests.invoice-issuance.create|process` / `my-requests.manage`.
- Entity/shape nos contratos: reutilizam as entidades `invoice_issuance_*` (mesmo payload) para não quebrar golden/parity.

## Gate de regressão

- `pytest requests-api/tests/parity/ -q` (shapes via `InMemoryOperationalLookupAdapter`)
- Testes unitários do adapter apontando paths `/request-lookups/…`
- Smoke api-delpi: `operationId` novos citados em `tests/`

## Fora deste doc (E18+)

- Remover ou marcar deprecated as rotas lookup sob `/invoice-issuance/`
- DROP schema / volume após retenção
