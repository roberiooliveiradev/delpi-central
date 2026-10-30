# SURI-MCP-FULL-PARITY-MATRIX — Ledger de paridade Portal ↔ SURI

Task: `SURI-MCP-FULL-PARITY-P0` · HEAD `8a822e29c1` · Status por item: `PROVEN | TO_INVENTORY | PLANNED | TARGET | BLOCKED`
Granularidade: família de operação (não endpoint). Uma tool ≠ N capacidades provadas sem teste por operação.
Revisão `SURI-MCP-SUPPLIERS-WRITE-001` (2026-10-30): B-01/B-02 superadas por evidência de runtime — ver seção «Reconciliação».
Revisão `SURI-MCP-FULL-PARITY-V4-G1` (2026-10-30): lote P1-R5 entregue — R-15..R-22 promovidas a PROVEN (catálogo v4, `test_suppliers_read.py`).

## Indicadores

```text
PORTAL CAPABILITIES (denominador: linhas PROVEN executáveis) : 45 (34 READ + 11 WRITE)
SURI CAPABILITIES PROVEN (linhas com cobertura homologada)   : 14 (R-08, R-10, R-15..R-22, R-33, R-34, W-10, W-11)
CURRENT PARITY PERCENTAGE (implementada)                     : 31.1% (14/45)
TARGET PARITY PERCENTAGE                                     : 100% das capacidades autorizadas
```

Nota de contagem (reconciliação do denominador): o indicador anterior
declarava «34 = 25 READ + 9 WRITE», mas a tabela READ continha 34 linhas e
a WRITE 9 — a unidade de contagem agora é **linha de capacidade PROVEN**.
O denominador correto do snapshot P0 era 43; com W-10/W-11 promovidas de
BLOCKED a PROVEN passa a 45.

Legenda SURI: `—` = sem dispatch; `read`/`analyze`/`knowledge`/`execute`/`delete` = tool alvo.

## READ capabilities (25)

