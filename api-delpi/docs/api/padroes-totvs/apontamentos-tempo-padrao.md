# Tempo padrão e eficiência (apontamentos SHY / SH6)

## Princípio

Ritmo unitário estável da OP = **`HY_TEMPAD`** (horas por unidade no snapshot `SHY010`).
**Não** derivar previsto ou meta de `HY_TEMPOM` sem normalizar — `HY_TEMPOM = HY_TEMPAD × HY_QUANT` e `HY_QUANT` encolhe com apontamento parcial.

## O que fazer

| Necessidade | Fórmula |
|-------------|---------|
| Meta/hora | `1 / HY_TEMPAD` |
| Tempo previsto | `SETUP + HY_TEMPAD × QTD_APONTADA` |
| Eficiência % | `TEMPO_PREVISTO / TEMPO_REAL × 100` |
| Fallback ritmo | `HY_TEMPOM / HY_QUANT`; depois `G2_TEMPAD` |

Constantes / domínio: `app/domain/production/production_meta_por_hora.py`, `production_tempo_previsto.py`, `production_standard_time.py`.
SQL canônico (único): `production_fabril_efficiency_sql.py` + joins `production_fabril_standard_time_sql.py`.
Consumidores: listagem EF (`production_fabril_ef_items_sql.py`), KPI/listagem OEE (`production_fabril_oee_kpi_sql.py`, `production_fabril_oee_sql.py`), detalhe SH6010 (`production_oee_sql.py`), tempo padrão por OP/operação (`production_standard_time_sql.py`).

## Leitura S2S — ciclo por peça física (MES)

`GET /production/orders/{production_order}/operations/{operation_code}/standard-time?branch=01`
(`operationId`: `get_production_operation_standard_time`, interna — `X-Delpi-Service-Token` válido, sem JWT humano).

Resolve **uma** operação de uma OP: `SC2010` (produto, unidade `C2_UM`, roteiro `C2_ROTEIRO`) + snapshot `SHY010` + roteiro `SG2010`. Não depende de `vw_Apontamentos_Eficiencia` nem de apontamento SH6 — funciona antes do primeiro apontamento.

| Campo | Regra |
|-------|-------|
| `standard_time_unit_hours` | `SHY.HY_TEMPAD` → `SHY.HY_TEMPOM / HY_QUANT` → `SG2.G2_TEMPAD` → `null` |
| `standard_time_source` | `shy_tempad` / `shy_tempom_quant` / `sg2_tempad` / `unavailable` |
| `ideal_cycle_seconds` | `unit_hours × 3600 ÷ piecesFactor` (`production_operational_units.json` — MI ÷1000); **segundos por peça física**, pensado para MES/Pulse |
| `setup_seconds` | `COALESCE(SHY.HY_SETUP, SG2.G2_SETUP, 0) × 3600` — separado do ciclo |
| `data_quality` | `complete` / `standard_time_unavailable` / `piece_conversion_unavailable` (unidade sem `piecesFactor`, ex.: MT) |

OP ou operação inexistente → `404`; operação existente sem tempo padrão → `200` com `data_quality=standard_time_unavailable`. Leitura apenas — nenhuma escrita no TOTVS.

## O que NÃO fazer

- `TEMPO_PREVISTO = HY_TEMPOM × (H6_QTDPROD / C2_QUANT)` (legado da view) — % cai artificialmente em OP parcial.
- `META = C2_QUANT / HY_TEMPOM` ou `QTD_OP / HY_TEMPOM` com TEMPOM residual.
- Confiar no `EFICIENCIA_PERCENTUAL` cru da view `vw_Apontamentos_Eficiencia` no KPI OEE, SI ou eficiência fabril — a API **recalcula** com `HY_TEMPAD × qtd`.
- Duplicar a expressão de previsto/% em um novo módulo SQL — estender `production_fabril_efficiency_sql.py`.

## Incidente

Ago/2026: Meta/hora 1099 correta (`1/TEMPAD`), mas eficiência ~29% porque o card usava o % da view (previsto com TEMPOM parcial).
Ago/2026: Dashboard Produção / Strategic Indicators (OEE 88,31%) divergiam da Eficiência Fabril (89,5%) no mesmo mês — KPI OEE ainda fazia `AVG` do % cru da view; alinhado ao SQL canônico TEMPAD.