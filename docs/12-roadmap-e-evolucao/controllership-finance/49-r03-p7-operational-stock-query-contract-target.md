# 49 — R03/P7: contrato TARGET de consulta operacional inicial

> 21/10/2026. PO aprovou **opção A**: preparar contrato e implementação da consulta operacional R03, sem afirmar reprodução integral do MATR460. Documento de design; **RUNTIME_GATE=PENDING**. Não executar deploy nem criar dados/fórmulas presumidos.

## 1. Objetivo e autoridade

PROC-0072, R03 — Registro de Inventário Modelo P7 (MATR460). TÉO é authority AS-IS; PDF/prints originais comprovam seus próprios valores e parâmetros; DAVI comprova somente campos/linhas consultados no Protheus; GitHub HEAD é authority TARGET. Ver docs 03, 46 §§10–22 e 48 (padrão R01/R02).

**Entregar agora, após gate:** leitura histórica por competência, filial, produto, tipo, grupo e armazém, com totais **rotulados como históricos exploratórios, nunca total oficial P7**. O usuário pode alternar o recorte abrangente e MP/PI/PA. **Fora da v1**: emitir PDF idêntico ao P7, tratar Bloco H como exportação fiscal oficial, reconstruir WIP/SC2 por suposição, executar Acompanha Custos ou alterar Protheus, homologar reconciliação Entradas/Saídas − P7 − H02.

## 2. Inventário físico e restrições comprovadas

- `SB9010`: `B9_FILIAL`, `B9_COD`, `B9_LOCAL`, `B9_DATA`, `B9_QINI`, `B9_VINI1`, `B9_CM1`, demais custos. `SB1010`: `B1_COD`, `B1_DESC`, `B1_TIPO`, `B1_GRUPO`, `B1_UM`. Testar cardinalidade e exclusão lógica conforme convenções locais antes de operacionalizar join.
- Competência `YYYY-MM` deriva **último dia calendário** de referência. `branchCode` é dimensão de dados, não código permission.
- Filtros funcionais `all_products` (P7 amplo, investigação) e `mp_pi_pa` (restringe `B1_TIPO` a MP, PI e PA), **como visões exploratórias**, não como equivalência comprovada de parâmetros internos do MATR460. Joici confirmou escopos distintos, e relatou layout H para a saída restrita; algoritmo real e destinatário Financeiro/Contabilidade ainda precisam confirmação.
- PDFs recebidos: `Estoque.pdf` (Matriz, 30/09/2026, folha 101, total 3.946.431,87), `Resumo Estoque.pdf` (folha 74, total 2.976.967,56). O vídeo mostra outra emissão (folha 91, 3.776.994,69). Nenhum desses números é automaticamente `SUM(B9_VINI1)`.
- **EXECUTION_DRIFT:** SB9 30/09/2026 filial 01 apresentou 4.812 linhas / soma 3.884.439,52 e, em rechecagem posterior, zero linhas. Obrigatório fail-closed de integridade/completude, sem mostrar total zero como fechamento válido.
- P7 visível no print: `MATR460`, saldo em processo Sim, terceiros Não, custo Médio, custo zerado Não, e `Verif Sld Processo=Data de Emissão`. Composição SC2/WIP e arredondamentos ainda `TO_INVENTORY`.

## 3. Boundaries e rotas candidatas (TARGET, não criadas)

- MFE exclusivo: `plugins/controllership-finance`, base `/apps/controllership-finance`. **Candidata:** `/apps/controllership-finance/closing/stock-inventory`. O HEAD `src/app/pluginRoutes.ts` registra somente `home` e `closing/financial-settlements`.
- BFF: `controllership-finance-api`, base `/apps/controllership-finance-api`. **Candidata:** `GET /apps/controllership-finance-api/closing/stock-inventory` para a v1 (consultar roteamento canônico e autorização).
- `api-delpi` mantém SQL, regras Protheus e contrato tipado. A **rota interna canônica ainda requer inventário** de padrões e endpoints existentes; proibir `POST /data/sql` como contrato do Portal e proibir SQL Protheus diretamente na BFF ou no browser.
- Não persistir tabelas do contexto Protheus na BFF. Clean Architecture / ports-adapters; alterações mínimas após gate.

