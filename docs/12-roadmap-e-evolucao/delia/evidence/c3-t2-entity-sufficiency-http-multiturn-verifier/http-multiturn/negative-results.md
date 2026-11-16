# HTTP multiturn negatives

| Case | Mechanism | Result |
|---|---|---|
| M+ positive two-turn | fixture handler + real route | PASS |
| M1 foreign AuthZ | real HandleInteractiveConversationTurn → 403 | PASS |
| M2 missing context | no invented objective | PASS |
| M4 DELIA_RESULT invented code | not authority (`invented_record_tokens`) | PASS |
| M5 user-named code | accepted | PASS |
| M10 code in first turn | no clarification | PASS |
| invalid context kind | rejected | PASS |
| M3/M6/M7/M8/M9 live | PENDING (no dedicated live identity / not critical) | PENDING |
