# Roadmap e gates de validação

**D0 (agora):** documentação greenfield, modelo, UX, catálogo, Yamazumi. `DOCUMENTED / TEST_NOT_RUN`.
**I1:** scaffold real e API pública com build e testes de contrato, sem importar Engineering.
**I2:** editor de operações e processo manual completo; dados originados no usuário.
**I3:** editor de turnos com horário/minutos, múltiplas pausas e validação de sobreposição/meia-noite.
**I4:** Station Board + Yamazumi original + tabela sincronizada + cenários.
**I5:** adapters de leitura autorizada oficial; integração no Portal Engenharia pelo contrato público sem copiar código legado.
**I6:** testes, Verify independente, HML e, após gate, PROD, com rollback.

## Critérios
`ST-01` Studio compilável independente; `ST-02` nenhum import/cópia do MFE Engenharia; `ST-03` catálogo M1–M6 honesto; `ST-04` manual sem SKU; `ST-05` origem oficial via adapter; `ST-06` turno e pausas; `ST-07` tabela↔gráfico sincronizados; `ST-08` estações e operações; `ST-09` cenário/draft isolados; `ST-10` nenhum solver fictício; `ST-11` dark/light/mobile/teclado; `ST-12` regressão Portal Engenharia; `ST-13` testes reais no SHA; `ST-14` Verify honesto; `ST-15` HML antes de PROD.

## Evidência requerida
`BASE_HEAD`, `FINAL_HEAD`, `FILES_CHANGED`, `TESTS`, `VERIFY_VERDICT`, `HML_DEPLOY_SHA`, `PROD_DEPLOY_SHA`, `PROD_AUTHENTICATED_SMOKE`, `ROLLBACK`, `EXECUTION_DRIFT`. Não declarar DONE por README.