## 4. Shape lógico inicial sob revisão

Request query: `period=YYYY-MM` (obrigatório), `branchCode` (escopo recurso obrigatório e autorizado), `reportScope=all_products|mp_pi_pa`, `warehouse` opcional, `page` e `pageSize` limitados; valores sujeitos aos padrões vigentes.

Response semântica proposta:
- `status: "available" | "source_missing" | "incomplete" | "error"`; `dataAsOf` e `referenceDate`; `source: "protheus_sb9_sb1"`; `officialP7: false`; `parityStatus: "TEST_NOT_RUN"`.
- `items[]`: `productCode`, `description`, `productType`, `productGroup`, `unit`, `warehouse`, `historicalQuantity`, `historicalStockValue`; `historicalUnitCost` só se regra/campo verificado.
- `summariesByType[]`, `summariesByWarehouse[]`, `historicalTotal` (não `officialTotal`), contagem e paginação. **Não somar números `float` sem definir precisão e política de arredondamento fundamentada.** Resumo deve usar universo integral do filtro, não só a página.
- Sem dados da filial/competência: `source_missing` ou `incomplete`, sem `0.00` enganoso. Diferenciar `no_matching_items` de `source_snapshot_missing` somente com prova de completude. Não rotular valores monetários com moeda oficial não comprovada.

Este shape é design, não OpenAPI validado; tipos, códigos HTTP e precedência de estado dependem do contrato atual e revisão transversal.

## 5. Segurança e UX

`controllership-finance.access` autoriza acesso quando resolvida pelo Core como **effective permission**, sempre combinada com `resource_scope/ownership` e regra de negócio, fail-closed. `manage` não substitui `access` automaticamente. JWT somente identidade/contexto. Sem nova permission por página, botão ou filial. Autorização obrigatória na BFF e na fronteira de dados; UI apenas auxilia.

MFE consome somente BFF; usar `@delpi/plugin-ui`, UX PT-BR, claro/escuro mesma árvore, responsividade e foco/teclado. Diferenciar claramente "Consulta operacional — valores históricos, não P7 oficial"; avisar que processo/terceiros e layout H não estão homologados; Help atualiza no mesmo gate.

## 6. Gates obrigatórios para executor

**G0 READ/VERIFY:** HEAD + git status do checkout executor, Project Instructions, .cursor aplicável, ADRs, doc README/30/46/48/49; inventariar padrão vigente de `api-delpi`, BFF, autenticação S2S, effective Core permissions, producers/consumers, schema/tests e owner. Search miss não prova ausência.

**G1 DATA:** verificar disponibilidade atual SB9 por competência/filial, cardinalidade SB1 e integridade/versão do snapshot; reportar `EXECUTION_DRIFT` se persiste. Não preencher gaps artificialmente.

**G2 CONTRACT/DESIGN:** propor API tipada `api-delpi → BFF → MFE`, filtros, comportamento em ausência e limites; resolver real escolha de contratos/rotas com aprovação explícita do PO antes de quebrar padrões existentes. Contrato e docs primeiro, antes de runtime.

**G3 AUTHORIZATION:** gate transversal explícito registrado após inventário; **esta aprovação A não é autorização irrestrita de runtime**. Só então implementar por página, minimum diff.

**G4 TESTS:** testes de data final do mês (incluindo fevereiro bissexto), escopo MP/PI/PA vs completo, múltiplos armazéns, campos faltantes, cardinalidade, arredondamento, paginação, auth fail-closed, branch scope, erros upstream e snapshot ausente; smoke real `TEST_NOT_RUN` até executado.

