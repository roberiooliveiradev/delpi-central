# ROADMAP.REBASELINE.R1 — Inventário E1–E29, gate E10 e readiness E11

**Data:** 2026-10-23 · **BASE HEAD:** `da1794d68d` (= `origin/main` no momento do inventário)
**Escopo:** reconciliação documental + verificação read-only. **Nenhum código, contrato, permission, migration, flag ou deploy foi alterado.**

> Documento de consolidação: aponta para as fontes canônicas existentes (não as substitui). Em conflito, `IMPLEMENTATION-PLAN.md` + ADRs + código HEAD vencem.

## Executive summary

- **E1–E9 concluídas** com gates registrados (E9 com FAIL→recovery→PASS documentado).
- **E10 / WF-15 Controle de Estoques: gate promovido para `PASS_DEPLOYED`** — o bloqueio histórico (bundle federado sem `InventoryPage`) está superado: o bundle servido hoje (`App-SSmBJjdj.js`) contém `stock-balances`, as rotas BFF respondem 401 protegidas em runtime e os testes focados passam. Residual honesto: `VISUAL_AUTHENTICATED = INCONCLUSIVE`.
- **E13/E14 (Fornecedores/360) IMPLEMENTADAS** com increments X4 (cadastro assistido, PUT, catálogos) e `SUPPLIERS.NAV.S1` (navegação contextual). Writes produtivos Protheus: **OFF** (X4.PROD-C1 `WAITING_ON_TOTVS_OWNER`).
- **USERS.PROFILE.S1–S3 fechadas** — ficha `/users/:userId`, avatar/nome navegáveis, tabela real de SC (review GPT `0a78362081`: `ACCEPT_WITH_RESIDUAL`).
- **E11 / WF-16 Estoque de Segurança: `READY_WITH_RESIDUAL`** — contratos de produtor completos em api-delpi, app legado `estoque-seguranca` de referência, rota `/apps/supplies/safety-stock` já no manifest; faltam BFF em `supplies-api`, página MFE e decisão de escopo vs E12.
- **E12–E29 reconciliadas** — nenhuma redundante; C1→C2→paridade→C3 preservado.
- **X4.PROD-C1 preservado** — `G8 = FAIL`, flags de escrita OFF, aguardando Gabriel/TOTVS.

## Matriz E1–E29

