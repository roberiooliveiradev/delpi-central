# Intermediários compartilhados entre PAs ativos

`GET /production/shared-structure-intermediates` — `operationId` `get_production_shared_structure_intermediates`, entity `production_shared_structure_intermediates`, shape `paged_list`.

Lista intermediários (`PI`/`PA` da estrutura) que aparecem na engenharia vigente de **mais de um** produto acabado com movimentação produtiva recente. Insumo do detector «Intermediários compartilhados» da Análise de problemas do Portal PCP.

## Regra

| Decisão | Valor |
|---|---|
| PA ativo | Apontamento `SH6010`, `H6_TIPO = 'P'`, `H6_PRODUTO` = código PA (`B1_TIPO = PA`) no período |
| Período | `movement_from` (ISO) até hoje, ou `lookback_days` (default 365, máx. 730) |
| Estrutura | SG1 recursiva vigente **na data de hoje** (`G1_INI` / `G1_FIM`) |
| Intermediário | `B1_TIPO IN ('PI','PA')`, excluindo o próprio PA raiz; MP não entra |
| Compartilhado | Mesmo `component_code` em ≥ 2 PAs distintos do universo ativo |
| Exclusões PA | Códigos `8000%` e `8001%` |

## Parâmetros

| Param | Valores | Efeito |
|---|---|---|
| `branch` | `all` \| `01` \| `02` | Filial do apontamento (`H6_FILIAL`) |
| `movement_from` | `YYYY-MM-DD` | Início da janela (opcional) |
| `lookback_days` | 1–730 | Usado quando `movement_from` omitido (default 365) |
| `page` / `page_size` | 1‑based / até 200 | Paginação **por intermediário** |

## Item (`data.items[]`)

| Campo | Descrição |
|---|---|
| `intermediate_code` | Código PI/PA compartilhado |
| `intermediate_description` | `SB1.B1_DESC` |
| `intermediate_type` | `SB1.B1_TIPO` |
| `shared_pa_count` | Quantidade de PAs ativos que usam o intermediário |
| `finished_products[]` | `{ product_code, description, bom_level }` |

## Summary (`data.summary`)

| Campo | Descrição |
|---|---|
| `checked_pa_count` | PAs ativos no período |
| `shared_intermediate_count` | Intermediários compartilhados |
| `max_shared_pa_count` | Maior número de PAs por intermediário |

## Consumidor

`production-control-api` → detector `shared-structure-intermediates` → MFE `plugins/production-control`.
