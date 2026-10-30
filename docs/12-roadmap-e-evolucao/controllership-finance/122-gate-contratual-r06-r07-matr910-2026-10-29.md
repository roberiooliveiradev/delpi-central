# 122 — Gate contratual R06/R07 (MATR910: CPV/Kardex e Inventários) — 29/10/2026

**Execução:** `CF-PROC0072-R06-R07-CONTRACT-GATE-014` — pacote 014 do doc 120.
**Natureza:** READ → VERIFY → CLASSIFY → CONTRACT → GATE → REPORT. **Documental, sem runtime.**
**Estado:** `TARGET` — contratos e RQ/AC prontos para aprovação; **implementação bloqueada** até gate de execução explícito (§12).
**HEAD de referência:** `2ff0ae240b` (main, local; 1 commit à frente de `origin/main` `07b1f9fa21` — commit de docs do workstream engineering, fora do escopo).
**Autoridades:** doc 118 (processo), doc 85 §6/§7 (regras BR-R06/BR-R07 — `PROVEN`), doc 83 (crosswalk/evidência), doc 84 §5.1 (paridade monetária), doc 80 §37–39 (provas linha-a-linha), `matr910_dlp.prx` (fonte no acervo — `SOURCE_AVAILABLE`), doc 117 (AS-IS operadora), doc 119/121 (contratos vigentes e paridade Portal×CLARA), HEAD (implementação), TÉO (AS-IS/proveniência).

---

## 1. Preflight e concorrência

- **HEAD local/remoto:** `2ff0ae240b` local × `07b1f9fa21` `origin/main` — divergência = 1 commit documental local (`engineering` master plan), 0 commits atrás. Sem overlap com este pacote.
- **Concorrência:** ~48 entradas em `git status`; classificadas e **preservadas intocadas**: (a) worktrees `.worktrees/*` e worktrees externos (`cf-*-wt`, `davi-*-wt`) de workstreams ativos; (b) 1 arquivo modificado fora do escopo (`delia-api/scripts/local_orchestration_reliability_eval.py`); (c) artefatos acidentais de comando na raiz (arquivos soltos tipo `forged`, `token`, `nul`, diretórios `docs/`, `plugins/` fragmentados) — não são deste pacote; (d) untracked sob pacotes (`api-delpi/`, `plugins/` etc.) — cópias fragmentadas, não fonte de verdade.
- **Baseline CLARA reconfirmado no HEAD** (não só na documentação): `interface/mcp/server.py` + `tool_bridge.py` + `constants.py` = **43 tools** congeladas por `MCP_TOOL_NAMES`, travadas por `test_clara_mcp_surface.py` e `test_clara_parity_016.py`; identidade delegada (Bearer do usuário → `mcp_transport_auth` → `delpi_auth` → bearer forwarding ao api-delpi) confirmada no código. **Nenhuma tool de kardex/CPV/INVENT existe** — correto, gate ainda não implementado.
- **Baseline Portal reconfirmado:** `REPORT_CATALOG` (`reports_routes.py:90-107`) tem R06/R07 `PENDING_CONTRACT`; rotas `closing/stock-inventory`, `closing/stock-movements`, `closing/work-in-process`, `closing/financial-settlements` implementadas (molde a reutilizar).
- **Drift de corpus detectado neste gate:** `corpus_manifest.py` marcava `doc-61→R05`, `doc-62→R06`, `doc-63→R07` enquanto o catálogo canônico mapeia MATR320→**R05**, P7→**R03**, CPV/Kardex→**R06**, INVENT→**R07**. Corrigido neste pacote documental (§8 D-08) — tag herança do mapeamento de slots do checklist ciclo-1.

## 2. D1 — Inventário direcionado e matriz de reuso

Produtor oficial dos dois relatórios: **MATR910** (`matr910_dlp.prx`, `SOURCE_AVAILABLE`; versão RPO `PENDING` — E7 externo TI/ERP). R07 é o mesmo relatório filtrado a `D3_DOC='INVENT'` — **não é MATR460** (E2 continua sobre R03/P7, sem relação com R07).