| E | WF | Página/capacidade | Rota | Owner | Estado doc | Estado HEAD | Runtime | Gate | Evidência | Residual / próxima ação |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | — | Descoberta + freeze | — | repo | COMPLETED | PROVEN | — | PASS | plan §E1 | — |
| E2 | — | supplies-api foundation/AuthZ | — | supplies-api | COMPLETED | PROVEN | container healthy | PASS | plan §E2 | — |
| E3 | — | MFE + RBAC coexistência | shell | plugins/supplies | COMPLETED | PROVEN | `delpi-supplies` Up | PASS | plan §E3 | — |
| E4 | WF-01 | Home + Ajuda + Perfil | `/` | supplies | COMPLETED | PROVEN (Atenção removida P3; guard test `Home.noAttention`) | bundle servido | PASS | `Home.noAttention.test.ts` | HOME-ATTENTION sem fonte canônica de tarefas — não reativar |
| E5 | WF-02/02R | Overview + OTD analytics | `/overview`, `/analytics/otd` | supplies-api | COMPLETED | PROVEN | servido | PASS | plan §E5 | — |
| E6 | WF-04 | Solicitações C1 + detalhe | `/purchase-requests`, `/purchase-requests/:b/:n` | PR-api→supplies-api | COMPLETED | PROVEN | servido | PASS | plan §E6; smoke federado INCONCLUSIVE (histórico) | identidade/foto/perfil entregues via PR.IDENTITY.S1–S4 + USERS.PROFILE.S1–S3 |
| E7 | WF-05 | Pedidos de compra | `/purchase-orders` | supplies-api | COMPLETED | PROVEN | servido | PASS | plan §E7 | link fornecedor via SUPPLIERS.NAV.S1 |
| E8 | WF-06 | Detalhe do pedido | `/purchase-orders/:b/:n` | supplies-api | COMPLETED | PROVEN | smoke federado PASS 2026-09-21 | PASS | e8 evidence | residual: 403 unidade não exercitado |
| E9 | WF-07 | Entregas/atrasos | `/deliveries` | supplies-api | COMPLETED | PROVEN | servido | PASS (após recovery) | e9 evidence | — |
| E10 | WF-15 | Controle de Estoques | `/inventory` | supplies-api + api-delpi | IN PROGRESS→**promovido** | PROVEN (S1–S3 ancestrais) | bundle contém `stock-balances`; rotas 401 protegidas | **PASS_DEPLOYED** · `VISUAL=INCONCLUSIVE` | e10 evidence + re-verificação R1 | smoke autenticado pendente |
| E11 | WF-16 | Estoque de Segurança | `/safety-stock` (manifest, placeholder) | supplies-api (a compor) | PLANNED | contratos produtor PROVEN | legado `estoque-seguranca` Up | READINESS ver §E11 | este doc | promover via E11.P0 (§abaixo) |
| E12 | WF-17 | Análise de Consumo | `/safety-stock/consumption-analysis` | api-delpi (contrato existe) | PLANNED | contratos `consumption-analysis/*` PROVEN | legado `analise-consumo` existe | TO_INVENTORY→READY parcial | api-delpi router | satélite de E11; mesma janela de dados |
| E13 | WF-09 | Fornecedores lista | `/suppliers` | supplies-api | IMPLEMENTADA | PROVEN | servido | PASS funcional | FORNECEDORES-RETOMADA | — |
| E14 | WF-10 | Fornecedor 360 + cadastro/edição | `/suppliers/:code/:store`, `/suppliers/new` | supplies-api + api-delpi | IMPLEMENTADA | PROVEN | servido; writes só TST | PASS funcional (TST) | X4-* docs | cutover produtivo **BLOCKED** (X4.PROD-C1) |
| E15 | WF-11 | OTD Fornecedores | `/suppliers/otd` | api-delpi `purchase-order-otd*` | PLANNED | contratos `purchase-order-otd{,/panel,/series}` existem | — | TO_INVENTORY | api-delpi routes | depende P-03 (paridade BI) p/ fechar semântica |
| E16 | WF-12 | Produtos / MP | `/products` (placeholder) | api-delpi `product_routes` | PLANNED | `/products{,/search,/{code},/inventory-blocks,/physical-locations}` existem | — | TO_INVENTORY | product_routes.py | escopo de lista p/ MP a definir |
| E17 | WF-13 | Produto 360 | `/products/:code` | api-delpi `product_routes` | PLANNED | `/{code}/*` rico: summary/stock/safety-stock/suppliers/last-purchase/pricing… | — | TO_INVENTORY | product_routes.py | composição 360 p/ recorte |
| E18 | WF-14/19 | Onde Usado + Histórico Preços | `/products/:code/where-used`, `…/price-history` ou seção 360 | api-delpi | PLANNED | `/{code}/parents` + `/{code}/purchase-price-history` + `…/purchase-budget-history` existem | — | TO_INVENTORY | product_routes.py | **P-15 aberto**: página vs seção — decidir com evidência |
| E19 | WF-18 | Savings/Negociações | `/negotiations` (placeholder) | a inventariar | PLANNED | sem contrato dedicado localizado | — | TO_INVENTORY | — | provar fonte antes de promover |
| E20 | WF-20 | Indicadores | `/indicators` (placeholder) | a inventariar | PLANNED | — | — | TO_INVENTORY | — | **P-14 aberto**: provar valor ≠ Overview/SI |
| E21 | WF-03 | Minhas Atividades | `/my-tasks` | a inventariar | PLANNED | nav existe; sem fonte canônica de tarefas | — | TO_INVENTORY | HOME-ATTENTION.P3 | bloqueado por fonte de tasks (mesmo motivo que removeu Atenção) |
| E22 | WF-21 | Administração | `/administration` (placeholder) | supplies | PLANNED | shell adm existe | — | TO_INVENTORY | — | conteúdo a definir |
| E23 | — | Auditoria Help/onboarding | — | supplies | PLANNED | help sincronizado por página | — | PENDING | HELP-AND-ONBOARDING | roda após páginas finais |
| E24 | — | Paridade inicial C1 | — | supr.+BI | PLANNED | HOMOLOGACAO-PARIDADE | — | BLOCKED | P-01/P-03/P-04/P-07 | aguarda dumps/BI |
| E25 | — | PR C2 (single-writer) | — | purchase-requests-api | PLANNED | E25.S1–S5 descritas | — | BLOCKED | **P-10** parcial (janela/volumes/rollback abertos) | runbook antes de E25 |
| E26 | — | Paridade final pós-C2 | — | supr. | PLANNED | — | — | BLOCKED | E25 | sequência canônica |
| E27 | — | Preparar cutover C3 | — | supr.+infra | PLANNED | CUTOVER-RUNBOOK | — | BLOCKED | E26 | — |
| E28 | — | Cutover C3 | — | supr.+infra | PLANNED | — | — | BLOCKED | E27 | — |
| E29 | — | Verify-final | — | supr. | PLANNED | — | — | BLOCKED | E28 | — |

