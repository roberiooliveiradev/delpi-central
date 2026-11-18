# Entry audit — Residuais das ondas

Registro contínuo dos residuais apontados pelo `delpi-verifier`, pelo owner ou pela
verificação de execução. Itens fechados ficam com status e evidência; abertos seguem
para correção na trilha.

## Onda 1 (T15–T17H) — revista de 18/11/2026

| # | Residual | Status | Evidência |
|---|---|---|---|
| R1 | `test_entry_audit_t9r4.py::test_e5_previous_kpis_match_current_fields` FAIL pré-existente: exigia `summary["previous"]` preenchido com UMA análise, contrariando o contrato U12 (`previous` = `None` sem análise anterior compatível — `test_entry_audit_u12_previous_and_sort.py`, `service.py` `_previous_analysis`/`_previous_kpis`) | **CLOSED** | teste reescrito como reconciliação com o contrato U12: monta a análise anterior compatível (mesmo span/filiais/tipos) + a atual e prova a igualdade dos campos; novo caso «sem anterior → `previous` é `None`». Código de produção intocado. Suíte `pytest tests -q`: 1439 passed, 0 failed |
| R2 | Rerun PROD `6bf91317…` × canônica `f8b4b1b4…`: −16 nas regras-alvo (esperado) e −4 líquido em regras não-alvo | **CLOSED — dados, não código** | diff por regra/nota: −8 removidas e +4 adicionadas, todas em notas corrigidas ou lançadas entre as execuções (evidência em `SF1`/`SD1`: ICMS e base estornados na nota com `header.icms_above_xml`; desconto lançado na nota com `accessory_field`/`total_mismatch`; alíquota e data corrigidas no CT-e com `credit_mismatch`/`rate_or_base`/`issue_date`; notas novas lançadas em 17/11 geraram `unusual_cfop_nature` e `presumed_wrong_tes`). Sem EXECUTION_DRIFT |
| R3 | Primeiro ensaio HML da T17H rodou com imagens pré-T16 — flags ligadas sem o código | **CLOSED — regra nova no track** | Parte 0 regra 4: antes de cada ensaio em HML, reconstruir os serviços afetados (`up-hml-sequential.sh --build`) e provar no container o SHA do código e o valor das flags; ensaio sem essa prova = INCONCLUSIVE |

## Abertos

_(nenhum no momento)_