**G5 OUTCOME:** comparar amostras SQL, totais exploratórios e limites com PDF sem exigir equivalência oficial; export parity `TEST_NOT_RUN`. Registrar relatório de execução, testes, evidências e SHAs; aceitar apenas com outcome verificável.

## 7. Decisão vigente

`OPTION_A_APPROVED=YES`; `DESIGN=TARGET`; `DATA_SOURCE=PROVEN_WITH_EXECUTION_DRIFT`; `CURRENT_P7_RUNTIME=NOT_PROVEN`; `TRANSVERSAL_RUNTIME_GATE=PENDING`; `P7_PARITY=TEST_NOT_RUN`; `OWNER_CALCULATION_RULES=TO_INVENTORY`.

**Próxima ação:** executor retornar inventário de rotas/contratos atuais e teste de fonte, com dúvidas reais destacadas como `DECISION_REQUIRED`, antes de alterar código.


## 8. Decisao de produto: filial e somente filtro (21/10/2026)

O PO confirmou explicitamente que **o Portal Controladoria & Financas nao separa acessos, paginas, funcionalidades nem usuarios por filial**. Filial (`branch` / `B9_FILIAL`) e exclusivamente um filtro de dados nos visuais, incluindo opcao `all` para consolidacao. O usuario com acesso efetivo `controllership-finance.access` ao contexto de consulta pode filtrar 01, 02 ou todas as filiais disponiveis, sem regras de ownership ou permissoes por filial. Essa e a regra de negocio do produto (`OWNER_DECISION=PROVEN`), nao uma inferencia do modelo `BranchAccessGate` de outros produtos. **Nao usar `BranchAccessGate` baseado em permissions por filial**, nem criar novas permission codes, nem bloquear a filial 02 para usuario da filial 01. A BFF continua validando acesso efetivo via Core, identidade humana delegada, regras gerais do recurso e autorizacao fail-closed; o filtro de filial nao confere acesso ao produto.

Inventario relatado pelo executor: rota S2S sugerida `/financeiro/stock-inventory` na api-delpi, BFF `/apps/controllership-finance-api/closing/stock-inventory`, MFE `/apps/controllership-finance/closing/stock-inventory`; scope S2S `stock-inventory.read` e flag default-off sao propostas, **nao provisionamento ou runtime comprovados**. Snapshot SB9 setembro/2026 filial01 ausente no inventario: `EXECUTION_DRIFT`. `BRANCH_POLICY=DECIDED`; `TRANSVERSAL_RUNTIME_GATE=PENDING` ate autorizacao explicita de executar contrato/codigo e verificar provisioning S2S.


## 9. Implementacao v1 executada (21/10/2026)

Gate transversal autorizado pelo briefing de execucao (escopo S2S dedicado, flag propria, contexto dedicado, filial como filtro). Implementacao nas tres camadas, seguindo o padrao `financeiro_settlements` (ADR-010):

**api-delpi** — contexto `financeiro_stock_inventory` (isolado, sem import de `supplies`):
- `GET /financeiro/stock-inventory` — guard S2S `require_s2s_service(required_scopes=("stock-inventory.read",), allowed_clients=("controllership-finance-api",))` + Bearer humano delegado obrigatorio.
- DTOs: `stock_inventory_request.py` (`period=YYYY-MM` → `B9_DATA` = ultimo dia calendario via `calendar.monthrange`; `branch=all|01|02`; `report_scope=all_products|mp_pi_pa`; `warehouse`; `page`/`page_size`), `stock_inventory_response.py`, `constantes.py`.
- Resolver de escopo `stock_inventory_scope.py` espelha D3: `SharedDatasetStockInventoryScopeResolver` exige `FINANCEIRO_STOCK_INVENTORY_ENABLED=true` **e** principal humano delegado; default off → `scope_unavailable` 403 tipado, fail-closed.
- SQL `stock_inventory_sql.py`: subquery agrupada por (`B9_FILIAL`, `B9_LOCAL`, `B9_COD`) com `SUM(B9_QINI)`/`SUM(B9_VINI1)`, `LEFT JOIN SB1010` por `B1_COD`, `D_E_L_E_T_=''` nas duas tabelas, `NOLOCK`, paginacao `OFFSET/FETCH` ordenada deterministicamente; presenca de snapshot medida por `COUNT` por filial **sem** filtros funcionais.
- Status: `available` | `incomplete` (filial esperada sem snapshot em `all`) | `source_missing` (nenhum snapshot → `historicalTotal=null`, `dataAsOf=null`, sem queries de itens) | `no_matching_items` (snapshot existe, filtro vazio → total `0` legitimo).
- Testes: `tests/test_financeiro_stock_inventory_{request,sql,use_case,routes,scope}.py` — 36 casos (bissexto 2028-02, escopos, ausencia/incompletude, S2S 401/403, flag off, principal nao-humano).

