# Produção — horas improdutivas

Consultas de **horas improdutivas / paradas PCP** alimentadas pela view TOTVS `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS` (inclui `DESCRICAO_MOTIVO`).

**Não confundir** com [`/retrabalhos/*`](./controle-retrabalhos.md), que usa a **mesma view** filtrada em `MOTIVO = RT` (retrabalho).

**Permissão:** `api-delpi.access` ou `dashboard-production.view` (`KPI_PRODUCTION_ACCESS`).

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10). Datas em **ISO `YYYY-MM-DD`**.

## Endpoints

| Método | Path | operationId | shape |
|--------|------|-------------|-------|
| `GET` | `/production/unproductive-hours/summary` | `get_production_unproductive_hours_summary` | `playbook_report` |
| `GET` | `/production/unproductive-hours/items` | `get_production_unproductive_hours_items` | `paged_list` |
| `GET` | `/production/unproductive-hours/ranking` | `get_production_unproductive_hours_ranking` | `list` |

## Parâmetros

| Param | Rotas | Notas |
|-------|-------|--------|
| `start_date` / `end_date` | todas | ISO `YYYY-MM-DD`; omitidos → últimos 12 meses; máx. 24 meses |
| `branch` | todas | `01` / `02`; vazio = consolidado |
| `stop_reason` | todas | Código `MOTIVO` (ex.: `RT`, `OT`); vazio = todos |
| `resource` | todas | `RECURSO` |
| `cost_center` | todas | `CENTRO_CUSTO` |
| `operator_code` | todas | `CODIGO_OPERADOR` |
| `page` / `page_size` | items | default 50, máx. 200 |
| `sort` | items | `date_desc\|date_asc\|hours_desc\|hours_asc\|cost_desc\|cost_asc` |
| `rank_by` | ranking | **obrigatório** — ver abaixo |
| `metric` | ranking | `hours` (default) \| `cost` |
| `limit` | ranking | 1–50, default 10 |

### `rank_by`

| Valor | Agrupa por |
|-------|------------|
| `stop_reason` | Motivo (+ `motivoDescricao` de `DESCRICAO_MOTIVO`) |
| `resource` | Recurso (+ centro de custo) |
| `cost_center` | Centro de custo |
| `operator` | Operador |
| `product` | Produto |
| `operation` | Operação |

## Respostas

**summary:** `periodo` + `summary` (`totalApontamentos`, `totalHoras`, `totalCusto`, `custoMedioHora`, registros/horas sem custo, destaques de recurso/operador).

**items:** `items[]` com `dataReferencia` (ISO), `motivo`, **`motivoDescricao`**, horas/custo, etc. + `pagination`.

**ranking:** `rankBy`, `metric`, `limit`, `items[]` com `rank` + campos da dimensão ativa + métricas.

## Fontes TOTVS

| Objeto | Uso |
|--------|-----|
| `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS` | Apontamentos de parada; `MOTIVO` + `DESCRICAO_MOTIVO` |

SQL: `app/infrastructure/persistence/totvs/production/unproductive_hours_sql.py`