| # | Elemento | Evidência | Owner | Veredito | Gaps |
|---|----------|-----------|-------|----------|------|
| 1 | `GET /supplies/cpv` — CPV canônico | `supplies_router.py:89-132`; `cpv_query_repository.py`; `get_cpv_use_case.py`; doc 85 BR-R06-010 | api-delpi/supplies | `REUSE_PARTIAL` (semântica) | auth `KPI_SUPPLIES_ACCESS` (não S2S do fechamento); floats; sem parity/provenance; custo corrente (PO 23/10: **correto para CPV vivo**, não lacuna); CFOPs fixos |
| 2 | Engine R05 `stock_movements` (UNION SD1+SD2+SD3, filtros SF4) | `financeiro_stock_movements/stock_movements_sql.py`; rota `/financeiro/stock-movements` | api-delpi/financeiro | `REUSE_PARTIAL` (padrão UNION + moldes de filtro) | grão = tipo de material agregado, não produto×linha com cadeia de saldo |
| 3 | Padrão governado P7/H02 (S2S+flag+snapshot+parity+export) | `stock_inventory_router.py`, `work_in_process_router.py`, `s2s_service_access.py`, `report_export_common.py` | api-delpi/financeiro | `REUSE_CONFIRMED` (molde arquitetural) | — |
| 4 | `GET /supplies/inventory-adjustments` (+`/summary`, `D3_DOC='INVENT'`) | `inventory_adjustments_router.py`/`repository.py` (`_BASE_WHERE` INVENT, natureza por CF DE0/RE0, SB7 fail-closed) | api-delpi/supplies | `REUSE_PARTIAL` (seleção INVENT + natureza) | auth divergente (`API_DELPI_ACCESS`); sem laço de saldo/custo `as_of`; sem parity/provenance do contrato governado |
| 5 | Classificação canônica SD3 (`INVENTORY_ADJUSTMENT_DOCUMENT`, `classify_internal_movement`) | `domain/totvs/protheus_internal_movements.py` | api-delpi/domain | `REUSE_CONFIRMED` (regra de domínio) | — |
| 6 | Estimador SB9+SD3 histórico | `stock_value_historical_sql.py` | api-delpi/supplies | `REUSE_PARTIAL` | estimativa sem TES/doc/estorno refinado |
| 7 | P7 engine SB9 `B9_DATA` exata | `stock_inventory_sql.py` (`snapshot_branch_counts`, `closing_balance_by_type`) | api-delpi/financeiro | `REUSE_CONFIRMED` (mecânica de saldo inicial @mês anterior) | — |
| 8 | `internal-movements` por produto | `product_routes.py:1390` | api-delpi | `REUSE_PARTIAL` | só SD3, sem SD1/SD2, custo ou cadeia |
| 9 | Kardex por produto com cadeia de saldo + custo `as_of` + REF | **inexistente** | — | `TO_INVENTORY → TARGET` (contrato `stock-kardex`, §4) | nenhum repo lê **TTAT**/log de custo `as_of` hoje |
| 10 | Ranking global por impacto (CPV/custo) | `top_products`/`top_documents` no use case CPV | api-delpi/supplies | `REUSE_PARTIAL` | ranking deve operar no **conjunto autorizado completo**, não na página (requisito §12 doc 121) |

**Conclusão D1:** não existe motor de kardex implementado; não criar segundo motor. Caminho = **um engine `stock-kardex`** no contexto financeiro da api-delpi (molde R03/R05/R08), reutilizando regras de domínio existentes; R07 = mesma engine com `document_kind=INVENT`. CPV = semântica canônica existente exposta pela família governada (D-O1).

## 3. D2 — Matriz de paridade (artefatos × dados/contratos)

Estado **pré-implementação** — evidência histórica de reconstrução (docs 80/83/84/85) já comprovada; comparação de contrato implementado será gate futuro (G6 permanece independente).

