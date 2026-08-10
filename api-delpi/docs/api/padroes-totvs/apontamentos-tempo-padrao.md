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
SQL: `production_fabril_ef_items_sql.py`, `production_oee_sql.py`.

## O que NÃO fazer

- `TEMPO_PREVISTO = HY_TEMPOM × (H6_QTDPROD / C2_QUANT)` (legado da view) — % cai artificialmente em OP parcial.
- `META = C2_QUANT / HY_TEMPOM` ou `QTD_OP / HY_TEMPOM` com TEMPOM residual.
- Confiar no `EFICIENCIA_PERCENTUAL` cru da view `vw_Apontamentos_Eficiencia` no KPI do dashboard — a API **recalcula** no SELECT de appointments.

## Incidente

Ago/2026: Meta/hora 1099 correta (`1/TEMPAD`), mas eficiência ~29% porque o card usava o % da view (previsto com TEMPOM parcial).
