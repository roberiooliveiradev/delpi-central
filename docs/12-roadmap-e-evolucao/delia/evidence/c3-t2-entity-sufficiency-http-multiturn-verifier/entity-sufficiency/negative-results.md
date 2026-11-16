# Entity sufficiency negatives (directed)

| Case | Expectation | Result |
|---|---|---|
| S2 sales_order metric vs process obligation | UNSATISFIED | PASS |
| S2b presentation without entity= | fail closed | PASS |
| S3 product entity mismatch | UNSATISFIED | PASS |
| Sibling process+ativo with congruent entity | SATISFIED | PASS |

Source: `tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py`
