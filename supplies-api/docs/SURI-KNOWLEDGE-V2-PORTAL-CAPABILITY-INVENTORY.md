# SURI Knowledge V2 — Portal Capability Inventory (K0)

```
TASK: SURI-KNOWLEDGE-AND-PORTAL-HELP-V2-END-TO-END-001
BASE HEAD: 46d9fb1714
STATUS: K0 COMPLETE — verified on HEAD (not just the V1 snapshot)
```

## Pages — 23 total (18 ROUTED_COMPONENT + 5 PLACEHOLDER)

| page_id | route | component | status |
|---|---|---|---|
| home | `/apps/supplies` | HomePage | ROUTED |
| overview | `/apps/supplies/overview` | OverviewPage | ROUTED |
| otd | `/apps/supplies/otd` | OtdAnalyticsPage | ROUTED |
| purchase-requests | `/apps/supplies/purchase-requests` | PurchaseRequestsPage | ROUTED |
| purchase-request-detail | `.../purchase-requests/:branch/:num` | PurchaseRequestDetailPage | ROUTED |
| purchase-orders | `/apps/supplies/purchase-orders` | PurchaseOrdersPage | ROUTED |
| purchase-order-detail | `.../purchase-orders/:branch/:num` | PurchaseOrderDetailPage | ROUTED |
| deliveries | `/apps/supplies/deliveries` | DeliveriesPage | ROUTED |
| suppliers | `/apps/supplies/suppliers` | SuppliersPage | ROUTED |
| supplier-detail | `.../suppliers/:code/:store` | SupplierDetailPage | ROUTED |
| supplier-create | `/apps/supplies/suppliers/new` | SupplierCreatePage | ROUTED |
| inventory | `/apps/supplies/inventory` | InventoryPage | ROUTED |
| safety-stock | `/apps/supplies/safety-stock` | SafetyStockPage | ROUTED |
| safety-stock-detail | `.../safety-stock/:branch/:code` | SafetyStockDetailPage | ROUTED |
| consumption-audit | `/apps/supplies/consumption-audit` | ConsumptionAuditPage | ROUTED |
| market-intelligence | `/apps/supplies/market-intelligence` | MarketIntelligencePage | ROUTED |
| user-profile | `/apps/supplies/users/:id` | UserProfilePage | ROUTED (self\|admin guard) |
| help | `/apps/supplies/help` | UserManualPage | ROUTED |
| my-tasks | `/apps/supplies/my-tasks` | PlaceholderPage | PLACEHOLDER |
| products | `/apps/supplies/products` | PlaceholderPage | PLACEHOLDER |
| negotiations | `/apps/supplies/negotiations` | PlaceholderPage | PLACEHOLDER |
| indicators | `/apps/supplies/indicators` | PlaceholderPage | PLACEHOLDER |
| administration | `/apps/supplies/administration` | PlaceholderPage | PLACEHOLDER |

## Help content verified on HEAD

- Manual sections: 7 (`want`, `screens`, `safety-stock`,
  `market-intelligence`, `consumption-audit`, `faq`, `glossary`)
- FAQ entries: **44** q/a pairs in `userManualContent.ts` (catalog said 43)
- Glossary terms: **22** in `glossaryContent.ts` (catalog said 21)
- Placeholder pages: 5 confirmed PLACEHOLDER on HEAD — never teach as ready
- MCP corpus v1: 17 items, corpus_version=1, token-overlap search

## MCP capability ↔ page map (45)

Read/analyze surfaces map to the pages above per
`SURI-MCP-FULL-PARITY-MATRIX.md` (45/45 proven); knowledge V2 adds
page/concept/method/faq/journey fichas under `knowledge`, preserving the
five-tool invariant — no new tools, no per-method tools.

## K0 → K1 handoff

Corpus v2 schema: typed items with `kind` ∈
{page, concept, method, faq, journey, topic} + `page_id`/`method_id`
locators + `knowledge_status` ∈ {IMPLEMENTED, KNOWLEDGE_ONLY, DATA_GAP,
PLACEHOLDER} + source locators + version.
