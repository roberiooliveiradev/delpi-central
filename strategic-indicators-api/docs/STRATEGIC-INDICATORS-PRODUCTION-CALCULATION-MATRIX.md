# SI — Production Calculation Matrix

## Semantics (proven live + code)

comparable_goal: period-prorated cadastral goal.
  Sep exact month → comparable=reference (92.0).
  Nov partial (2d) → 6.13 = 92×2/30 (average-unit indicators sum
  daily slices intra-month; accumulated multi-month keeps level).
goal_period_kind: exact | accumulated; goal_period_partial bool.
realized{01,02,consolidated}: per-branch from producer +
  consolidated = producers consolidated (source_consolidated
  semantics for percent; sum for currency/count).
IDD score: direction-aware ratio×10 cap 10; consolidated score =
  MEAN OF BRANCH SCORES for average_of_units depts —
  Sep OTD: 01:98.03→10.00, 02:91.81→9.98 → (10+9.98)/2=9.99 ✓
  EXPLAINS the previously unresolved 9.99.
dept idd = weighted score via weight_pct, average_of_units rollup.

## Field classification

realized.consolidated = SOURCE_VALUE (producer consolidated).
realized.01/02 = SOURCE_VALUE per branch.
comparable_goal = CALCULATED. reference_goal = STORED config.
score/idd = DERIVED (domain calculator).
branch_value_aggregation = STORED config (not in this payload).
