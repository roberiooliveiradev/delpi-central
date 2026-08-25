# Faixa válida de eficiência na produção (0–199%)

Regra única para **OEE** e **Eficiência Fabril**. A eficiência é **(tempo previsto ÷ tempo real) × 100**, com previsto canônico:

```text
tempo_previsto = setup + HY_TEMPAD × qtd_apontada
```

(fonte SQL: `production_fabril_efficiency_sql.py`; domínio: `production_tempo_previsto.py`).  
A view `vw_Apontamentos_Eficiencia` ainda expõe `EFICIENCIA_PERCENTUAL` legado (`HY_TEMPOM` parcial) — **KPIs e listagens da API recalculam** e não usam esse valor cru. Detalhe SH6010: mesma lógica via roteiro e horários.

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
| Ago/2026 | KPI/listagem/série OEE e SI alinhados ao % canônico `HY_TEMPAD` (mesma expressão da eficiência fabril); SQL centralizado em `production_fabril_efficiency_sql.py` + `production_fabril_standard_time_sql.py`. |
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
| `production_fabril_efficiency_sql.py` | %/previsto/meta canônicos (`HY_TEMPAD`) + `status` valid/outlier |
| `production_fabril_standard_time_sql.py` | CTEs/joins SHY+SG2 compartilhados |
| `production_fabril_oee_sql.py` | Listagem OEE (view + `appointment_id` via SH6010 + % canônico) |
| `production_fabril_oee_kpi_sql.py` | KPI agregado OEE (`NOLOCK`, % canônico TEMPAD) — ver [apontamentos-tempo-padrao.md](./padroes-totvs/apontamentos-tempo-padrao.md) |
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
- **Métrica do painel:** % canônico (`setup + HY_TEMPAD × qtd` ÷ tempo real) — mesma expressão da eficiência fabril; média simples na faixa 0–199%.
- Detalhe: `GET /production/oee/appointments/{id}` — SH6010 com roteiro, tempos e eficiência calculada pelos mesmos critérios.
- Campos `time_analysis.formula_*`: textos em linguagem operacional (sem códigos Protheus) — ver changelog jun/2026.
### Eficiência Fabril — `GET /production/eficiencia-fabril/*`

- Listagem inclui `appointment_id` (vínculo SH6010 via `production_fabril_sh6010_apply`) para abrir detalhe.
- Detalhe na UI: `GET /production/oee/appointments/{appointment_id}` (roteiro SG2, estrutura BOM, tempos, `findings` de alertas).

- **Dashboard** (`/dashboard`): summary e charts aplicam cap 0–199 via repositório. `weighted_efficiency_pct` é a média simples das médias por CT (não a média dos apontamentos).
- **Appointments** (`/appointments`): retorna todos os registros do período (com `turno`/`turno_label` classificados por `hora_inicio`); o MFE filtra localmente para KPIs. Filtro opcional `shift=1|2|3` (CSV) na API para consumidores externos.
- **Eficiência por CT** (`/efficiency-by-work-center`): média % por centro de trabalho — mesma regra do plugin (OK + faixa 0–199%); use no TV em vez da lista bulk.
- **Turnos de fábrica (canônico na API):** `app/domain/production/factory_shifts.py` — 1º `04:34–14:17`, 2º `14:18–23:49`, 3º `23:50–04:33`. O plugin espelha as faixas em `constants/shifts.ts` e prefere `item.turno` quando a API envia.
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
- [padroes-totvs/apontamentos-tempo-padrao.md](./padroes-totvs/apontamentos-tempo-padrao.md) — fórmula `HY_TEMPAD` (único ponto de verdade)
- [producao-eficiencia-changelog-jun2026.md](./producao-eficiencia-changelog-jun2026.md) — eficiência por tempos, fórmulas legíveis, auto-refresh, alinhamento OEE/SI
- [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../../docs/12-roadmap-e-evolucao/eficiencia-fabril/)
- `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md` — filtro `status` do OEE

## Alterar a faixa no futuro

1. Atualizar **apenas** `production_efficiency_valid_range.py` e espelhar em `businessRules.ts` (eficiência fabril **e** dashboard-production).
2. Rodar testes de OEE e eficiência fabril.
3. Atualizar este documento e as specs em `docs/12-roadmap-e-evolucao/eficiencia-fabril/`.
4. Revisar vocabulário do chat (`presentation_profiles.json`, `external_action_responses.json`) se textos citarem a faixa.