| Dimensão | R06 (`cpv 09 26 matriz.xlsb`) | R07 (`Invent.xlsb`) | Estado |
|---|---|---|---|
| População | 1.544 blocos produto / 9.357 movimentos — **só produtos com movimento** (mv_par07=Não) | 45 linhas `D3_DOC='INVENT'` (32×999 + 13×499) | `PASS` (reconstrução) |
| Vínculo linha-a-linha | 9.357/9.357 ao UNION SD1/SD2/SD3 | 45/45 ao SD3 (35 direto + 10 via `TTAT_OLD`) | `PASS` |
| Datas | SD1 `D1_DTDIGIT` · SD2 `D2_EMISSAO` · SD3 `D3_EMISSAO` (281 casos dig≠emi) | `D3_EMISSAO` | `PASS` |
| Ordem | data + `D3_NUMSEQ` (1.971/1.971 grupos) | idem | `PASS` |
| REF | `F-` 260/260 · `P-` 594/594 · `OP` 6.060/6.060 · `CC` ~2.443 | n/a (SD3) | `PASS` |
| Custos | `as_of` emissão: 7.376 `CUR` + 1.981 `TTAT_OLD` = 100% | `D3_CUSTO1` `as_of` (10 via TTAT_OLD) | `PASS` |
| Sinal/devoluções | `TIPONF='D'` coluna oposta ×−1 — 11/11 linhas | TES 499=entrada(+), 999=saída(−) | `PASS` |
| Saldo inicial | `B9_QINI`/`B9_VINI1` @2026-08-31 — 1.544/1.544 | mesma cadeia | `PASS` |
| Cadeia de saldo | linha-a-linha contínua — 1.544/1.544 | por linha impressa | `PASS` |
| Totais oficiais | agregados do kardex **não são** CPV | entradas 2.348,108 / R$185.103 · saídas 30.808,206 · líquido −28.460,098 | `PASS` |
| Saldo final × SB9 corrente | 354 produtos Δvalor (SB9 regravado pós-recálculo) | — | `STALE_EVIDENCE` (drift, não erro) |
| Versão RPO/parâmetros efetivos | E7 externo | E7 externo | `PENDING` |
| **Contrato implementado × artefato** | endpoint ainda não existe | endpoint ainda não existe | `TEST_NOT_RUN` — gate futuro |
| Aceite humano | G1–G5 `PASS` · **G6 `PENDING`** | G1–G5 `PASS` · **G6 `PENDING`** | — |

**Nota AS-IS (doc 117 ANL-016/017):** a prévia CPV da operadora filtra CF `501,524,601,624` (filtro de tela, destino Fiscal) — **não** confundir com os CFOPs do CPV canônico `5101,5124,6101,6124`. Inventário: arm. 99, marcador `INVENT`, Σentradas−Σsaídas; demais armazéns omitidos por imaterialidade.

## 4. D3 — Contratos TARGET (api-delpi → BFF → MFE → CLARA)

### 4.1 api-delpi — família `financeiro_stock_kardex` (owner técnico; owner funcional Controladoria)

Um único engine; três leituras + medida CPV. Molde obrigatório = família governada R03/R05/R08 (S2S dedicado + flag + dataset scope + provenance/parity + export + erros tipados). **Invariantes:** sem SQL no BFF/MFE/CLARA; `NOLOCK` + `D_E_L_E_T_=''`; sem permissão nova no Portal; `UNAVAILABLE`/`source_missing` nunca vira zero.

