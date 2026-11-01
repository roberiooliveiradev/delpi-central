# SURI-MCP-FULL-PARITY-CONTINUOUS-EXECUTION — LEDGER

PROGRAM: SURI-MCP-FULL-PARITY-CONTINUOUS-EXECUTION-001/002
CURRENT LOT: G13 — Preferences/Profile WRITE (W-01, W-02)
LAST CLOSED LOT: G12 Enrichment WRITE (0d462a5dd7)
G12 EVIDENCE: catalog v13 in-image; enrichment_execute espelha
  ACT V005 + rate limiter + normalize_supplier_id;
  smoke — decide/decide_bulk/prepare_update rejected paths
  proven (not_found/bad-decision), bogus key/action fail-closed.
  Positive write = em review real (nao exercitada — writes
  mutam dados; negativos+rejected provam dispatch/service).

G11 EVIDENCE: catalog v12 in-image; comex_execute espelha ACT V005;
  smoke — ncm_request candidate sobre NCM existente -> confirmed
  (already_registered, sem mutacao); mesma idem_key -> replayed;
  transition governanca inexistente -> rejected not_found;
  view_create 'smoke' criou view real do actor (visivel em views);
  bogus key/status/action fail-closed. W-09 delete fica p/ G14.

G10 AUDIT: PostgresSuriExecuteOperationsRepository (V005) = claim
  atomic in_progress -> complete, replay/conflict/in_progress kinds,
  payload_hash LGPD, TTL+gc, fail-closed on store error;
  _audit = actor+correlation+action+index+key-hash estruturado;
  EXECUTE registry fechado; AuthZ primeiro; MAX ops bounded;
  caller Bearer token only (sem service-account); batch isolation.
  GAP registrado: sem expected_revision generico; delete (G14)
  exige confirmation channel — se indisponivel, retornar
  confirmation_unavailable sem executar.


G8 EVIDENCE: catalog v11 in-image; smoke — session.capabilities/
  preferences success; users.related_requests success; profile
  self-only 'Forbidden' provado; photo 'photo not found' honesto;
  identidade vazia/filtro extra fail-closed.

G7 EVIDENCE: catalog v10 in-image; smoke — market filters/summary/series/fx/quotes/quote_compare/monthly success;
  import_series+ppi = domain errors 'unknown ncm/series' (data-gated);
  comex products_search/ncm_list(pending_fiscal_review)/views success;
  negativos fail-closed (export/bogus/bad-status).

G6 EVIDENCE: catalog v9 in-image; smoke — search total=474896,
  bad-fragment/short-key/1-op/unknown-action/unit-99 fail-closed;
  S2S DelpiS2SApiGateway + require_units preservados.
G4 EVIDENCE em history; G5 EVIDENCE: catalog v8 in-image; smoke —
  otd aggregate/series success; analyze(overview_summary) success
  (Literal fix 5bdf3e713c); negativos fail-closed.
G4 EVIDENCE: catalog v7 in-image; smoke autenticado — filters/summary ok,
  items total=14232, details+suppliers ok (code 10010001),
  details sem branch -> 'A concrete branch (01 or 02) is required',
  action/filtro inválidos fail-closed. Suite suri_mcp verde.
CURRENT HEAD: 0d462a5dd7 · CATALOG: V13 · SOURCE SHA: idem · CATALOG: V6 · TOOLS: 5
PARITY: 39/45 = 86.7% · TARGET: 45/45 = 100%

## G4 — Inventário concluído (contratos reais no HEAD)

Owner BFF: `SafetyStockService` em
`supplies-api/app/application/services/safety_stock_service.py`
Guard: `@require_policy(can_use_operations)` (supplies.access) em todas.
Erros: ValueError→422 · DelpiApiGatewayError→mapeado (401/403/404/502).

Rotas BFF (espelhar exatamente):
- GET /safety-stock/filters → get_filters(user, branch, includeBlocked)
- GET /safety-stock/summary → get_summary(user, branch, includeBlocked,
    productGroup, unit, search, status, includeWithoutSafetyStock)
- GET /safety-stock/items → list_items(user, branch, page, page_size,
    sortBy, sortDirection, includeBlocked, productGroup, unit, search,
    status, includeWithoutSafetyStock)
- GET /safety-stock/items/<code>/details → get_item_details(user, code, branch)
- GET /safety-stock/items/<code>/suppliers → get_item_suppliers(user, code, branch)

Regra especial R-14 (do brief): se detail/suppliers exigir branch
específica e contexto vier `all`/ausente → erro estruturado de escolha
obrigatória (verificar semântica exata dentro de SafetyStockService —
ler os métodos get_item_details/get_item_suppliers antes do freeze).

Produtor: api-delpi supplies safety_stock (ver supplies_delpi_reads.py
para paths do gateway).

## Próxima ação exata (S1 de G4)

1. Ler safety_stock_service.py: assinaturas completas, validações de
   branch (details/suppliers), defaults e paginação (MAX_PAGE_SIZE).
2. Congelar schemas: SafetyStockFilters/Summary/ItemsFilters,
   SafetyStockItemIdentity {code, branch?} — extra="forbid".
3. Implementar (mesmo padrão G3): constants (registry + allowlists +
   CATALOG_VERSION=7), schemas, server Literals/union, tool_bridge
   (_dispatch_safety_stock_read + 5 handlers via _operations_user).
4. Testes: positive/sibling/negative + union-dispatch + catalog v7.
5. Suite suri_mcp → commit/push → rebuild+recreate só supplies-mcp →
   smoke OAuth real (filters/summary/items/details/suppliers +
   branch-all negativo) → matriz R-13/R-14 → ledger → G5.

Padrão de referência: G3 (commits a4a2697058, 31ccaae2e0).
Rollback: tag infra-supplies-mcp:pre-v6-rollback; nova tag por lote.

## Estado dos lotes

G0 CLOSED (8935dab669) · G4 IN_PROGRESS (S0 done) · G5–G15 PENDING.
Resíduos conhecidos: CHATGPT_SCHEMA refresh = PENDING_USER_ACTION.