## E10 — re-verificação e decisão de gate

Histórico: `E10.S4 = INCONCLUSIVE` porque o bundle federado não continha `InventoryPage` (`DEPLOY_REQUIRED=YES`).

Evidência nova nesta task (read-only):

- **Ancestralidade:** S1 `abf47ec1cb`, S2 `379ac45937`, S3 `1970fb9150` → todos ancestrais do HEAD.
- **Código:** `features/inventory/` completo (Page, Filters, ListTable, query, content) + rotas `inventory` no router + BFF `GET /inventory/stock-balances/{summary,items}`.
- **Runtime (2026-10-23):** bundle servido `App-SSmBJjdj.js` contém `stock-balances` (3×) e «Estoques»; `delpi-supplies-api` responde **401** nos dois endpoints (registrados + protegidos).
- **Testes focados:** `features/inventory` + structural → **23 passed**; suíte BFF inventory já registrada (12 pass) + suíte completa 481 pass neste HEAD.
- **BFF autenticado local** (evidência S4): PASS — Todas/01/02/03→422, negativo/zero/UM null amostrados.

**`E10_GATE_DECISION`: `GATE-FEATURE E10 = PASS_DEPLOYED`** — código+contrato+deploy+rotas protegidas comprovados. Residual formal: `VISUAL_AUTHENTICATED = INCONCLUSIVE` (nenhum smoke autenticado em browser; não inferido). Recomenda-se o fechamento formal via clique autenticado pelo PO na próxima sessão disponível — sem isso, E10 permanece `ACCEPT_WITH_RESIDUAL`, não `REWORK`.

## E11 — readiness WF-16 Estoque de Segurança

**`E11_READINESS = READY_WITH_RESIDUAL`**

### Source → Owner → Contract → BFF → MFE → Evidence

| Camada | Estado | Evidência |
|---|---|---|
| Regras ESTSEG (ideal/consumo/lead-time/cobertura/projeção) | **Owner: api-delpi** — services `safety_stock_*` (consumption, shortage_30d, unit_conversion, purchase_coverage, stock_projection) | `api-delpi/app/application/services/supplies/safety_stock_*` |
| Contratos produtor | **PROVEN completos:** `/supplies/safety-stock{,/filters,/summary,/items,/items/{code}/details,/items/{code}/suppliers,/consumption-analysis/{summary,items,/items/{code}},/items/{code}/suppliers/{sup}/purchase-price-history}` | `safety_stock_router.py` + ~14 test files |
| AuthZ produtor | `BranchAccessGate` + `SAFETY_STOCK_BRANCH_VIEW_PERMS` por filial | `safety_stock_branch_access.py` |
| App legado de referência | `plugins/estoque-seguranca` (MFE standalone `delpi-estoque-seguranca`, Up em runtime) — `SafetyStockPage` + `ConsumptionAnalysisPage`, chama api-delpi **direto** (`/apps/api-delpi/...`), permission `estoque-seguranca.access` | `plugins/estoque-seguranca/` |
| Rota Portal | `/apps/supplies/safety-stock` **já no manifest** (`supplies.access`, `showInMenu:false`); view `safety_stock` = placeholder "deep link legado" | `supplies.manifest.json:99`, `App.tsx:49` |
| BFF supplies-api | **AUSENTE** — nenhuma rota `safety-stock` | grep rotas = 0 |
| MFE supplies | **AUSENTE** — sem `features/safety-stock/` | fs |

