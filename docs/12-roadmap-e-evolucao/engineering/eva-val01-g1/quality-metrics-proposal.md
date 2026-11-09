# G1_QUALITY_METRICS_AND_THRESHOLDS_PROPOSAL

**APPROVAL_STATUS:** `OWNER_BLOCKED`  
**APPROVAL_OWNER:** Engenharia  
**Nota:** valores em `PROPOSED_THRESHOLD` são **propostas justificadas**, não percentuais aprovados.

## Métricas estruturais (M1)

| METRIC_NAME | DEFINITION | DENOMINATOR | MATCHING_RULE | CRITICALITY | PROPOSED_THRESHOLD | THRESHOLD_RATIONALE |
|---|---|---|---|---|---|---|
| `table_detection` | Região `component_table` encontrada na página anotada | nº páginas com tabela no GT | IoU região ≥ 0,8 vs GT | HIGH | *owner* | Sem tabela, demais métricas inválidas |
| `row_identity` | Linhas físicas distintas preservadas (ex. A2≠A3) | nº pares de linhas adjacentes críticas no GT | sem fusão indevida | **CRITICAL** | **0 fusões críticas** | Defeito P0 histórico |
| `column_identity` | Colunas Item/QTD/Componente/Descrição separadas | nº colunas rotuladas no GT | ordem/papel corretos | HIGH | *owner* | Fragmentação A9+qty+code |
| `cell_match` | Célula com IoU/posição correta | nº células GT com box | IoU ≥ 0,5 ou centro em célula | MED | *owner* | Sensível a DPI/crop |
| `span_match` | rowspan/colspan corretos | nº células com span≠1 | rowspan/colspan iguais ao GT | HIGH | *owner* | Pais de subconjunto |
| `false_row_merge` | Duas linhas GT em um campo | nº oportunidades de merge | contagem de merges | **CRITICAL** | **0** em casos críticos homologados | 10080192∥10090316 |
| `false_cell_split` | Uma célula GT fragmentada | nº células multilinha | splits indevidos | MED | *owner* | Descrição longa |
| `token_cell_association` | Texto/token na célula correta | nº textos CLEAR no GT | contenção/associação correta | HIGH | *owner* | Base do M2 |

## Métricas funcionais (M2 — posteriores; não gateiam M1)

| METRIC_NAME | DEFINITION | DENOMINATOR | CRITICALITY | PROPOSED_THRESHOLD |
|---|---|---|---|---|
| `item_qty_link` | item↔qty mesma ocorrência | ocorrências GT | HIGH | *owner* |
| `item_code_link` | item↔component_code | ocorrências GT | **CRITICAL** | *owner*; 0 falsos códigos críticos |
| `code_description_link` | code↔description | ocorrências GT | HIGH | *owner* |
| `occurrence_subset_link` | ocorrência↔subconjunto pai | ocorrências sob grupo | **CRITICAL** | *owner* |
| `duplicate_or_lost_occurrence` | perda/duplicata | ocorrências GT | HIGH | *owner* |
| `false_promoted_code` | código promovido indevidamente | campos publicados | **CRITICAL** | **0** em regressão crítica |

## Segurança / incerteza

| METRIC_NAME | DEFINITION | CRITICALITY | PROPOSED_THRESHOLD |
|---|---|---|---|
| `false_component` | Componente inventado | CRITICAL | 0 |
| `invented_critical_field` | Campo crítico sem evidência | CRITICAL | 0 |
| `unflagged_ambiguity` | Ambiguidades GT não sinalizadas | HIGH | *owner* |
| `provenance_failure` | Sem página/região/box | HIGH | 0 em casos exigindo proveniência |
| `correct_abstention` | Abstenção quando GT=AMBIGUOUS | HIGH | *owner* (não punir abstenção correta) |

## Regras de uso

1. Thresholds só entram em vigor após `THRESHOLD_APPROVAL_STATUS=APPROVED` pela Engenharia.
2. Completude (mais campos preenchidos) **não** substitui precisão estrutural.
3. Holdout cego só após `TRUE_UNSEEN_HOLDOUT` disponível e aprovado.
