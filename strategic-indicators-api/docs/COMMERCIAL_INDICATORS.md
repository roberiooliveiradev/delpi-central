# Departamento Comercial — catálogo e medições

**Última atualização:** 2026-05-27  
**Migrations:** `V015`, `V024`, `V026`

## Modelo atual (por unidade)

| Campo | Valor |
|-------|--------|
| `aggregation_mode` | `average_of_units` — IDD do departamento = média das notas das filiais 01 e 02 |
| ROL | Um indicador `commercial-rol` (`per_unit`), metas por filial em `goal_scope_branch` `01` / `02` |
| Demais KPIs | `per_unit` com `source_key` e metas por filial |

**Inativos:** `commercial-rol-matrix`, `commercial-rol-branch` (substituídos por `commercial-rol`).

## Indicadores ativos

| ID | Nome | Peso | Escopo | Meta | `source_key` | Medição |
|----|------|------|--------|------|--------------|---------|
| `commercial-rol` | ROL | 40% | `per_unit` | Curva R$ por filial | `commercial_rol` | TOTVS: filial 01 = matriz, 02 = filial |
| `commercial-closing-rate` | Taxa de Fechamento | 15% | `per_unit` | Padrão % | `commercial_sales_conversion_rate` | Propostas ganhas / total |
| `commercial-sales-order-otd` | OTD Pedidos de Venda | 30% | `per_unit` | Padrão 95% | `commercial_sales_order_otd` | `SC6010` + `SC5010` |
| `commercial-new-business-rol` | % ROL Novos Negócios | 15% | `per_unit` | Curva % | `commercial_new_business_rol_pct` | ROL não-WEG / ROL total |

## Medições no SI (`CommercialIndicatorsSnapshotProvider`)

- **ROL:** `unit_values["01"]` e `unit_values["02"]` (sem indicadores separados matriz/filial).
- **Demais:** `unit_values` por filial quando a visão é consolidada; valor único quando `branch=01|02` na leitura.
- Visão **Consolidado:** nota de cada indicador = média das notas 01 e 02 (com metas por filial).
- Visão **Filial 01/02:** meta estrita no escopo; realizado da unidade correspondente.

## Dashboard Comercial (`plugins/dashboard-commercial`)

Rotas api-delpi (metas via `commercial_rol` + filial):

| KPI na UI | Rota | Meta SI |
|-----------|------|---------|
| ROL Matriz (01) | `GET /commercial/head_office_rol_target_pct` | `commercial_rol`, `branch=01` |
| ROL Filial (02) | `GET /commercial/branch_rol_target_pct` | `commercial_rol`, `branch=02` |
| Conversão / OTD / % novos | rotas com `branch` opcional | `source_key` do indicador + `branch` |

Chaves legadas `commercial_head_office_rol_target` / `commercial_branch_rol_target` ainda resolvem para `commercial-rol` na API de metas do SI.

## Rotas de dados (strategic-indicators-api / api-delpi)

- `GET /commercial/sales-order-otd?start_date=&end_date=&branch=`
- `GET /commercial/new-business-rol-pct?start_date=&end_date=&branch=`
- `GET /commercial/closing-rate?start_date=&end_date=&branch=`

Após alterar catálogo ou metas: `scripts/refresh_period_scores.py` na competência afetada.
