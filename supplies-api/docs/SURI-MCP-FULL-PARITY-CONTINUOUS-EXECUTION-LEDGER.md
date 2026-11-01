# SURI-MCP-FULL-PARITY-CONTINUOUS-EXECUTION — LEDGER

PROGRAM: SURI-MCP-FULL-PARITY-CONTINUOUS-EXECUTION-001/002
CURRENT LOT: G4 — Safety Stock (R-13, R-14) — INVENTORY done, S1 next
LAST CLOSED LOT: G0 (8935dab669)
CURRENT HEAD: 8935dab669 · SOURCE SHA: idem · CATALOG: V6 · TOOLS: 5
PARITY: 21/45 = 46.7% · TARGET G4: 23/45 = 51.1%

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
