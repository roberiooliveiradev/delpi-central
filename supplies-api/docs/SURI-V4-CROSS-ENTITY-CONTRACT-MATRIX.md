# SURI V4 — Cross-Entity Contract Matrix

```
TASK: SURI-PROCUREMENT-INTELLIGENCE-V4-CONTINUOUS-EXECUTION-001
HEAD: 86dfa83098 · verified on HEAD
```

| dataset | owner | read op | keys | grain | branch | join eligible |
|---|---|---|---|---|---|---|
| overview | supplies-api | analyze overview_summary | branch, dates | per-period composite | list\|single | no (composite only) |
| otd | supplies-api | read otd aggregate\|series | branch, dates | per-period | str \| list | aggregate=1 branch; series=multi |
| deliveries | supplies-api | read deliveries late | branch, dates | per-receipt MP | list | by order num when exposed |
| safety_stock | supplies-api | read safety-stock summary\|items\|details\|suppliers | branch+product | per material×branch | str | by product_code+branch |
| purchase_orders | api-delpi | read purchase-orders | branch+num | per line | str | by num+branch |
| purchase_requests | purchase-requests-api | read purchase-requests | branch+num | per item | str | by num+branch |
| suppliers | api-delpi(S2S) | read suppliers search\|get | code+store | per supplier | — | by code+store |
| consumption | api-delpi(S2S) | read consumption search\|get\|comparison | 11-char OP | per OP | str unit | by OP key |
| market | supplies-api | read market filters\|summary\|series | instrument+dates | per series | — | not joinable |
| comex | supplies-api pg | read\|execute comex | governance_id, view_id | per record | unit_scope | not joinable |

## Rules honored

- Canonical keys only — no fuzzy joins by name/description.
- Aggregation per source's own unit scope; composition never widens.
- Sample vs population explicitly separated (population_total_lines).
- data_gap when a source fails — never fabricated.
- Deliveries list = receipts MP by entry date; OTD analytics =
  order-line population — documented divergence, not a bug.

## Missing inputs (declared, not invented)

- Lead time homologado per etapa → IN-07/IN-04 partial
- Risk probability homologada → SU-04/Kraljic quadrante = ilustrativo
- Supplier score weights aprovados → SU-01 scorecard = parcial