### Residuais a resolver na promoção (não aqui)

1. **Filtro de filial (decisão PO):** filial em Suprimentos é exclusivamente filtro de dados, sem autorização por filial e sem `supplies.unit.*`. Inventariar `SAFETY_STOCK_BRANCH_VIEW_PERMS` como regra do produtor/legado e propor contrato de consulta E11 compatível com `supplies.access` e filtro `branch`, sem propagar permissões por filial ao BFF. Divergências de autorização upstream exigem decisão explícita do owner; não contornar guardas silenciosamente.
2. **Boundary MFE:** legado chama api-delpi direto com `estoque-seguranca.access`; no Portal o padrão é BFF-only com `supplies.*` — a promoção exige composição nova em `supplies-api`, **não** importar código do plugin legado.
3. **Escopo E11 vs E12:** `consumption-analysis/*` tem página própria na fila (linha 9) — E11 deve ficar na posição ESTSEG (summary/items/details/suppliers); consumo entra como E12 satélite ou link.
4. **Item details/suppliers/price-history** sobrepõem E17/E18 — manter na ficha do item do ESTSEG sem duplicar o Product 360.
5. **Indicadores** (cobertura, ruptura 30d, projeção) dependem de homologação funcional dos services api-delpi antes de expor.

### Receita proposta — E11.P0 e fatias (NÃO autorizada ainda)

- **E11.P0** — Contract freeze: inventariar envelopes/filtros/paginação do produtor, confirmar filial somente como filtro (sem `supplies.unit.*`), reconciliar eventual `BranchAccessGate` de ESTSEG com o owner correto, decidir escopo (ESTSEG somente) e documentar RQ/AC.
- **E11.S1** — BFF `supplies-api`: `GET /safety-stock/{filters,summary,items}` (+ `items/{code}/details`, `items/{code}/suppliers` se no recorte) — gateway api-delpi, `can_use_operations` + `require_units`, paginação limitada, degrade parcial.
- **E11.S2** — MFE página kit-first `/safety-stock`: filtros (unidade/grupo/busca do contrato `/filters`), summary hero, tabela com sort/paginação server-side, URL/F5, estados completos.
- **E11.S3** — Ficha do item (details + linked suppliers) se aprovada em P0; link para Product 360 futuro via `product_code` somente se contrato existir.
- **E11.S4** — Help sync (saldo disponível ≠ físico ≠ ESTSEG), testes, `userManualContent`, FAQ.
- **E11.S5** — Suites + gate + deploy + smoke; `VISUAL` conforme evidência.

RQ mínimos: vínculo unidade (positive/sibling/negative), paginação, empty/partial/error/403/404, zero N+1, "Ver análise de consumo" como link (se E12 não entregue → esconder).

## Dependências E12–E29

- **E12** depende de E11 (mesmo contexto/rota-pai); contratos já existem — `READY` parcial quando E11 abrir o caminho BFF.
- **E15** tem contratos `purchase-order-otd{,/panel,/series}` — bloqueio semântico **P-03** (paridade BI Atraso/OTD) antes do aceite, não da construção.
- **E16/E17** produtor rico já existe (`/products/*`, `/{code}/*`) — `TO_INVENTORY`; promover E16→E17 na ordem.
- **E18** — **P-15 aberto**: página própria vs seção do Product 360; `parents` + `purchase-price-history` prontos.
- **E19/E20** — sem fonte comprovada; **P-14** deve provar valor distinto do Overview/SI.
- **E21** — bloqueado pela mesma causa do HOME-ATTENTION.P3: não existe fonte canônica de tarefas atribuídas.
- **E22** — conteúdo administrativo a definir.
- **E23** — auditoria final, após páginas.
- **E24–E29** — cadeia C1→C2→paridade→C3 preservada; **P-10** abre E25; X4.PROD-C1 independente mas igualmente bloqueado por TOTVS.

