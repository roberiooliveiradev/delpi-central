# Programas de máquina (Manutenção) — ranking de intermediários

Rota usada pelo submódulo **Programas de máquina** do plugin Manutenção (via `maintenance-api`).

## Endpoint

`GET /production/machine-programs/top-intermediates`

| operationId | Shape | Entity |
|-------------|-------|--------|
| `list_production_machine_program_top_intermediates` | `paged_list` | `production_machine_program_intermediate` |

### Query params

| Param | Obrigatório | Descrição |
|-------|-------------|-----------|
| `branch` | sim | Filial TOTVS (`01` / `02`) |
| `date_start` | não | Início do período (YYYY-MM-DD). Default: ~6 meses atrás |
| `date_end` | não | Fim inclusivo. Default: hoje |
| `page` | não | Página (default 1) |
| `page_size` | não | Tamanho (default 10, máx 100) |
| `search` | não | Filtro em código PI ou PA |

### Item (`data.items[]`)

| Campo | Origem |
|-------|--------|
| `intermediate_code` | `H6_PRODUTO` (`B1_TIPO = PI`) |
| `intermediate_description` | `SB1.B1_DESC` |
| `finished_product_code` | OP mãe `LEFT(H6_OP,6)+01001` → `SC2.C2_PRODUTO` (modo: PA mais frequente) |
| `cutting_work_center` | `SG2.G2_CTRAB` com `G2_OPERAC = 01` |
| `has_open_production_order` | `SC2` do PI com saldo (`C2_QUANT > C2_QUJE`, `C2_DATRF` vazio) |
| `qty_produced` | `SUM(H6_QTDPROD)` |
| `appointment_count` | quantidade de apontamentos no período |

### Regras

- Apontamentos: `SH6010`, `H6_TIPO = 'P'`, período em `H6_DTAPONT`
- Intermediário: `B1_TIPO = 'PI'` e código iniciando com `5` (`H6_PRODUTO LIKE '5%'`)
- Exclui CT de corte `CT-02A` (roteiro SG2 operação 01)
- **Top 100** mais produzidos no período (`summary.top_limit = 100`; `total` nunca ultrapassa 100)
- Cache: namespace `production-machine-programs-top-intermediates` (TTL do `query_cache`)
- Permissão: `api-delpi.access`

### Exemplo

```http
GET /production/machine-programs/top-intermediates?branch=01&page=1&page_size=10
Authorization: Bearer <jwt>
```
