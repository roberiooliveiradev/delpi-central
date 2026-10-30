# SURI-MCP-FULL-PARITY-EXECUTION-BRIEFS — Receita por lote

Task: `SURI-MCP-FULL-PARITY-P0` · HEAD `8a822e29c1`. Cada brief é autorização-condicional: só executa após aceite explícito do lote.

Template comum de autoridades (todo lote): instruções GPT Arquiteto, `.cursor` globais + `platform-security-identity-authorization`, `platform-api-contracts-integration`, `platform-quality-testing`, ADR ARCH-MCP-01, `SURI-S1-CONTRACT-FREEZE-V2.md`, este plano, inventário e matrix. Owner único: `supplies-api/app/interfaces/mcp` + reuse read-only de services/gateways da `supplies-api`. Proibido em todo lote: criar permissão, alterar RBAC/Keycloak/realm, tocar outros MCPs, escrita ERP, executor genérico, tool por endpoint, secrets em evidência, alterar contrato frozen sem bump de versão.

---

## P1-R1 — `read entity=purchase_requests`

- **GOAL:** paridade da jornada SC (lista/filtros, summary, facets, detalhe, export, foto).
- **RQ/AC:** RQ-1 `action=search` aceita filtros fechados (branch[], date range, request_number, product, requester, cost_center, stage, page/size ≤200); RQ-2 `action=summary|requesters|cost_centers|get|export`; RQ-3 photo respeita `RequesterPhotoScopeGuard` (404 facet); RQ-4 identity `{branch, request_number}`; RQ-5 export devolve artefato conforme DECISION-G1.
- **Estado atual:** BFF+PR-api PROVEN; SURI não tem a entidade.
- **Contratos:** PR-api GETs (sem writes — jornada read-only por design); `PurchaseRequestsGateway` existente; identity enrich via `RequesterIdentityService` (reuso obrigatório — não duplicar enriquecimento).
- **Escopo permitido:** `constants.py` (entity+filter keys), `schemas.py` (PurchaseRequests*Filters/Identity extra=forbid), `tool_bridge.py` handlers, reuse gateway/identity service, testes.
- **Escopo proibido:** create/approve/cancel SC (não existe no Portal — BLOCKED B-03); bypass facet guard; unit grant novo.
- **AuthZ:** `can_use_purchase_requests` + `require_units("branch")`; export exige branch não-vazio (espelhar BFF).
- **Testes:** contract schema (unknown key→422), dispatch cada action, units deny, facet 404, export contract, 401 challenge, regressão 4 tools.
- **Evidence:** tools/list + call real em container teste; matrix R-04..R-07 → PROVEN.
- **Dependências:** nenhuma (1º lote). **Próxima etapa:** P1-R2.

## P1-R2 — PO export

- **GOAL:** `read entity=purchase_orders action=export` com mesmo XLSX do BFF.
- **RQ/AC:** reuso `build_purchase_orders_xlsx`; mesmo recorte de filtros do search.
- **Files:** `tool_bridge.py`, constants, tests. **Dependências:** DECISION-G1 (formato do artefato).
- **Stop:** artefato divergir do BFF.

## P1-R3 — deliveries + inventory

- **GOAL:** `read entity=deliveries action=late`, `read entity=inventory action=summary|items`.
- **Contratos:** `LateDeliveriesCompositionService` + `InventoryStockBalancesService` reuse (page-budget cap preservado).
- **AuthZ:** `can_use_operations`. **Files:** constants/schemas/bridge/tests.

## P1-R4 — safety_stock

- **GOAL:** `read entity=safety_stock` filters/summary/items/details/suppliers.
- **AC especial:** branch `all` em detail → erro estruturado `branch_required` (espelha SafetyStockBranchChoiceDialog — sem default silencioso).
- **AuthZ:** `can_use_operations`. **Dependência:** P1-R3 (padrão de handlers de leitura consolidado).

## P1-R5 — suppliers reads

- **GOAL:** `read entity=suppliers`: list, get, catalogs(14 allowlist), postal-code, existing(dup-check), integration-status(manage), operations, creation-preview(analyze).
- **Contratos:** `DelpiS2SApiGateway` (NÃO o shared); upstream `*_DISABLED`/S2S codes repassados.
- **AC:** integration-status sem manage → 403 (negative); catalogs fora da allowlist → 422; preview → `analyze analysis=supplier_creation_preview` com `write_enabled:false` espelhado.
- **Files:** bridge + schemas + reuse `DelpiSupplierDuplicateSearch`, `SupplierCreationPreviewService` + rate limiter de ator.
- **Stop:** qualquer caminho de preview persistir estado.

## P1-R6 — analytics (overview + otd)

- **GOAL:** `analyze analysis=overview_summary` (compose service, partial-honest) + `read entity=otd` (aggregate/series).
- **AC:** fan-out com origem falha → `unavailable`/`partialFailures` igual BFF; units por serviço.
- **Files:** reuse `OverviewCompositionService`, `OtdSeriesService`, `OtdAggregateService`.

## P1-R7 — consumption_audit

