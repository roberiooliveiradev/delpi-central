# Faixa válida de eficiência na produção (0–199%)

Regra única para **OEE** e **Eficiência Fabril** — eficiência calculada como **(tempo previsto ÷ tempo real) × 100** (`EFICIENCIA_PERCENTUAL` na view `vw_Apontamentos_Eficiencia`; no detalhe SH6010, via roteiro e horários do apontamento).

## Objetivo

Apontamentos com eficiência fora da faixa **0–199%** são tratados como **outliers** (erro de apontamento ou dado inconsistente). Eles:

- **permanecem listáveis** na tabela (conferência operacional);
- **não entram** em médias, KPIs, gráficos nem exportações agregadas;
- na UI da Eficiência Fabril aparecem com status **Verificar**;
- na listagem OEE usam `status=outlier` (filtro `valid` / `outlier`).

A faixa **não** vem de documentação formal do Protheus — é convenção operacional da plataforma DELPI, alinhada entre os dois indicadores desde jun/2026.

## Histórico

| Data | Mudança |
|------|---------|
| Mar/2026 | KPI OEE nasceu com teto **0–299%** (`overall_equipment_effectiveness_repository.py`). |
| Abr/2026 | OEE alterado para **0–199%** (commit `30cb0c36`). |
| Mai/2026 | Eficiência Fabril MVP usava teto **250%** (`max_efficiency_indicator_pct`). |
| Jun/2026 | Faixa unificada em **0–199%** para OEE e Eficiência Fabril; constante compartilhada na API. |
| Jun/2026 | Eficiência passa a ser **só por tempos** (fim de `H6_ZEFICI`); fórmulas legíveis em `time_analysis`; auto-refresh 5 min nos dashboards — ver [producao-eficiencia-changelog-jun2026.md](./producao-eficiencia-changelog-jun2026.md). |

## Constantes (fonte de verdade)

### API (`api-delpi`)

| Símbolo | Arquivo | Valor |
|---------|---------|-------|
| `PRODUCTION_EFFICIENCY_VALID_MIN_PCT` | `app/domain/production/production_efficiency_valid_range.py` | `0` |
| `PRODUCTION_EFFICIENCY_VALID_MAX_PCT` | idem | `199` |
| `is_valid_production_efficiency_pct()` | idem | helper Python |
| `PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD` | idem | `50` — alerta operacional de baixa eficiência |
| `is_low_production_efficiency_pct()` | idem | `true` se na faixa válida e `< 50%` |

Consumidores:

| Módulo | Uso |
|--------|-----|
| `production_fabril_appointment_scope.py` | View, CTs excluídos, `STATUS_REGISTRO_OK` |
| `production_fabril_appointment_filters.py` | `build_fabril_view_filters()` — usado por eficiência fabril **e** OEE |
| `production_fabril_efficiency_sql.py` | `status` valid/outlier em `EFICIENCIA_PERCENTUAL` |
| `production_fabril_oee_sql.py` | Listagem OEE (view + `appointment_id` via SH6010) |
| `production_fabril_ef_items_sql.py` | Listagem eficiência fabril com `appointment_id` |
| `production_fabril_sh6010_apply.py` | `OUTER APPLY` view → SH6010 (compartilhado OEE + EF) |
| `production_appointment_time_analysis.py` | Diagnóstico `time_analysis.findings` no detalhe do apontamento |

### MFE Eficiência Fabril

| Símbolo | Arquivo | Valor |
|---------|---------|-------|
| `PRODUCTION_EFFICIENCY_VALID_MIN_PCT` | `plugins/eficiencia-fabril/src/constants/businessRules.ts` | `0` |
| `PRODUCTION_EFFICIENCY_VALID_MAX_PCT` | idem | `199` |
| `VERIFY_EFFICIENCY_THRESHOLD_PCT` | idem | `199` (alias do máximo) |
| `isProductionEfficiencyOutlier()` | idem | `true` se fora de 0–199 |

### MFE Dashboard Produção (OEE)

| Símbolo | Arquivo | Valor |
|---------|---------|-------|
| `PRODUCTION_EFFICIENCY_VALID_*_PCT` | `plugins/dashboard-production/src/constants/businessRules.ts` | `0` / `199` |
| `isProductionEfficiencyOutlier()` | idem | faixa 0–199 |
| `isOeeAppointmentOutlier()` | idem | usa `status` da API ou `oee_pct` |

- Listagem: `DataTableSection` em `OeePage.tsx` — colunas no padrão eficiência fabril, com busca, ordenação server-side e badges **Verificar** / **OK**.
- KPIs e aviso na página: `OeePage.tsx`.

## Comportamento por superfície

### OEE — `GET /production/oee`

- **Mesmo escopo** da eficiência fabril: view `vw_Apontamentos_Eficiencia`, `STATUS_REGISTRO = OK`, CTs excluídos.
- **Métrica do painel:** `EFICIENCIA_PERCENTUAL` — média simples na faixa 0–199% (tempo previsto ÷ tempo real).
- Detalhe: `GET /production/oee/appointments/{id}` — SH6010 com roteiro, tempos e eficiência calculada pelos mesmos critérios.
- Campos `time_analysis.formula_*`: textos em linguagem operacional (sem códigos Protheus) — ver changelog jun/2026.

### Eficiência Fabril — `GET /production/eficiencia-fabril/*`

- Listagem inclui `appointment_id` (vínculo SH6010 via `production_fabril_sh6010_apply`) para abrir detalhe.
- Detalhe na UI: `GET /production/oee/appointments/{appointment_id}` (roteiro SG2, estrutura BOM, tempos, `findings` de alertas).

- **Dashboard** (`/dashboard`): summary e charts aplicam cap 0–199 via repositório.
- **Appointments** (`/appointments`): retorna todos os registros do período; o MFE filtra localmente para KPIs.
- Tabela: linha vermelha + badge **Verificar** se `isProductionEfficiencyOutlier(eficiencia_percentual)`.
- Tabela: linha âmbar + badge **Eficiência baixa** se eficiência na faixa válida e `< 50%` (`isProductionEfficiencyLow`).
- Clique na linha → `/apps/eficiencia-fabril/{sc|es}/appointment/{id}`; API de detalhe: `GET /production/oee/appointments/{id}` com `time_analysis.findings` (inclui `low_efficiency_reported` e diagnóstico de motivo).

## Testes

```bash
cd api-delpi
pytest tests/test_production_efficiency_valid_range.py tests/test_production_fabril_appointment_filters.py tests/test_production_appointment_time_analysis.py -q
pytest tests/test_get_eficiencia_fabril_dashboard_use_case.py -q
```

## Documentação relacionada

- [06-modulos-departamentais.md](./06-modulos-departamentais.md) — rotas `/production/oee` e eficiência fabril
- [producao-eficiencia-changelog-jun2026.md](./producao-eficiencia-changelog-jun2026.md) — eficiência por tempos, fórmulas legíveis, auto-refresh
- [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/)
- `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md` — filtro `status` do OEE

## Alterar a faixa no futuro

1. Atualizar **apenas** `production_efficiency_valid_range.py` e espelhar em `businessRules.ts` (eficiência fabril **e** dashboard-production).
2. Rodar testes de OEE e eficiência fabril.
3. Atualizar este documento e as specs em `docs/12-roadmap-e-evolucao/eficiencia-fabril/`.
4. Revisar vocabulário do chat (`presentation_profiles.json`, `external_action_responses.json`) se textos citarem a faixa.
