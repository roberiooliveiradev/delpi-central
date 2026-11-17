# Matriz de requisitos, testes e evidência

**Status:** TARGET / TEST_NOT_RUN para Studio V4. PASS de V3 no Portal Engenharia **não** prova Studio desacoplado.

| RQ | Aceite requerido | Teste mínimo |
|---|---|---|
| ST-01 | API pública Studio sem import do Portal Engenharia | residual search + build consumer |
| ST-02 | Primeira importação em Processos sem regression V3 | E2E autenticado + screenshots |
| ST-03 | Seis métodos documentados e status honesto | catálogo/componente |
| ST-04 | Criar estudo sem SKU e inserir operações | componente + e2e manual |
| ST-05 | Fonte oficial via BFF/AuthZ real | integração 200/403/404/empty |
| ST-06 | Visual e tabela referenciam mesmo estado | alter table, assert chart e vice-versa |
| ST-07 | Editor de horário/minutos e múltiplas pausas | unit cases 24h/overlap/zero |
| ST-08 | Stepper + campo numérico de demanda/lote/postos | teclado/validação |
| ST-09 | Yamazumi com atribuição exclusiva e movimentos | unit invariants + e2e |
| ST-10 | UNKNOWN não vira zero e agregado não se decompõe | unit + visual |
| ST-11 | Sem cálculo fictício para MANUAL | contrato e estado de método |
| ST-12 | Cenário A/B preserva contexto e revision | state tests, F5, STALE |
| ST-13 | Clear remove apenas estudo do scope | storage isolation + confirm |
| ST-14 | Export tem origem, método e limitações | CSV/XLSX/PDF test |
| ST-15 | Dark/light 1440/1024/390/320, sem overflow | Playwright screenshot |
| ST-16 | Acessível por teclado, labels, sem color-only | axe/keyboard/semantic checks |
| ST-17 | Roteiro da Ficha do Produto intacto | regressão E2E existente |
| ST-18 | Verify independente, findings resolvidos | veredito e rodadas |
| ST-19 | HML aprovado antes de PROD | SHA + smoke SSO |
| ST-20 | PROD validado ou PENDING_USER_SMOKE explícito | artefato + browser legítimo |

## Matriz de testes de algoritmo e dado
- Roteiro: operação duplicada por componente, múltiplas filiais, estágios separados, setup por lote, tempo faltante, zero vs UNKNOWN.
- Manual: sem código, duas operações mesmo nome, IDs estáveis, unidade segundos/minutos, categoria não declarada.
- Yamazumi: postos vazios, operação órfã, duplicação, sobre-takt, takt desconhecido, alta densidade, input inválido.
- Turno: múltiplas pausas, overlap, fora de janela, virada, modo minutos.
- Storage: usuário/portal/filial diferente, revisão mudada, quota/erro, clear/cancel, refresh.
- API: 403 fail-closed, 404, truncamento, erro temporário, mudança de permissão.

## Evidência exigida em cada execução
`BASE_HEAD`, `FINAL_HEAD`, `ORIGIN_MAIN`, `FILES_CHANGED`, testes no SHA, screenshots referenciáveis, `VERIFY_VERDICT`, `HML_DEPLOY_SHA`, `PROD_DEPLOY_SHA`, `PROD_AUTHENTICATED_SMOKE`, rollbacks, `EXECUTION_DRIFT`. Classificar `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN` sem extrapolar.
