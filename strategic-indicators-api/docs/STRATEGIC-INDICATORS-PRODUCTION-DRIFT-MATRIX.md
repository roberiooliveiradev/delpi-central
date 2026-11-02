# SI — Production Drift Matrix

| DRIFT | OFFICIAL (SI) | CONSUMER | Δ | SEVERITY |
|---|---|---|---|---|
| D1 supplies-otd consolidated 2026-08-04→11-02 | 91.12% (source_consolidated, weighted by line counts; SI publishes it) | OTD page / SURI = 92.00% (_mean of branch %) | +0.88pp | HIGH — consumer computes unapproved simple mean |
| D2 OTD page aggregation | SI consolidated = producer value | OtdAggregateService averages branch ratios | method | HIGH |
| D3 Overview | matches SI 91.12% | conformant | — | OK |
| D4 negotiation-savings realized null→0 | score 0 per formula (v None→0) | screen shows Indisponível | ok, presentational | LOW |
| D5 financial realized null | source unavailable | scores 0 (formula) | data gap, not formula bug | LOW |
| CORRECTION to prior investigation: earlier report attributed
  average_of_units as the realized-consolidation rule. Production
  evidence shows SI publishes the SOURCE consolidated for
  percent indicators (weighted); average_of_units governs SCORE
  rollup (branch scores mean) and goal aggregation, not the
  realized value. The divergent consumer is the OTD page/SURI. |

## Recommended minimal diff (NOT executed)

OtdAggregateService/SURI should report the SI/producer consolidated
(91.12) alongside per-branch values, or label its mean explicitly
as unweighted branch average — decision is architectural (changes
displayed number → requires PO/architect GO).
