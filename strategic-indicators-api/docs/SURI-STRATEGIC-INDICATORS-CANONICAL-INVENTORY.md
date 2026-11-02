# Strategic Indicators — Canonical Data & Calculation Inventory

```
TASK: STRATEGIC-INDICATORS-CANONICAL-DATA-AND-CALCULATION-INVENTORY-001
BASE_HEAD: 431f10f9a0 · GIT_STATUS: limpo (worktree /tmp/inv-wt, read-only)
SCOPE: investigation only — nenhum código/dado/migration alterado
```

## 1. Doc 1+2 — Physical schema & indicator catalog (static)

```
TABLE: strategic_indicators.department_indicators (owner: SI)
  cols confirmadas via migrations:
    indicator_id PK·logical, department_id, name, description,
    is_active, value_unit, aggregation_mode (V022+),
    branch_value_aggregation (V034, default 'auto',
      CHECK ∈ {auto,sum,average,source_consolidated}),
    source_key, goal fields, performance_direction
  outras tabelas: goals/history/catalog snapshots +
    period scores materializados (period_scores_*)
MIGRATIONS-CHAVE: V022 supplies→average_of_units;
  V023 metas 2026 supplies; V026 comercial per_unit;
  V034 branch_value_aggregation + overrides.
SUPPLIES indicators: supplies-otd, supplies-stock-value,
  supplies-stock-turnover, supplies-cpv (ativos);
  supplies-negotiation-savings (INATIVO — planilha IDD).
RUNTIME_DB_INVENTORY = INCONCLUSIVE (sem acesso DB autorizado
  nesta sessão — inventário é estático por migrations).
```

## 2. Doc 3 — Field semantics (PROVEN)

```
realized = SOURCE_VALUE — vem do producer (api-delpi) via
  providers; SI não recalcula o KPI, aplica regras de agregação/
  período e publica em snapshots materializados.
goal (cadastral) = STORED_CONFIGURATION.
comparable_goal = CALCULATED — resolve_reference_goal +
  calculate_comparable_goal (domain calculator; prorata diária,
  snapshot vs período, multi-mês via _effective_goal_aggregation).
nota_idd = DERIVED — calculate_indicator_score:
  lower_better: v≤g→10 else min(g/v×10,10)
  higher_better: v≥g→10 else min(v/g×10,10)
  v None→0, g≤0→0. round(,2).
performance_direction governa lower/higher_is_better.
```

## 3. Doc 4 — Calculation rules map

```
INDICATOR CONFIG (department_indicators)
 → SOURCE RESOLUTION (providers: supplies_indicators_snapshot_
   provider → delpi_supplies_gateway.get_supplies_otd, source_key)
 → SOURCE VALUES (por filial via api-delpi)
 → BRANCH AGGREGATION (shared/consolidated_value_aggregation.py —
   VER §5) → PERIOD (comparable_goal/prorata domain calc)
 → REALIZED (snapshot materializado, period_scores_*)
 → IDD (calculate_indicator_score)
 → PUBLIC CONTRACT (/dashboard/department-indicators —
   expõe branch_value_aggregation por indicador)
```

## 4. AUTO resolution — PROVEN (a função existe)

`si_app/shared/consolidated_value_aggregation.py`:

```python
resolve_consolidated_value_aggregation(bva, value_unit):
  'sum'→sum · 'average'→average · 'source_consolidated'→average
  'auto' → _VALUE_UNIT_DEFAULT: {'currency':sum,'count':sum}
           else → 'average'          # percent→AVERAGE
aggregate_branch_goal_values: percent/ppm/ratio → SEMPRE average
```

```
supplies-otd (value_unit='percent', bva='auto') → consolidated =
AVERAGE dos valores por filial = (95,86+88,14)/2 = 92,00% ← regra
oficial. O 91,12% do Overview usa consolidado do producer
(weighted by denominators) — método divergente do catálogo SI.
aggregation_mode ('average_of_units', V022) governa o ROLLUP DE
SCORES do departamento (calc_department_score_average_of_units),
camada distinta de branch_value_aggregation (rollup de valores).
```

## 5. Doc 5 — Consumer parity matrix

```
CONSUMER          OTD CONSOLIDADO      MÉTODO
api-delpi         consolidado weighted producer
Overview          91,12%               producer_consolidated ✗
OTD page / SURI   92,00%               average_of_units ✓
SI dashboard      average por regra    oficial ✓
dashboard-supplies(legado)             evidência de tela apenas
PARITY: FAIL entre Overview e catálogo SI (drift confirmado).
```

## 6. September/2026 reconciliation (screen evidence)

```
OTD 94,27% meta 92,00% nota 9,99 — consistente com a fórmula
(ratio 94,27/92,00≈1,0247→10,00; 9,99 sugere valor não arredondado
94,1x ou meta não arredondada — fórmula provada, inputs exatos
= TO_INVENTORY). 362/384 linhas = 94,27% ✓ população coerente.
CPV 43,09% = 2.193.940,70/5.091.141,24 ✓ = 43,09% PROVEN.
negotiation-savings "Indisponível" — indicador inativo, nota 0
(regra: v None→0) ✓ consistente.
RUNTIME_VALUES = INCONCLUSIVE (sem requery autorizada nesta
sessão; valores de tela usados como evidência histórica).
```

## 7. Classification + minimal diff (proposta, não executada)

```
PROVEN: auto→average p/ percent; fórmula IDD; lineage;
  supplies-otd official = average_of_units; Overview=drift.
TO_INVENTORY: DB runtime inventory; valores atuais; aplicação
  de source_consolidated no caminho do realizado (helper resolve
  para average — difere de "usar consolidado do producer";
  semântica exata do campo no realized-path = pendente).
EXECUTION_DRIFT: OverviewCompositionService usa producer
  consolidado ≠ regra do catálogo SI.
MINIMAL DIFF (futuro): Overview consumir average_of_units sobre
  valores por filial, via branch_value_aggregation exposto pelo
  SI — preserva contrato, unifica Overview=OTD page=SURI=SI.
  ⚠ muda número exibido → requer GO do PO.
```