**BFF** `controllership-finance-api` — `GET /closing/stock-inventory` em `closing_routes.py`: mesma cadeia `_authorized_user` (principal humano + `controllership-finance.access` efetiva via Core, `rbac_unavailable`→503), Bearer delegado, gateway S2S `ApiDelpiSettlementsGateway` reutilizado (mesmo client credential), envelope `ok`/`fail` com repasse de `scope_unavailable` e status do payload intacto. Testes `test_closing_stock_inventory.py` — 22 casos.

**MFE** `plugins/controllership-finance` — rota `closing/stock-inventory` (`stock_inventory` view), client `api/stockInventoryApi.ts`, pagina `features/closing/StockInventoryPage.tsx` (filtros competencia/filial/visao/armazem, indicadores, resumos por tipo e armazem, tabela paginada, estados dedicados para `source_missing`/`incomplete`/`no_matching_items`/403/503/erro; disclaimer "nao equivale ao MATR460"), ajuda contextual `CF_HELP.stockInventory`, catalogo do hub e manifest atualizados. Testes `StockInventoryPage.test.tsx` (9 casos) + rotas/catalogo/manifesto.

**Evidencia SQL real** (Protheus, 21/10/2026): presenca 2026-09 → somente filial 02 (3.117 linhas); totals `all_products` filial 02 = 3.117 itens / 10.576.487,839; `mp_pi_pa` = 2.547 itens / 10.002.994,971; resumo por armazem soma consistente (00/01/03/25/50/98/99); filial 01 ausente → `source_missing` confirmado. `SB9_SEPT_FILIAL01=EXECUTION_DRIFT` persiste.

**Pendencias externas (nao bloqueiam o codigo):**
- Provisioning Keycloak do scope `stock-inventory.read` no client `controllership-finance-api` — mesma rotina `PROD-CF-S2S-KEYCLOAK-01`. Sem ele a rota responde 403 de scope S2S.
- `FINANCEIRO_STOCK_INVENTORY_ENABLED=true` no ambiente para habilitar o dataset (gate separado de enablement, default off).
- TI-Protheus: causa da ausencia da SB9 30/09/2026 filial 01.

`R03_IMPLEMENTATION=EXECUTED_V1`; `P7_PARITY=TEST_NOT_RUN`; `E2E_SMOKE=TEST_NOT_RUN` (depende do provisioning S2S e da flag); `S2S_KEYCLOAK_PROVISIONING=PENDING`; `FEATURE_FLAG=OFF`.

## 10. RCA do bloqueio 403 em producao (21/10/2026, segunda execucao)

Sintoma reportado: pagina `/apps/controllership-finance/closing/stock-inventory` exibia "Acesso restrito" (403 sem `error.code`). Rastreio das tres origens possiveis de 403 na cadeia:

| Origem | Condicao | Codigo tipado upstream | Estado MFE |
|---|---|---|---|
| BFF `_authorized_user` | sem `.access` efetiva via Core | nenhum (403 direto) | "Acesso restrito" |
| api-delpi guard S2S | token sem `stock-inventory.read` ou client errado | `S2S_SCOPE_DENIED` / `S2S_CLIENT_DENIED` | colapsava em "Acesso restrito" |
| api-delpi resolver de dataset | flag off ou principal nao-humano | `scope_unavailable` | "Escopo de dados indisponivel" |

**Causa raiz comprovada (config, deterministica):** `S2S_SCOPE: ${CF_S2S_SCOPE:-settlements.read}` nos dois docker-compose fazia a BFF solicitar apenas `settlements.read` no token client-credentials — o JWT S2S nunca carrega `stock-inventory.read`, mesmo apos provisioning do scope no client. api-delpi responde `S2S_SCOPE_DENIED` (403) → BFF mapeava 403 generico sem codigo → MFE "Acesso restrito". A convencao documentada (`infra/.env.prod.example`: "use S2S_SCOPE apenas para scopes optional nao-default") exige `S2S_SCOPE` vazio para que o token carregue todos os default scopes do client.

**Causa composta pendente (ops):** scope `stock-inventory.read` ainda nao provisionado como client scope + default scope no client `controllership-finance-api` (`S2S_KEYCLOAK_PROVISIONING=PENDING`); sem ele o 403 persistiria mesmo com `S2S_SCOPE` corrigido. Alem disso `FINANCEIRO_STOCK_INVENTORY_ENABLED` precisa estar `true` no ambiente — com flag off o usuario veria "Consulta ainda nao habilitada", nao dados.

**Correcao aplicada:**
- `infra/docker-compose.yml` + `infra/docker-compose.dev.yml`: `S2S_SCOPE: ${CF_S2S_SCOPE:-}` (vazio → token carrega todos os default scopes do client) e `FINANCEIRO_STOCK_INVENTORY_ENABLED`/`FINANCEIRO_SETTLEMENTS_SHARED_DATASET_ENABLED` explicitados com default `false` no servico api-delpi.
- `infra/scripts/keycloak_s2s_controllership_finance_scope.py` — provisioner bounded (mesmo padrao `keycloak_s2s_supplies_scope.py`): garante `settlements.read` + `stock-inventory.read` como client scopes com atribuicao DEFAULT no client `controllership-finance-api` + audience mapper `api-delpi`. `--check` read-only; `--apply` exige `https://`.
- BFF `_map_gateway_error`: propaga `error.code` upstream (`S2S_*`) em `data.error.code` nos 401/403 — RBAC (sem codigo), negacao S2S e gate de dataset agora distinguiveis.
- MFE: banners distintos — `S2S_*` → "Integracao de dados pendente"; `scope_unavailable` → "Consulta ainda nao habilitada"; 403 sem codigo → "Acesso restrito" (RBAC). Ajuda contextual atualizada (`CF_HELP.stockInventory.status`).
- Testes: BFF +2 (`S2S_SCOPE_DENIED`/`S2S_CLIENT_DENIED` propagados tipados → 24 pass); MFE +1 (banner S2S → 61 pass vitest; eslint clean; tsc clean).

**Smoke real:** `TEST_NOT_RUN` neste ambiente — stack local nao roda os servicos CF, credenciais admin do Keycloak local e `CF_S2S_CLIENT_SECRET` indisponiveis neste contexto. Procedimento de ativacao: (1) deploy do commit em `main`; (2) `python3 infra/scripts/keycloak_s2s_controllership_finance_scope.py --check` e `--apply` no Keycloak de producao; (3) `FINANCEIRO_STOCK_INVENTORY_ENABLED=true` no `.env` de producao; (4) smoke `2026-09`/`branch=02` (dados) e `branch=01` (`source_missing`).

`S2S_SCOPE_FIX=EXECUTED`; `S2S_KEYCLOAK_PROVISIONING=PENDING_OPS`; `FEATURE_FLAG=OFF_UNTIL_OPS_ENABLES`; `E2E_SMOKE=TEST_NOT_RUN`.