- **GOAL:** `read entity=production_orders`: search (mesma allowlist de params, OP key regex), get, comparison(2–10).
- **AC:** `require_unit("unit")`; upstream `S2S_SCOPE_DENIED`→403 propagado; comparison exige 2–10.
- **Files:** bridge + schemas + S2S gateway.

## P1-R8 — market_intelligence

- **GOAL:** `read`/`analyze`: filters, summary, 5 series families, monthly-averages, quotes/compare + `read entity=comex` products-search, ncm-governance list/get, views list/get.
- **AC:** provider down → `external_data_unavailable` honesto; `source_use_pending`/quarentena → estado contratual, nunca preço sintético; comex transitions só leitura aqui (write = P2-E2).
- **Files:** reuse `MarketIntelligenceService`, `ComexAnalysisService`, `MarketDataGateway`.

## P1-R9 — users/me/home

- **GOAL:** `read entity=users` (profile/photo/related self|manage), `read entity=me` (capabilities+preferences), `analyze analysis=home_attention` (5 count-sources, `unavailable` honest).
- **AC:** perfil alheio sem manage → 403; related com `require_units` quando branch informado; counts 0-confirmado ≠ falha.

## P1-A1 — analyze multi-entidade

- **GOAL:** estender `analysis` para `purchase_requests_summary`, `suppliers_summary`, `consumption_audit_summary`, `safety_stock_summary`, `market_intelligence_summary` — mesmo padrão facts/calculations/recommendations/input_hash, sem ação executiva.
- **Dependência:** entidades R1–R8 já dispatched.

## P1-K1 — knowledge corpus

- **GOAL:** entradas por entidade/ação nova (buscas guiadas, glossário); version+SHA bump; teste de integridade.
- **Files:** `app/content/suri_knowledge.json`, `knowledge.py` tests.

## P2-E1 — governed-write foundation

- **GOAL:** infraestrutura `execute`/`delete` homologada — registry ACT, proposal store (DECISION-E1: pg `supplies` recomendado; migration própria `suri_*`), prepare→commit, idempotency store, audit channel `mcp/suri`, `delpi/toolClass` PREPARE/ACT meta, annotations `read_only:false`.
- **RQ/AC:** RQ-1 registry rejeita (entity,action) não cadastrado; RQ-2 proposal actor-bound + TTL + fingerprint + single-use; RQ-3 commit re-checa policy; RQ-4 read-back pós-write com `OUTCOME_VERIFICATION_FAILED` honesto; RQ-5 batch → resultado individual, sem transação presumida; RQ-6 tools/list passa a 6 tools.
- **Escopo proibido:** consent/callback forjável client-side; auto-act em destructive; writes em lote cross-owner.
- **Testes:** forged handle/consent rejeitados; TTL expiry; replay idempotency; policy flip entre prepare e commit.
- **Dependência:** DECISION-E1+D1 fechadas.

## P2-E2 — comex execute (+ primeiro delete)

- **GOAL:** `execute`: `comex.view.save`, `comex.ncm.request`, `comex.ncm.transition` (manage-gated → consent/step-up); `delete`: `comex.view.delete` (confirmação explícita).
- **AC:** transition manage-only sem manage → 403; approve/inactive dispara `PUT ncm-allowlist` ED-api com falha reportada; delete exige confirmação + read-back `gone`.
- **Reuse:** `ComexAnalysisService` (transitions já checam capability), repositories pg.

## P2-E3 — enrichment execute

- **GOAL:** `execute`: `supplier.enrichment.review.create`, `.decide`, `.bulk_decide`, `.prepare_update`.
- **AC:** expected_revision/idempotency do serviço preservados; server-owned-fields rejeitados; actor rate-limit → 429; **NUNCA** ERP write (prepare-update segue draft-only).
- **Reuse:** `SupplierEnrichmentReviewService` + `PostgresSupplierEnrichmentRepository`.

## P2-E4 — preferences/profile execute

- **GOAL:** `execute`: `me.preferences.update`, `users.profile.update` (self).
- **AC:** self-only enforcement; resolver owner único da write (TO_INVENTORY patchPreferences×patchUserProfile).
- **Reuse:** `PreferencesService`, `UserProfileService` (`_assert_can_edit`).

## P2-D1 — delete foundation

- **GOAL:** `delete` tool + policy DELETE=confirmação sempre; canal DECISION-D1 (elicit `target_echo` recomendado); read-back `expected_postcondition: read_gone`.
- **AC:** sem canal → `confirmation_unavailable`; declined → `confirmation_declined`; handle estranho → erro; audit registra actor+target+result.

## P3/P4 — fora de agenda

- **P3:** `supplier.create`/`supplier.update` ERP — SÓ após B-01/B-02 (liberação TOTVS + homologação). Nova capacidade no registry permanece `status=blocked` honesta (veredicto `not_implemented`/`blocked`, padrão CAIO).
- **P3-B:** SC workflow — inexistente no Portal; depende de decisão de produto (C2/C3).
- **P4:** páginas placeholder — SURI acompanha o Portal, nunca o precede.
