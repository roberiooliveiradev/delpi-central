# Regressão — IDD de Engenharia zerado (jul/2026)

**Status:** corrigido em `68a9bf3f0` (calculador SI).  
**Sintoma:** `dashboard-engineering` badge **IDD 0.0 Crítico** enquanto cards KPI mostravam **Nota IDD 10**.  
**Não era** cadastro admin nem rota api-delpi `/dashboard/department-idd` (outros departamentos OK).

## Causa raiz

Dois caminhos distintos de “nota IDD”:

| Superfície | Fonte | O que o usuário via |
|------------|-------|---------------------|
| Cards KPI do MFE | `GET /engineering/...` + cálculo local (`goalDisplay`) | 10,00 |
| Badge do header | `GET /dashboard/department-idd` → SI | 0.0 Crítico |

No SI, o provider de engenharia publica **só** `unit_values = { "consolidated": valor }` (`build_unit_values_for_consolidated_department`).

Após **26/06/2026** (`9d519dcfb` — “penalizar indicadores sem dado com nota zero”), `_scores_zero_when_unfilled` passou a retornar `True` para **todos** os indicadores. Em caminhos que pedem filial `01`/`02` (`average_of_units` ou `_calculate_branch_scoped_indicator_score` com `branch_goals`), a ausência de chave por filial virou **nota 0** e puxou o IDD do departamento para 0 — mesmo com `measurement.value` válido e KPIs em 10.

Preparação (mai/2026): scoring por filial + medição consolidada-only em engenharia (`3b47a5518`, `6fed86127`).

## Correção canônica

`StrategicIndicatorsCalculator`:

1. `_uses_average_of_units_aggregation` — se `is_consolidated_aggregation_department(department_id)` (engenharia, financeiro em `branch_filter.CONSOLIDATED_AGGREGATION_DEPARTMENT_IDS`), **nunca** usa média por filial.
2. Não aplica `_calculate_branch_scoped_indicator_score` nesses departamentos — usa `measurement.value` + meta consolidada.

**Catálogo:** ajustar agregação/`scope_type` só pela aplicação admin SI — **não** migration de dados para “corrigir” IDD.

**Não corrigir no MFE** do dashboard-engineering (badge só exibe `item.score` do SI).

## Anti-padrões (proibido reintroduzir)

1. Fazer `_scores_zero_when_unfilled` (ou equivalente) zerar filial `01`/`02` ausente em departamento que só publica `consolidated`.
2. Assumir que `aggregation_mode` do banco sozinho define o cálculo — departamentos em `CONSOLIDATED_AGGREGATION_DEPARTMENT_IDS` têm medição consolidada por contrato do provider.
3. Duplicar `01`/`02` em `unit_values` de engenharia “só para o IDD bater” — quebra rótulo/exibição consolidada; o calculador deve respeitar a chave `consolidated`.
4. Patch só no MFE para inventar IDD global a partir dos cards.

## Testes de regressão (obrigatórios)

Arquivo: `tests/test_engineering_consolidated_branch_view.py`

- `test_engineering_idd_not_zero_when_catalog_still_average_of_units`
- `test_engineering_ignores_orphan_branch_goals_with_consolidated_measurement`

Cenário mínimo: medições com valor e `unit_values={"consolidated": …}`, notas dos indicadores 10 → **IDD departamento 10**, mesmo com `aggregation_mode=average_of_units` ou `branch_goals` 01/02 órfãos.

```bash
cd strategic-indicators-api
PYTHONPATH=. pytest tests/test_engineering_consolidated_branch_view.py -q
```

## Checklist antes de alterar scoring / providers

- [ ] Departamento novo com medição só `consolidated` → entra em `CONSOLIDATED_AGGREGATION_DEPARTMENT_IDS` + provider usa `build_unit_values_for_consolidated_department`.
- [ ] Mudança em `_scores_zero_when_unfilled` / `average_of_units` → rodar testes de engenharia acima.
- [ ] Badge IDD do dashboard: validar `GET .../dashboard/department-idd?department_id=engineering` com KPIs bons no mesmo período.

## Referências

- Calculador: `si_app/domain/services/strategic_indicators_calculator.py`
- Lista consolidada: `si_app/shared/branch_filter.py`
- Provider: `si_app/infrastructure/providers/strategic_indicators/engineering_indicators_snapshot_provider.py`
- Metas/escopo: [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md)
- Regra Cursor: `.cursor/rules/si-consolidated-department-idd.mdc`
