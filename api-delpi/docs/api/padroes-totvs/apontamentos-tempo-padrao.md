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

Constantes / domínio: `app/domain/production/production_meta_por_hora.py`, `production_tempo_previsto.py`.  
SQL canônico (único): `production_fabril_efficiency_sql.py` + joins `production_fabril_standard_time_sql.py`.  
Consumidores: listagem EF (`production_fabril_ef_items_sql.py`), KPI/listagem OEE (`production_fabril_oee_kpi_sql.py`, `production_fabril_oee_sql.py`), detalhe SH6010 (`production_oee_sql.py`).

## O que NÃO fazer

- `TEMPO_PREVISTO = HY_TEMPOM × (H6_QTDPROD / C2_QUANT)` (legado da view) — % cai artificialmente em OP parcial.
- `META = C2_QUANT / HY_TEMPOM` ou `QTD_OP / HY_TEMPOM` com TEMPOM residual.
- Confiar no `EFICIENCIA_PERCENTUAL` cru da view `vw_Apontamentos_Eficiencia` no KPI OEE, SI ou eficiência fabril — a API **recalcula** com `HY_TEMPAD × qtd`.
- Duplicar a expressão de previsto/% em um novo módulo SQL — estender `production_fabril_efficiency_sql.py`.

## Incidente

Ago/2026: Meta/hora 1099 correta (`1/TEMPAD`), mas eficiência ~29% porque o card usava o % da view (previsto com TEMPOM parcial).  
Ago/2026: Dashboard Produção / Strategic Indicators (OEE 88,31%) divergiam da Eficiência Fabril (89,5%) no mesmo mês — KPI OEE ainda fazia `AVG` do % cru da view; alinhado ao SQL canônico TEMPAD.