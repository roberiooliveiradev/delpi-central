# Faixa válida de eficiência na produção (0–199%)

Regra única para **OEE** (`H6_ZEFICI` / SH6010) e **Eficiência Fabril** (`EFICIENCIA_PERCENTUAL` / view `vw_Apontamentos_Eficiencia`).

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

## Constantes (fonte de verdade)

### API (`api-delpi`)

| Símbolo | Arquivo | Valor |
|---------|---------|-------|
| `PRODUCTION_EFFICIENCY_VALID_MIN_PCT` | `app/domain/production/production_efficiency_valid_range.py` | `0` |
| `PRODUCTION_EFFICIENCY_VALID_MAX_PCT` | idem | `199` |
| `is_valid_production_efficiency_pct()` | idem | helper Python |

Consumidores:

| Módulo | Uso |
|--------|-----|
| `production_fabril_appointment_scope.py` | View, CTs excluídos, `STATUS_REGISTRO_OK` |
| `production_fabril_appointment_filters.py` | `build_fabril_view_filters()` — usado por eficiência fabril **e** OEE |
| `production_fabril_efficiency_sql.py` | `status` valid/outlier em `EFICIENCIA_PERCENTUAL` |
| `production_fabril_oee_sql.py` | Listagem OEE (view + `appointment_id` via SH6010) |

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
- **Métrica do painel:** `EFICIENCIA_PERCENTUAL` (média simples na faixa 0–199%).
- Detalhe: `GET /production/oee/appointments/{id}` — ainda SH6010 (`H6_ZEFICI`, roteiro, tempos).

### Eficiência Fabril — `GET /production/eficiencia-fabril/*`

- **Dashboard** (`/dashboard`): summary e charts aplicam cap 0–199 via repositório.
- **Appointments** (`/appointments`): retorna todos os registros do período; o MFE filtra localmente para KPIs.
- Tabela: linha vermelha + badge **Verificar** se `isProductionEfficiencyOutlier(eficiencia_percentual)`.

## Testes

```bash
cd api-delpi
pytest tests/test_production_efficiency_valid_range.py -q
pytest tests/test_get_eficiencia_fabril_dashboard_use_case.py -q
```

## Documentação relacionada

- [06-modulos-departamentais.md](./06-modulos-departamentais.md) — rotas `/production/oee` e eficiência fabril
- [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/)
- `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md` — filtro `status` do OEE

## Alterar a faixa no futuro

1. Atualizar **apenas** `production_efficiency_valid_range.py` e espelhar em `businessRules.ts` (eficiência fabril **e** dashboard-production).
2. Rodar testes de OEE e eficiência fabril.
3. Atualizar este documento e as specs em `docs/12-roadmap-e-evolucao/eficiencia-fabril/`.
4. Revisar vocabulário do chat (`presentation_profiles.json`, `external_action_responses.json`) se textos citarem a faixa.