| Rota TARGET | Parâmetros | Saída | Observações |
|---|---|---|---|
| `GET /financeiro/stock-kardex` | `period`(YYYY-MM, req) · `branch`(all\|01\|02) · `warehouse`(multi, opc; evidência R06=01) · `product_code`? · `document_kind`(ALL\|INVENT) · `page`,`page_size` (tier `page_50_200`) · `sort`(allowlist: `date`+`numseq` default, `value_out`,`value_in`,`quantity`,`cost`,`balance`,`product`) | `items[]` grão **movimento** dentro de bloco produto×armazém; `blocks[]` com `initialBalance{qty,value}` e `finalBalance` | UNION SD1(DTDIGIT)+SD2(EMISSAO)+SD3(EMISSAO); `F4_ESTOQUE='S'` só SD1/SD2; `D3_ESTORNO<>'S'`; `ORIGLAN<>'LF'`; `SB1.B1_COD<>MV_PRODIMP`; REF decodificado; devolução `TIPONF='D'` ×−1; custo `as_of` = `TTAT_OLD` senão corrente |
| `GET /financeiro/stock-kardex/summary` | `period`,`branch`,`warehouse` | totais entrada/saída (qtd+valor), por armazém e por `B1_TIPO`, `topProductsByCost` **global server-side**, `movementCount`, CPV vivo (D-O1) | agregados do kardex ≠ CPV — resposta separa `kardexOutputs` de `cpv` |
| `GET /financeiro/stock-kardex/products/{code}` | `period`,`branch`,`warehouse` | bloco completo do produto com cadeia de saldo linha a linha | drill-down por produto |
| `GET /financeiro/inventory-adjustments` | `period`,`branch`,`warehouse`(multi; evidência 01+99),`product_code`?,`nature`(ENTRY\|OUTPUT),`page`,`page_size`,`sort` | ajustes SD3 `D3_DOC='INVENT'` com sinal/TES (999/RE0 saída, 499/DE0 entrada), `D3_CUSTO1` `as_of`, proveniência | mesma engine; SB7 como proveniência **não-autoridade** opcional (fail-closed, molde supplies existente) |
| `GET /financeiro/inventory-adjustments/summary` | `period`,`branch`,`warehouse` | entradas/saídas/líquido por filial/armazém; `adjustmentCount`; `topImpacts` global | — |
| `GET /financeiro/cpv` (D-O1) | `period`,`branch` | `cpv_total`, `cpv_percentage`, `by_cfop`/`by_tm`, `top_products`,`top_documents` | **reuso da semântica** de `GetCPVUseCase`/`CpvQueryRepository` (mesma app, contexto financeiro), exposta sob contrato governado; custo **corrente vivo** por decisão PO 23/10 — `asOfConvention:"live"` |
| `…/export` nas rotas acima (D-O2) | `format=csv\|pdf` | arquivo com bloco de identidade, watermark *«RELATÓRIO OPERACIONAL — PARIDADE OFICIAL PENDENTE»*, SHA-256 `content_hash` | molde `report_export_common.py` |

Campos por linha do kardex (DTO camelCase): `productCode/productName/um/productType`, `warehouse`, `doc`, `movementDate`, `dateField` (`DTDIGIT|EMISSAO`), `sourceTable` (`SD1|SD2|SD3`), `tes`,`tm`,`cfop`, `reference` (`F-|P-|OP|CC`), `movementKind` (`ENTRY|OUTPUT`), `isReturn`, `quantity`, `entryQty`,`entryValue`,`outputQty`,`outputValue`, `unitCost`, `costAsOfSource` (`CURRENT|TTAT_OLD`), `runningQty`,`runningValue`. Bloco: `initialBalance{qty,value,asOfDate,snapshotStatus}` — `B9_DATA` exata do mês anterior; ausente → `status=source_missing` **fail-closed** (molde P7; nunca substituir mês nem fabricar saldo). Envelope: `source`, `provenance{engine:"matr910_contract", officialProducer:"MATR910", snapshotDate, asOfConvention}`, `officialMatr910:false`, `parityStatus:"PENDING"`, `parityNotes`.

**Regra monetária (canônica):** `CAST(... AS DECIMAL(30,9))` por linha antes do SUM (floats `D*_CUSTO*`), saída `DECIMAL(28,6)` serializada como string; exibição 2dp half-up sobre soma não arredondada; tolerância de paridade = **zero** (doc 15.1).

### 4.2 BFF — `controllership-finance-api` (proxy fino, sem recálculo)

| Rota BFF TARGET | Upstream | Gate |
|---|---|---|
| `GET /closing/competences/{period}/reports/stock-kardex` (+`/summary`,`/export`,`/products/{code}`) | `/financeiro/stock-kardex*` | `controllership-finance.access` |
| `GET /closing/competences/{period}/reports/inventory-adjustments` (+`/summary`,`/export`) | `/financeiro/inventory-adjustments*` | `controllership-finance.access` |
| `GET /closing/competences/{period}/reports/cpv` (D-O1) | `/financeiro/cpv` | `controllership-finance.access` |
| `REPORT_CATALOG` (pós-implementação) | R06 → `operational_view:"stock-kardex"`, `source_kind:"OPERATIONAL_VIEW"`, `official_parity:"PENDING"`; R07 → `operational_view:"inventory-adjustments"` | — |

