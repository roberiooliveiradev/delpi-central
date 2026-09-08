# Lookups canônicos (E17–E18) — inventário e contrato

**Status:** E18 entregue — lookups legado `/invoice-issuance/*` **removidos**.  
Canônico único: `GET /request-lookups/*` (`ApiDelpiAdapter` + router api-delpi).

## Inventário legado (removido em E18)

| Método port | Path legado (removido) | `operationId` legado (removido) |
|-------------|------------------------|----------------------------------|
| `search_parties` | `GET /invoice-issuance/parties` | `search_invoice_issuance_parties` |
| `search_products` | `GET /invoice-issuance/products` | `search_invoice_issuance_products` |
| `search_carriers` | `GET /invoice-issuance/carriers` | `search_invoice_issuance_carriers` |
| `list_open_sales_orders` | `GET /invoice-issuance/open-sales-orders` | `list_invoice_issuance_open_sales_orders` |
| `get_warehouse_01_balance` | `GET /invoice-issuance/products/{code}/warehouse-01-balance` | `get_invoice_issuance_warehouse_01_balance` |

Código canônico: [`api_delpi_adapter.py`](../../../requests-api/requests_app/infrastructure/gateways/api_delpi_adapter.py) (`_LOOKUP_PREFIX = "/request-lookups"`).  
Router: [`request_lookups_router.py`](../../../api-delpi/app/interface/http/routes/request_lookups_router.py).  
Exposição MFE: `GET /apps/requests-api/v1/request-types/invoice-issuance/lookups/*` (inalterado no browser — nunca api-delpi direto).

## Contrato canônico (ativo)

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
- `pytest requests-api/tests/test_api_delpi_adapter_lookups_paths.py -q` — zero path `/invoice-issuance/` nos lookups
- `pytest api-delpi/tests/test_request_lookups_routes.py tests/test_invoice_issuance_contracts.py -q`

## Fora deste doc

- DROP schema `invoice_issuance` / volume host após retenção ([MIGRATION-RUNBOOK.md](./MIGRATION-RUNBOOK.md))
