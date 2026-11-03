# SI — Production Inventory Acceptance

AUTHENTICATED_USER_USER=PASS (user@local.com PKCE, delpi realm)
EFFECTIVE_PERMISSION_SCOPE=PASS (7 depts returned, no elevation)
DEPARTMENT_INVENTORY=PASS (7 depts, 38 indicators)
INDICATOR_CATALOG=PASS (configs + realized + goals + scores live)
GOAL_CONFIG_INVENTORY=PASS (comparable vs reference, period kinds)
REALIZED_INVENTORY=PASS (branch+consolidated, source gaps visible)
BRANCH_AGGREGATION=PASS (sum for currency/count; source-consolidated
  for percent realized; avg-of-unit-scores for IDD)
TEMPORAL_AGGREGATION=PASS (exact vs accumulated; partial prorata proven:
  92×2/30=6.13 Nov OTD comparable)
IDD_RECONCILIATION=PASS (Sep 9.99 = mean of branch scores 10.0/9.98)
SEPTEMBER_2026_RECONCILIATION=PASS (all 5 values match PO screen:
  CPV 43.09/10.00, OTD 94.27/9.99, stock 14,469,584.01/8.21,
  turnover 0.15/0.76, savings Indisponível/0.00)
LATEST_CLOSED_COMPETENCE: current period = Nov/2026 (partial, 2d)
CUSTOM_PERIOD_RECONCILIATION=PASS (supplies-otd: SI 91.12 vs
  consumers 92.00 — drift direction corrected vs prior report)
SUPPLIES_PARITY=DRIFT_DOCUMENTED (D1/D2)
BUSINESS_WRITES=NONE · CODE_CHANGES=NONE · DEPLOY=NONE
