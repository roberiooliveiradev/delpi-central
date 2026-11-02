# Strategic Indicators — Production Global Inventory (as user)

TASK: STRATEGIC-INDICATORS-PRODUCTION-GLOBAL-INVENTORY-001
AUTH: user@local.com via PKCE/mcp-supplies — authorized scope only
ENDPOINT: /strategic-indicators/integrations/dashboard-departments-indicators
BASE_HEAD: 4408d88de9 · READ-ONLY · zero mutation

## Departments — 7 found, 38 indicators total

| dept | idd (nov current) | dept_aggregation | indicators |
|---|---|---|---|
| financial | 0.0 | consolidated | 3 (fixed-cost, ebitda, pmr) |
| hr | 7.53 | average_of_units | 6 |
| commercial | 1.5 | average_of_units | 6 |
| production | 1.25 | average_of_units | 5 |
| quality | 0.0 | average_of_units | 11 (incl. 6 ppm) |
| supplies | 4.2 | average_of_units | 5 |
| engineering | 4.0 | consolidated | 2 |

## Field exposure (contract)

per indicator: indicator_id, name, weight_pct, goal_label,
goal_value, comparable_goal, reference_goal, goal_periodicity,
goal_mode, goal_aggregation, goal_period_kind, goal_period_partial,
performance_direction, value_unit, realized{01,02,consolidated},
score. NOT_EXPOSED here: branch_value_aggregation, source_key,
is_active, aggregation_mode per-indicator (dept-level only).

## realized coverage

- currency+count+sum indicators: consolidated = SUM of branches
  (stock-value: 3,893,096.17+10,576,487.84=14,469,584.01 ✓)
- percent indicators: consolidated = SOURCE consolidated (weighted
  by producer denominators), NOT mean — supplies-otd Sep:
  branches 98.03/91.81 → consolidated 94.27 (=362/384 lines);
  mean would be 94.92. CPV: 42.43/43.24→43.09 ≠ 42.83 mean.
- negotiation-savings: realized null both branches (inactive,
  manual/spreadsheet source) → score 0.
- financial: all realized consolidated:null (source unavailable).
