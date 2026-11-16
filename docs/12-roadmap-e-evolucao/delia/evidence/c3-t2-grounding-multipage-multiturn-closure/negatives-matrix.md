# Matriz de negativos — G2 / REF05 / R5 / R6

Classificação por evidência executada nesta task ou suites canônicas
já verdes no HEAD.

## G2 / falso COMPLETE

| Cenário | Esperado | Resultado | Evidência |
|---|---|---|---|
| Plano ausente + clarificação | `CLARIFICATION_REQUIRED` | `CONTRACT_TEST_PASS` | `test_g2_plan_absent_keeps_clarification_over_unrelated_evidence` + `test_clarification_short_circuits_finalize` |
| Plano sem obrigações + evidência não pertinente | não descartar clarificação | `CONTRACT_TEST_PASS` | OC-1 `550eae55` + teste acima |
| Uma obrigação SATISFIED e outra pendente | não COMPLETE | `CONTRACT_TEST_PASS` | `test_g2_one_satisfied_one_pending_does_not_publish_complete` |
| Evidência relacionada sem filtro/identidade | ask-back / parcial | `CONTRACT_TEST_PASS` | `test_g2_clarification_still_applies_when_obligations_unmet` |
| Total sem escopo autoritativo | insuficiência/parcial | `CONTRACT_TEST_PASS` | r45 `PAGE_SLICE_NOT_TOTAL` / `PARTIAL_UNKNOWN` |
| Fonte declara incompletude | não enumerar COMPLETE | `CONTRACT_TEST_PASS` | r45 t20 + R5-N10 |
| Identificador explícito não coberto | cobertura parcial | `CONTRACT_TEST_PASS` | `test_g2_unbound_target_still_runs_partial_identifier_coverage` |
| COMPLETE sem evidência suficiente | override | `CONTRACT_TEST_PASS` | `test_g2_complete_without_bound_evidence_is_overridden` |
| Modelo cita valor não sustentado | não FACT | `CONTRACT_TEST_PASS` | `declared_answer_unverified_values` (g1 + live R6 pré-gate) |
| AuthZ parcial | não ocultar negativa | `CONTRACT_TEST_PASS` | `test_int1_partial_authorization_finalize` |

`FALSE_COMPLETE=0` / `FALSE_SATISFIED=0` nos casos válidos executados.

## REF05

| Caso | Resultado | Evidência |
|---|---|---|
| Positivo: filtro descritivo espúrio não veta agregação SATISFIED | `CONTRACT_TEST_PASS` | `test_g2_...ref05_target_unbound_nonblocking` |
| Identidade nomeada não coberta | `CONTRACT_TEST_PASS` | `test_g2_unbound_target_still_runs_partial_identifier_coverage` |
| Obrigação não satisfeita | `CONTRACT_TEST_PASS` | `test_g2_unbound_target_still_fails_when_obligation_unsatisfied` |
| Evidence anchor só sintático / capability sem pertinência | `CONTRACT_TEST_PASS` | suite `test_pydantic_ai_semantic_rework` REF05 |
| Total não demonstrado / scope incompatível | `CONTRACT_TEST_PASS` | obligation scope + r45 |

## R5-N1 … R5-N10

| ID | Caso | Classificação | Evidência |
|---|---|---|---|
| R5-N1 | Página duplicada | `CONTRACT_TEST_PASS` | `test_r5_n1_*` / r45 t05 |
| R5-N2 | Registro duplicado | `CONTRACT_TEST_PASS` | `test_r5_n2_*` / r45 t06 |
| R5-N3 | Owner diferente | `PENDING` | Aggregator é owner-agnostic; sem contrato de composição cross-owner — residual documentado, sem inventar isolamento novo |
| R5-N4 | Filtros divergentes | `PENDING` | Continuação de walk não persiste fingerprint de filtro no aggregator; residual OPEN |
| R5-N5 | Scope divergente | `PENDING` | Idem N4 no nível de página; AuthZ cross-user coberto por suites de isolation, não por merge de páginas |
| R5-N6 | Total divergente | `CONTRACT_TEST_PASS` | `test_r5_n6_*` / r45 t12 |
| R5-N7 | Página ausente | `CONTRACT_TEST_PASS` | `test_r5_n7_*` / r45 t04 |
| R5-N8 | Truncamento sem total | `CONTRACT_TEST_PASS` | `test_r5_n8_truncated_walk_without_total_not_complete` / r45 t10; com `total_count` o aggregator trata a contagem como autoritativa (contrato), enumeração continua em N10 |
| R5-N9 | Deadline/budget | `CONTRACT_TEST_PASS` | `test_r5_n9_*` / r45 t09 (sem total autoritativo) |
| R5-N10 | Agregação ≠ enumeração | `CONTRACT_TEST_PASS` | `test_r5_n10_*` + expected do live R5 |
| R5+ | Walk 40+40+29 | `LIVE_PASS` | `or-qwen14b-e12d13cf3f56` + `test_r5_positive_three_page_walk_109` |

## R6 multi-turno

| Caso | Classificação | Evidência |
|---|---|---|
| Continuação com código no prior | `LIVE_PASS` + `CONTRACT_TEST_PASS` | `e12d13` recovery + `invented_record_tokens` prior-turn |
| 1º turno já tem identificador | `CONTRACT_TEST_PASS` | literal aceito quando presente |
| 2º turno identificador inválido/inventado | `LIVE_PASS` / unit | pré-gate `P12345` + gate unitário |
| Mudança de assunto / contexto outro usuário | `PENDING` / AuthZ suites | sem live dedicado nesta task; fail-closed AuthZ pré-existente |
| Contexto ausente/expirado | `CONTRACT_TEST_PASS` | prior vazio → invented |
| Permissão mudou | `PENDING` | R4 identidade deny ainda OPEN |
| Owner indisponível | `LIVE_PASS` (parcial) | `davi.get_context` SOURCE_UNAVAILABLE no recovery, read posterior SUCCESS |
| Clarificação parcial / correção de código | `CONTRACT_TEST_PASS` | testes invented correction |
| Modelo propõe id não fornecido | `CONTRACT_TEST_PASS` + live pós-gate | `4136fe9b93c0` ask-back; gate invented |