Bearer do usuário repassado (`_user_bearer`) + `X-Delpi-Service-Authorization` da BFF; erros tipados propagados (`_map_gateway_error`); paginação/filtros idênticos ao Portal e à CLARA.

### 4.3 MFE — Central de Fechamento

- Rotas novas `closing/stock-kardex` e `closing/inventory-adjustments` (molde `closing/stock-inventory`): filtros competência/filial/armazém/produto, resumo, tabela paginada, drill por produto, export, proveniência e `official_parity` explícitos; deep link `?tab=reports&report=R06|R07`.
- Reuso obrigatório: `@delpi/plugin-ui`, componentes de tabela/filtro/export dos relatórios existentes, `CfTitleWithHelp`, helpTooltips novas entradas `reports.stockKardex`/`reports.inventoryAdjustments`; sem regra de negócio no MFE.
- Matriz R01–R15: estados só mudam **após** implementação+teste — `PENDING` nunca promovido por existência de rota.

### 4.4 CLARA — tools READ (consumidora obrigatória; 43→**48**)

| Tool TARGET | Delega à rota BFF | Parâmetros |
|---|---|---|
| `get_stock_kardex` | `…/stock-kardex` | `period`,`branch`,`warehouse`?,`product_code`?,`page`,`page_size` |
| `get_stock_kardex_summary` | `…/stock-kardex/summary` | `period`,`branch`,`warehouse`? |
| `get_stock_kardex_product` | `…/stock-kardex/products/{code}` | `period`,`branch`,`product_code`,`warehouse`? |
| `get_inventory_adjustments` | `…/inventory-adjustments` | `period`,`branch`,`warehouse`?,`product_code`?,`nature`?,`page`,`page_size` |
| `get_inventory_adjustments_summary` | `…/inventory-adjustments/summary` | `period`,`branch`,`warehouse`? |

CPV: se D-O1 aprovado, `get_cpv(period,branch)` → 43→48; senão CPV dentro de `get_stock_kardex_summary` → 43→47. Export permanece `PORTAL_ONLY`. Mesma identidade delegada, paginação, erros tipados e `parityStatus` do Portal — **nenhum DTO separado para CLARA** (tools invocam a mesma rota via `_call_route`). Rankings sempre sobre o conjunto autorizado completo (contrato server-side, nunca agregado da página).

## 5. D4 — Matriz de segurança

| Camada | Controle | Detalhe |
|---|---|---|
| Identity | Keycloak/OIDC usuário real | JWT nunca é autoridade final; `aud`/scopes conforme `oauth_contract.py` (MCP) |
| Capability Portal | `controllership-finance.access` (efetiva via Core RBAC) | **sem permission nova**; `.manage` não se aplica (somente leitura); `.access.dre` não vê R06/R07 (dados internos) |
| S2S BFF→api-delpi | `require_s2s_service(scope="stock-kardex.read", allowed_clients=("controllership-finance-api",))` | novo **scope S2S interno** da família (molde `stock-inventory.read`) — não é permissão de usuário |
| Dataset scope | `StockInventoryScopeResolver`/resolver irmão + flag `FINANCEIRO_STOCK_KARDEX_ENABLED` | `scope_unavailable`→403 tipado `recoverable:false`; filial/armazém = **dimensão de dados**, não permission code |
| Delegação MCP | Bearer original → `mcp_transport_auth` → `delpi_auth` → tool re-aplica gate | `require_mcp_context` fail-closed; service tokens proibidos |
| Resource scope | `branch`/`warehouse`/`product_code` validados no produtor | sem SQL arbitrário; sort por allowlist |
| Auditoria | provenance + `operation_id` + `parityStatus` em toda resposta | consulta operacional ≠ relatório oficial |
| Fail-closed | `rbac_unavailable`→503; ausência de snapshot→`source_missing`; sem dado→nulo explícito | nunca zero fabricado |

## 6. D5 — RQ/AC

