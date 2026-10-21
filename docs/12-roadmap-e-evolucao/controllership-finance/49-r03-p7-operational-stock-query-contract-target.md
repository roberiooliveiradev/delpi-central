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