Nenhuma etapa redundante identificada; ordem canônica mantida.

## Bloqueios externos preservados

- **X4.PROD-C1** (`WAITING_ON_TOTVS_OWNER`, `G8=FAIL`): POST/PUT homologados em `DELPI_TST01`; rota produtiva `192.168.1.231:8061/restall` 404 + credencial 401; `PROTHEUS_SUPPLIER_CREATE/UPDATE_ENABLED=false`; `AMBIENTE=1` ainda resolve TST (transitório intencional). Handoff: `X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md`. **Intocado.**
- **P-01/P-03/P-04/P-07** — dumps/BI de produção pendentes (paridade).
- **P-06** — alçada sem workflow comprovado.
- **P-10** — janela/volumes/rollback C2 abertos.
- **P-11** — Qualidade fora do Supplier 360.
- **P-14/P-15** — Indicadores e Histórico de Preços a decidir com evidência.

## Drifts encontrados e corrigidos nesta task

| Drift | Correção |
|---|---|
| README/PLAN declaravam `E10 GATE INCONCLUSIVE` por "bundle sem InventoryPage" — **superado** pelo deploy posterior | Gate reclassificado `PASS_DEPLOYED` com residual visual; README/PLAN/API-ROUTES atualizados |
| API-ROUTES sem `GET /users/{id}/related-requests` e `GET /users/{id}/photo` (entregues em USERS.PROFILE.S1–S3) | rotas adicionadas |
| README "próxima receita = deploy E10; não iniciar E11" — obsoleto | atualizado para readiness E11 |
| Página `/deliveries` marcada "bloqueada até autorização PO" na fila — **já FECHADA** (E9 GATE PASS) | corrigido na tabela de fila |
| Linhas 7–10 da fila ("fila") desatualizadas vs estados reais | reconciliadas (inventory fechada c/ residual visual; suppliers fechadas) |

## Sequência recomendada

1. **Próxima task (proposta):** `E11.P0` — contract freeze Estoque de Segurança (read-only, produzir matriz de campos + decisão AuthZ filial + recorte vs E12/E17/E18).
2. Smoke autenticado E10 (clique do PO) fecha o residual visual — não exige task.
3. Resposta Gabriel/TOTVS → reabrir X4.PROD-C1 por handoff próprio.
4. C2 (E25) somente após P-10 fechar janela/volumes/rollback.

## Handoff para novo chat/Cursor

- Ler primeiro: este doc → `IMPLEMENTATION-PLAN.md` → `README.md` → `X4-PROD-C1-HANDOFF-*` (se tocar fornecedores/write).
- Ficha do usuário: `/apps/supplies/users/:userId` (USERS.PROFILE.S1–S3). Tabela de SC reutilizável: `PurchaseRequestsListTable`.
- Navegação contextual: `SuppliesPersonIdentity`/`SuppliesSupplierIdentity` (SUPPLIERS.NAV.S1).
- AuthZ: permissions efetivas da Core para acesso/capacidades (`supplies.access`, `supplies.manage` quando cabível), sem permission por filial; `branch` é filtro de dados (ADR-009). O BFF mantém AuthZ server-side fail-closed para capacidade, recurso e regras aplicáveis.
- Writes ERP: **OFF** — flags `PROTHEUS_SUPPLIER_*_ENABLED=false` até Gabriel/TOTVS.

## Arquivos inspecionados (amostra de evidência)

`IMPLEMENTATION-PLAN.md`, `README.md`, `WIREFRAMES.md`, `API-ROUTES.md`, `DIRECTORY-OBJECTS.md`, `DECISOES_FUNCIONAIS_PENDENTES.md`, `HELP-AND-ONBOARDING.md`, `X4-PROD-C1-HANDOFF-*`, `e10-wf15-s4-final-acceptance.md`, `product_routes.py`, `safety_stock_router.py`, `safety_stock_branch_access.py`, `plugins/estoque-seguranca/` (pages+api), `plugins/supplies/src/features/{inventory,...}`, `pluginRoutes.ts`, `supplies.manifest.json`, `App.tsx`, `inventory_routes.py`.