Ledger completo registrado em **doc 23 — seção `CONTRACT-GATE-014` (RQ-R06-*, RQ-R07-*, RQ-X-*)**: consulta/resumo/detalhe de cada relatório, filtros, ordenação global, paginação, proveniência, erros tipados, segurança, exportação, tools CLARA, corpus/Help, paridade Portal×CLARA e não-regressão R03/R05/R08. Cada AC tem fonte de evidência e verificação objetiva (rota 200 autenticado / 401 anônimo / 403 sem scope / `source_missing` / igualdade de resultado Portal=MCP para mesmos parâmetros / paridade técnica × XLSB).

## 7. D6 — Plano de implementação (sequência mínima)

| Etapa | Escopo | Arquivos-alvo | Testes | Rollback |
|---|---|---|---|---|
| E1 | api-delpi: `financeiro_stock_kardex` (sql/repo/use case/port/route) + TTAT read | `application/use_cases/financeiro_stock_kardex/*`, `infrastructure/persistence/totvs/financeiro_stock_kardex/*`, `interface/http/routes/financeiro/stock_kardex_router.py`, scope resolver, flag | unit SQL (UNION, filtros, TTAT, cadeia), contrato, S2S 401/403 | flag OFF |
| E2 | api-delpi: `inventory-adjustments` governado (mesma engine) + `financeiro/cpv` (D-O1) | idem + reutilizar `CpvQueryRepository`/`GetCPVUseCase` | INVENT 45/45 reconstruído; totais R07 | flag OFF |
| E3 | BFF proxy + `REPORT_CATALOG` | `closing_routes.py`, `reports_routes.py` | rotas BFF, `_map_gateway_error`, 401/403 | revert |
| E4 | MFE views + help + matriz | `src/features/closing/*`, `helpTooltips.ts`, `pluginRouteCatalog.ts` | vitest, a11y, temas, mobile | revert MFE |
| E5 | CLARA tools READ + testes | `mcp/server.py`,`tool_bridge.py`,`constants.py` + tests (`43→48`) | parity 016-style, surface, conformance | revert |
| E6 | Export (se D-O2 aprovado) | `report_export_common` reuse | integridade CSV/PDF, watermark, hash | flag export OFF |
| E7 | Corpus/Help/docs + matriz R01–R15 | `corpus_manifest.py`, ingestão, docs 121/23/README | `test_clara_corpus_parity.py`, busca com citação pós-ingestão | corpus version anterior |
| E8 | Paridade técnica × XLSB (evidência) | scripts de conferência (read-only) | R06/R07 linha-a-linha | — |
| E9 | Deploy sequencial + smoke autenticado + SHA | `infra/scripts/up-prod-sequential.sh` | health, bundle, smoke | git revert + redeploy |

## 8. D7 — Plano de publicação conjunta

Portal + CLARA + corpus + Help + matriz publicados **como uma única entrega** (diretriz permanente §1 do gate): (1) manifest autoriza docs novos/atualizados; (2) `corpus_ingestion --publish` por caminho governado — versão/hash comprovados via `list_knowledge_sources` + buscas com citação (**nunca** editar hash manualmente); (3) tools só se declaram disponíveis após deploy real; (4) matriz R01–R15 reflete estado implementado com `official_parity` independente; (5) Help do Portal e corpus CLARA descrevem limitações (operacional ≠ oficial; `as_of`; sem ajuste de estoque via Portal/CLARA).

## 9. D8 — Registro de decisões