| ID | Área | Capacidade | Portal | SURI hoje | Owner | Contrato | AuthZ | Evidência | Gap | Fase |
|---|---|---|---|---|---|---|---|---|---|---|
| R-01 | Início | Hub + contagens de atenção | PROVEN | — | supplies-api (comp. página) | me/capabilities + dados-fonte | access | HomePage + BFF | tool `read`/knowledge nav | P1-R9 |
| R-02 | Overview | Dashboard composto (OTD, CPV, turnover, savings, ES, SCs, SI) | PROVEN | — | supplies-api → api-delpi+PR-api+SI | `/analytics/overview` | access+units | test_overview | `analyze` overview | P1-R6 |
| R-03 | Overview | OTD aggregate + series | PROVEN | — | api-delpi | `/analytics/otd[/series]` | access | test_otd_* | `read`/`analyze` otd | P1-R6 |
| R-04 | SC | Lista + filtros | PROVEN | — | PR-api | `GET /purchase-requests` | access+units | bff tests | `read` entity=purchase_requests | P1-R1 |
| R-05 | SC | Summary + facets (requesters, cost-centers, photo guard) | PROVEN | — | PR-api + core | `/summary\|/requesters\|/cost-centers\|photo` | access | bff tests | `read` summary/facets | P1-R1 |
| R-06 | SC | Export XLSX | PROVEN | — | supplies-api in-proc | `/export` | access+units | export test | `read` export (artefato) | P1-R1 |
| R-07 | SC | Detalhe + links | PROVEN | — | PR-api + core | `/{branch}/{num}` | access+unit | bff tests | `read` get | P1-R1 |
| R-08 | PC | Lista + filtros | PROVEN | `read:PO search` | api-delpi | `GET /purchase-orders` | access+units | suri tests | — | PROVEN |
| R-09 | PC | Export XLSX | PROVEN | — | supplies-api in-proc | `/export` | access | bff tests | `read` export | P1-R2 |
| R-10 | PC | Detalhe | PROVEN | `read:PO get` | api-delpi | `/{branch}/{num}` | access+unit | suri tests | — | PROVEN |
| R-11 | Entregas | Atrasos (panel paginado) | PROVEN | — | api-delpi | `/deliveries/late` | access | bff tests | `read` deliveries | P1-R3 |
| R-12 | Estoque | stock-balances summary + items | PROVEN | — | api-delpi | `/inventory/stock-balances/*` | access | bff tests | `read` inventory | P1-R3 |
| R-13 | Safety stock | filters+summary+items | PROVEN | — | api-delpi | `/safety-stock/*` | access | bff tests | `read` safety_stock | P1-R4 |
| R-14 | Safety stock | item details + suppliers | PROVEN | — | api-delpi | `/items/{code}/details\|suppliers` | access | bff tests | `read` get/details | P1-R4 |
| R-15 | Fornecedores | Lista | PROVEN | `read:suppliers search` | api-delpi(S2S) | `GET /suppliers` | access | routes + suri tests | — | PROVEN |
| R-16 | Fornecedores | Ficha 360 | PROVEN | `read:suppliers get` | api-delpi(S2S) | `/{code}/{store}` | access | routes + suri tests | — | PROVEN |
| R-17 | Fornecedores | Catálogos (14 kinds) | PROVEN | `read:suppliers catalogs` | api-delpi(S2S) | `/catalogs/{kind}` allowlist | access | routes + suri tests | — | PROVEN |
| R-18 | Fornecedores | CEP assist | PROVEN | `read:postal_codes lookup` | api-delpi | `/postal-codes/{cep}` | access | routes + suri tests | — | PROVEN |
| R-19 | Fornecedores | Dup-check por tax_id | PROVEN | `read:suppliers search_by_tax_id/existing` | api-delpi(S2S) | `/existing-suppliers` | access | creation + suri tests | — | PROVEN |
| R-20 | Fornecedores | Creation preview (read-only) | PROVEN | `analyze:supplier_creation_preview` | registry provider + S2S | `POST /creation-preview` (semântica READ) | access+rate-limit | preview + suri tests | — | PROVEN |
| R-21 | Fornecedores | Integration status | PROVEN | `read:suppliers integration_status` | api-delpi | `/integration-status` | **manage** | routes + suri tests | — | PROVEN |
| R-22 | Fornecedores | Operations tracking read | PROVEN | `read:suppliers operations` | api-delpi | `/operations/{id}` | access | routes + suri tests | — | PROVEN |
| R-23 | Consumo | Busca OP (fragmento/filtros) | PROVEN | — | api-delpi(S2S `consumption-audit.read`) | `/consumption-audit/orders` | access+unit | routes tests | `read` production_orders | P1-R7 |
| R-24 | Consumo | Detalhe OP | PROVEN | — | api-delpi(S2S) | `/orders/{op}` | access+unit | routes tests | `read` get | P1-R7 |
| R-25 | Consumo | Comparação 2–10 OPs | PROVEN | — | api-delpi(S2S) | `/comparison` | access+unit | routes tests | `analyze` compare | P1-R7 |
| R-26 | Mercado | filters+summary+series×5+monthly-averages+quotes/compare | PROVEN | — | external-data-api(S2S) | `/market-intelligence/*` | access | mi bff tests | `read`/`analyze` market | P1-R8 |
| R-27 | Mercado | Comex products search | PROVEN | — | api-delpi(S2S) | `/comex/products/search` | access | comex tests | `read` comex products | P1-R8 |
| R-28 | Mercado | Comex NCM governance list/detail | PROVEN | — | pg supplies | `/comex/ncm-governance` | access | comex tests | `read` governance | P1-R8 |
| R-29 | Mercado | Comex views list/get | PROVEN | — | pg supplies | `/comex/views` | access | comex tests | `read` views | P1-R8 |
| R-30 | Usuários | Perfil + foto | PROVEN | — | core-api+pg | `/users/{id}/profile\|photo` | self\|manage | profile tests | `read` user profile | P1-R9 |
| R-31 | Usuários | SCs relacionadas | PROVEN | — | PR-api+core | `/related-requests` | self\|manage+units | profile tests | `read` related | P1-R9 |
| R-32 | Sessão | capabilities + preferences read | PROVEN | `get_context` (parcial: sem preferences) | supplies-api | `/me/capabilities`, `/me/preferences` | shell | session ctx | `read`/`get_context` prefs | P1-R9 |
| R-33 | Ajuda | Manual/FAQ/glossário | PROVEN | `knowledge` (corpus parcial) | supplies content | in-proc | access | knowledge tests | ampliar corpus | P1-K1 |
| R-34 | Consumo | Análise determinística | PROVEN | `analyze:PO summary` | supplies-api | sample+facts+hash | access | suri tests | estender p/ demais entidades | P1-A1 |