## Revisão GPT — ROADMAP.REBASELINE.R1 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para o inventário/documentação; `E10=PASS_DEPLOYED` (não `GATE-FEATURE PASS` integral); `E10_VISUAL_AUTHENTICATED=INCONCLUSIVE`; `E11=READY_WITH_RESIDUAL`; `E11.S1=NOT_AUTHORIZED`. Inspecionados este documento e `README.md` no SHA `b3e1fc46b7`. A evidência reportada de E10 (ancestralidade, bundle servido com `stock-balances`, 401 em rotas protegidas, 23 testes focados) supera o bloqueio histórico de **ausência do bundle**; o runtime autenticado em navegador continua sem prova, portanto não equiparar presença de bundle ou 401 a DoD integral. Os probes/testes foram informados pelo executor e não reexecutados nesta revisão GPT.

**Inconsistências materiais para E11.P0:** o README vigente declara expressamente na seção 5 que unidade do Portal é filtro de dados `01/02` e **não** `supplies.unit.*`, enquanto este R1 recomenda mapear `SAFETY_STOCK_BRANCH_VIEW_PERMS` para `supplies.unit.filial-*`. A formulação da receita E11 não deve cristalizar essas permissions sem authority da Core/ADR no HEAD; tratar como `TO_INVENTORY / CONTRACT_DECISION_REQUIRED` e resolver a interseção `capability AND unit_scope AND resource_scope AND business_rule` em E11.P0. O app legado ter `estoque-seguranca.access` tampouco significa que o usuário com `supplies.access` recebe automaticamente o mesmo universo de dados.

**Drift documental residual comprovado:** `README.md` §7 \"Próximo passo operacional\" ainda ordena deploy E10, re-smoke e \"Não iniciar E11\", em conflito com o cabeçalho e a fila R1; §\"Atualização bounded — enriquecimento\" repete E10 em foco. Não reescrever evidência histórica; marcar como histórico superado ou corrigir a instrução ativa no próximo commit documental escopado. A contagem e classificação E1–E29 permanecem úteis como matriz de planejamento, não autoridade superior a contratos/HEAD. Cuidado também com a afirmação de `E10.S4 PASS`: registrar que o S4 histórico foi `INCONCLUSIVE` e que o bloqueio foi **revalidado posteriormente** por R1, sem reclassificar retroativamente o resultado original.

**Próxima tarefa aprovada para proposta (não execução automática):** `E11.P0` exclusivamente read-only/contract freeze: verificar source e grants por filial no HEAD, distinguir unidade Core de gate ESTSEG, definir escopo exato E11 vs E12/E17/E18 e congelar RQ/AC e endpoints antes de qualquer implementação. `X4.PROD-C1` permanece WAITING_ON_TOTVS_OWNER; CREATE/UPDATE OFF; nenhum cutover ou deploy autorizado por este parecer.


## Decisão explícita do Product Owner — Filial é filtro, não autorização (2026-10-23)

**Decisão canônica de produto para o Portal Suprimentos:** filial (`01`, `02`, etc.) é **filtro de consulta**, nunca uma permission ou restrição de visibilidade específica por filial. **Não criar, exigir, traduzir ou registrar no manifest** `supplies.unit.*`, `supplies.unit.filial-*` ou equivalentes. A autorização do Portal é por capacidades efetivas da Core e, onde aplicável, recurso/ownership/regra de negócio — não autorização por filial. Essa decisão corrige as propostas anteriores deste documento que indicavam mapeamento de `SAFETY_STOCK_BRANCH_VIEW_PERMS` para permissões de Suprimentos; esses trechos históricos devem ser lidos apenas como drift já reconciliado.

**Manifest verificado:** `plugins/supplies/supplies.manifest.json` não contém `supplies.unit.*` nos campos inspecionados; **nenhuma alteração de manifest necessária nessa verificação**. A existência de `SAFETY_STOCK_BRANCH_VIEW_PERMS` no `api-delpi`/aplicativo ESTSEG é fato de outro boundary e exige inventário de impacto e contrato no E11.P0; não autoriza bypass de checks upstream sem decisão do owner. E11.P0 deve documentar como expor os filtros de filial coerentemente com esta regra. Nenhum código, permissão ou runtime foi alterado nesta decisão documental.