**Fechadas neste gate:**
- **D-01** Owner técnico = contexto `financeiro` da api-delpi; owner funcional = Controladoria; produtor oficial = MATR910 (R06 e R07). `PROVEN`.
- **D-02** Um único engine `stock-kardex`; R07 = mesmo engine com `document_kind=INVENT` (confirma candidato do doc 85 §15). `TARGET`.
- **D-03** Datas assimétricas preservadas (`D1_DTDIGIT`/`D2_EMISSAO`/`D3_EMISSAO`) — condição de paridade. `PROVEN`.
- **D-04** Custo `as_of` por linha via `TTAT_OLD` quando existir, senão corrente (`costAsOfSource` exposto). `TARGET` — acesso TTAT é novo (gap #9 D1).
- **D-05** Saldo inicial = SB9 `B9_DATA` exata do fechamento anterior; ausente → `source_missing` fail-closed. `TARGET`.
- **D-06** CPV vivo (custo corrente) — decisão PO 23/10/2026 registrada em doc 85 BR-R06-010; exposta via família governada. `PROVEN`.
- **D-07** Sem permissão nova; filial/armazém como dimensão de dados. `APPROVED_RULE`.
- **D-08** Correção do drift de tags `doc-61/62/63` no corpus manifest (R05↔R06↔R03) — executada neste pacote documental.

**Pendentes externas (não bloqueiam o contrato):** E7 versão RPO + parâmetros efetivos `mv_par09/10/16` (TI/ERP); classificação `F4_PODER3` no escopo kardex; confirmação do parâmetro de armazém da emissão R07.

**Opções materiais — APROVADAS pelo PO em 2026-10-29** (aprovação em sessão, execução `CF-PROC0072-R06-R07-IMPLEMENTATION-015`, Gate 0; as quatro recomendações técnicas foram aceitas integralmente):
- **D-O1** CPV: **`GET /financeiro/cpv` dedicado** — aprovado.
- **D-O2** Export **CSV e PDF** das duas consultas — aprovado (molde `report_export_common`).
- **D-O3** R07 como view dedicada **`inventory-adjustments`** — aprovado (matriz/deep-link independentes).
- **D-O4** `mv_par20/21` (saldo zero/negativo): **omitir** — população = produtos com movimento.

## 10. Critérios AC-G do gate

| AC | Estado | AC | Estado |
|---|---|---|---|
| G01 HEAD/concorrência | `PASS` §1 | G13 contratos BFF | `PASS` §4.2 |
| G02 instruções/authorities | `PASS` | G14 frontend p/ reuso | `PASS` §4.3 |
| G03 reuso CPV inventariado | `PASS` §2 | G15 CLARA obrigatória | `PASS` §4.4 |
| G04 regras MATR910 confrontadas | `PASS` §2/§3 | G16 tools READ projetadas | `PASS` §4.4 |
| G05 semântica R06 | `PASS` `PROVEN` | G17 corpus/Help | `PASS` §7 |
| G06 semântica R07 | `PASS` `PROVEN` | G18 paridade Portal×CLARA | `PASS` §4.4 |
| G07 grão | `PASS` movimento/bloco produto | G19 matriz AuthZ | `PASS` §5 |
| G08 filtros/datas | `PASS` §4.1 | G20 RQ/AC | `PASS` doc 23 |
| G09 precisão monetária | `PASS` §4.1 | G21 riscos/gaps | `PASS` §9 |
| G10 `as_of` | `PASS` D-04/D-05/D-06 | G22 sem runtime indevido | `PASS` §12 |
| G11 provenance | `PASS` §4.1 | G23 docs publicadas | `PASS` este pacote |
| G12 contratos api-delpi | `PASS` §4.1 | G24 bloqueio até gate explícito | `PASS` §12 |

## 11. Riscos residuais

- **E7** (versão RPO/parâmetros efetivos MATR910): `PENDING` externo — mitigação: semântica `PROVEN` empiricamente linha-a-linha; se a versão compilada divergir do fonte, reabrir D-03..D-05.
- **TTAT** nunca foi lida pela api-delpi — novo acesso de leitura (volume/índice a validar na E1).
- **Corpus drift doc-61/62/63** corrigido neste pacote — re-ingestão necessária para propagar.
- Paridade técnica futura × artefato continua `TEST_NOT_RUN` até E8; **G6 humano permanece `PENDING`**.
- Saídas agregadas do kardex ≠ CPV — contrato separa as duas medidas para evitar leitura errada (risco funcional mitigado por design).

## 12. Limites declarados

Nenhum endpoint, schema, migration, página, tool MCP produtiva, permissão, regra de autorização, rotina ERP ou deploy foi criado/alterado. A única alteração de código declarada é o manifest de fontes do corpus (tags `doc-61/62/63` saneadas + `doc-122` autorizado) — configuração documental, sem efeito runtime até a ingestão governada. **Implementação permanece bloqueada** até gate de execução transversal explicitamente aprovado (proposto: `CF-PROC0072-R06-R07-IMPLEMENTATION-015`).