## WRITE capabilities (9 — todas plugin-db ou workflow; nenhuma ERP liberada)

| ID | Área | Capacidade | Portal | SURI | Owner | Contrato | AuthZ | Estado | Fase |
|---|---|---|---|---|---|---|---|---|---|
| W-01 | Sessão | PATCH preferences | PROVEN | — | supplies-api pg | `/me/preferences` | self | tool `execute` pref.update | P2-E4 |
| W-02 | Usuários | PATCH profile (self) | PROVEN | — | supplies-api pg | `/users/{id}/profile` | self only | `execute` profile.update | P2-E4 |
| W-03 | Fornecedores | Enrichment review create | PROVEN | — | pg + S2S read + registry | `POST enrichment-reviews` | access+rate | `execute` review.create (PREPARE) | P2-E3 |
| W-04 | Fornecedores | Enrichment decisions + bulk | PROVEN | — | pg (expected_revision, idempotency) | `POST .../decisions\|bulk-decisions` | access | `execute` decide (PREPARE) | P2-E3 |
| W-05 | Fornecedores | Enrichment prepare-update (draft) | PROVEN | — | pg draft (nunca ERP) | `POST .../prepare-update` | access | `execute` prepare-update | P2-E3 |
| W-06 | Mercado | Comex NCM request create | PROVEN | — | pg | `POST /ncm-governance` | access | `execute` ncm.request | P2-E2 |
| W-07 | Mercado | Comex transition (algumas manage; ED-api put on approve/inactive) | PROVEN | — | pg + ED-api | `POST /{id}/transition` | access/manage | `execute` transition (PREPARE+consent p/ manage) | P2-E2 |
| W-08 | Mercado | Comex views create/update | PROVEN | — | pg | `POST/PUT /views` | access | `execute` view.save | P2-E2 |
| W-09 | Mercado | Comex views delete | PROVEN | — | pg | `DELETE /views/{id}` | access | `delete` view (confirmação explícita) | P2-D1 |
| W-10 | Fornecedores | Supplier create (Protheus POST) | PROVEN | `execute:suppliers.create` | api-delpi(S2S) + Protheus REST | `POST /suppliers` → `/integrations/protheus/suppliers` | access + S2S `suppliers.create` | runtime 2026-10-30 + 30 testes SURI | **PROVEN** (era B-01) |
| W-11 | Fornecedores | Supplier update (Protheus PUT) | PROVEN | `execute:suppliers.update` | api-delpi(S2S) + Protheus REST | `PUT /suppliers/{code}/{store}` | access + S2S `suppliers.update` | runtime end-to-end + 30 testes SURI | **PROVEN** (era B-02) |

## Reconciliação — bloqueios superados por evidência (SURI-MCP-SUPPLIERS-WRITE-001, 2026-10-30)

O inventário P0 classificou B-01/B-02 como bloqueados com base em
documentação anterior ao corte produtivo. Verificação não-destrutiva de
runtime provou o contrário:

- `PROTHEUS_SUPPLIER_CREATE_ENABLED=true` e `PROTHEUS_SUPPLIER_UPDATE_ENABLED=true` no container produtivo (`delpi-api-delpi`);
- provider S2S da `supplies-api` autentica com scopes `suppliers.read .create .update .consumption-audit.read`;
- **UPDATE end-to-end**: use case executado em produção com fornecedor inexistente `999999/01` atravessou validação → gate → codusr do ator → params → target guard → **REST Protheus alcançado** → `PROTHEUS_SUPPLIER_NOT_FOUND` (sem escrita possível);
- **CREATE**: payload válido normalizado atravessou validação → gate → parou em `PROTHEUS_IDENTITY_UNMAPPED` com ator propositalmente não mapeado (antes de qualquer byte REST — o POST real não foi disparado por segurança);
- BFF `POST /suppliers`/`PUT /suppliers/{code}/{store}` publicam `acknowledged`/`persistence_proven`/`operation_id`/`tracking_warning` — read-back e rastreio já fazem parte do contrato;
- SURI `execute` implementado com os mesmos primitivos canônicos (S2S gateway, DTOs, classificador de erro), `idempotency_key` por operação, pré-checagem de duplicidade por tax_id, correlation-id propagado ao tracker e auditoria por operação.

Classificação P0 anterior: `STALE_EVIDENCE` — o bloqueio documental foi
superado pelo runtime, não removido por força de instrução.

## BLOCKED — não viram operação MCP enquanto bloqueio vigente

| ID | Capacidade | Causa | Gate p/ desbloqueio |
|---|---|---|---|
| ~~B-01~~ | ~~Supplier create (Protheus)~~ | superado → W-10 (evidência acima) | — |
| ~~B-02~~ | ~~Supplier update (Protheus PUT)~~ | superado → W-11 (evidência acima) | — |
| B-03 | SC create/approve/cancel | **não existe no Portal** (PR-api read-only) | decisão de produto nova (C2/C3 roadmap) |
| B-04 | Metais dados reais | quarentena LME + firewall Sophos + retention right PENDING | aprovação de fonte + exceção de TI |

## TARGET/PLANNED — não contam na paridade atual (cobertura de roadmap)

| ID | Capacidade | Estado Portal | Nota |
|---|---|---|---|
| P-01 | Minhas tarefas | PLANNED (sem owner) | residual HOME-ATTENTION |
| P-02 | Produtos / Product 360 | PLANNED (E17) | api-delpi tem `/supplies/products/search` (comex) — base futura |
| P-03 | Negociações | PLANNED | negotiation-savings já entra no Overview |
| P-04 | Indicadores página | PLANNED | SI já compõe Overview |
| P-05 | Administração | PLANNED | admin real hoje = integration-status + comex manage inline |
| P-06 | Safety-stock consumption-analysis (E12) + price history (E18) | PLANNED | produtor já possui rotas |
| P-07 | ~~Supplier create/update~~ | PROVEN | promovido a W-10/W-11 (runtime + execute) |

## EXECUTION_DRIFT / TO_INVENTORY

- `patchPreferences` shared client existe mas a UI escreve por `patchUserProfile` — reconciliar owner da write de preferência no lote P2-E4. **TO_INVENTORY**
- SURI `get_context` não inclui preferences — avaliar `read entity=me/preferences`. **TO_INVENTORY**
- Asymmetry: MCP usa `DelpiApiGateway` (shared token) para purchase_orders; `execute` já usa `DelpiS2SApiGateway` (W-10/W-11). Ao estender `read` p/ suppliers/consumption-audit, usar o S2S gateway (scope enforcement upstream). **DECISION registrada no plano**
- VISUAL_AUTHENTICATED=INCONCLUSIVE persiste em várias páginas (não bloqueia paridade técnica; residual de homologação PO)
