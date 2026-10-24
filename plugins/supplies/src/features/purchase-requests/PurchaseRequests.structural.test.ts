import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { mapPurchaseRequestsFetchError } from "./content";
import { attentionQueryPatch, activeAttentionBucket } from "./attentionBuckets";
import {
  authorizeQueryBranches,
  buildListSearchParams,
  buildRequestKey,
  buildUrlSearch,
  createDefaultQuery,
  parseQueryFromSearch,
  parseRequestKey,
} from "./query";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PurchaseRequests feature", () => {
  it("App liga lista e ficha real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/PurchaseRequestsPage/);
    expect(app).toMatch(/PurchaseRequestDetailPage/);
    expect(app).not.toMatch(/Lista e detalhe de SC entram na jornada C1/);
  });

  it("cliente fala só com supplies-api", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/purchase-requests/);
    expect(api).not.toMatch(/purchase-requests-api/);
    expect(api).not.toMatch(/api-delpi/);
  });

  it("lista sem painel inline e com redirect legado", () => {
    const page = readFileSync(join(dir, "PurchaseRequestsPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("highlights=");
    expect(page).toContain("SuppliesScopeChipBar");
    expect(page).toContain("listPurchaseRequestSummary");
    expect(page).toContain("setSummary(null)");
    expect(page).not.toContain("items.reduce");
    expect(page).toContain("PurchaseRequestsFilters");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("lastUpdatedAt");
    expect(page).toContain("PurchaseRequestsListTable");
    expect(page).toContain("buildPurchaseRequestDetailPath");
    expect(page).toContain("navigatePluginPath");
    expect(page).toContain("parseRequestKey");
    expect(page).toContain("authorizeQueryBranches");
    expect(page).toContain("canonicalizeUiBranches");
    expect(page).not.toContain("getPurchaseRequest");
    expect(page).not.toContain("detailOpen");
    expect(page).not.toContain("detailLoading");
    expect(page).not.toContain("resolveDefaultBranch");
    expect(page).not.toContain("onApply");
    expect(page).not.toContain("applyFilters");

    const detail = readFileSync(join(dir, "PurchaseRequestDetailPage.tsx"), "utf8");
    expect(detail).toContain("getPurchaseRequest");
    expect(detail).toContain("SuppliesPagePath");
    expect(detail).toContain("SP_HELP.purchaseRequestDetail");
    expect(detail).toContain("SuppliesPersonIdentity");
    expect(detail).toContain("classifyPurchaseRequestDetailError");
    // Identity guard (PR.IDENTITY.S4): the hero requester must come from the
    // enriched `header.requester` PersonRef — never a raw TOTVS name string.
    expect(detail).toContain("person={header?.requester}");
    expect(detail).not.toMatch(/header\?\.requester\?\.(name|display_name)/);
    // EN.A2: hero uses only contracted, safe indicators — never a single-UM
    // total; approval shown with per-line granularity (no fictitious header
    // approver); linked orders counted by canonical identity.
    expect(detail).toContain("countLinkedOrders");
    expect(detail).toContain("uniqueApproverNames");
    expect(detail).toContain("labelApprovalStatus");
    expect(detail).toContain("approvalBadgeVariant");
    expect(detail).toContain("stageBadgeVariant");
    expect(detail).toContain("has_overdue_order");
    expect(detail).toContain("max_days_overdue");
    expect(detail).toContain("visible_items_count");
    // Header-level summed quantities are never rendered (heterogeneous UM
    // semantics); line/order quantities are allowed at line granularity.
    expect(detail).not.toMatch(/header\?\.(requested|ordered|received)_quantity/);
    // No approver is ever promoted to the header/summary — per-line only.
    expect(detail).not.toMatch(/header\?\.approver_name|approval_summary\?\.approver_name/);
    // EN.A3–A5: per-line enrichment, linked orders/receipts/timeline sections
    // and the SC→PC link with a complete canonical identity.
    expect(detail).toContain("formatQuantityWithUnit");
    expect(detail).toContain("line.unit");
    expect(detail).toContain("line.request_required_date");
    expect(detail).toContain("line.suggested_supplier");
    expect(detail).toContain("line.account_code");
    expect(detail).toContain("SuppliesSupplierIdentity");
    expect(detail).toContain("collectLinkedOrders");
    expect(detail).toContain("collectReceipts");
    expect(detail).toContain("hasCompleteOrderIdentity");
    expect(detail).toContain("buildPurchaseOrderDetailPath");
    expect(detail).toContain("SuppliesEntityLink");
    expect(detail).toContain("labelLinkedOrderDeliveryStatus");
    expect(detail).toContain("linkedOrderDeliveryVariant");
    expect(detail).toContain("SuppliesEventsSection");
    expect(detail).toContain("timelineEventTone");
    expect(detail).toContain("timelineReferenceLabel");
    expect(detail).toContain("SP_HELP.purchaseRequestDetailOrders");
    expect(detail).toContain("SP_HELP.purchaseRequestDetailReceipts");
    expect(detail).toContain("sp-purchase-request-detail__table");
    // The timeline is «Acompanhamento», never an audit-history section.
    expect(detail).not.toMatch(/histórico|historico|audit/i);
  });

  it("filtros Unidade alinhados à Visão geral", () => {
    const filters = readFileSync(join(dir, "PurchaseRequestsFilters.tsx"), "utf8");
    expect(filters).toContain("SuppliesFilterBarShell");
    expect(filters).toContain("SuppliesMultiSelectField");
    expect(filters).toContain("SUPPLIES_UNIT_FILTER_LABEL");
    expect(filters).toContain("canonicalizeUiBranches");
    expect(filters).toContain("emptyLabel=\"Todas\"");
    expect(filters).toContain("searchable");
    expect(filters).toContain("SuppliesSegmentToggle");
    expect(filters).toContain("PERIOD_PRESET_OPTIONS");
    expect(filters).toContain("matchPeriodPreset");
    expect(filters).toContain("C.periodLabel");
    expect(filters).toContain("sp-filter-bar__period-block");
    expect(filters).not.toContain("C.moreFilters");
    expect(filters).not.toContain("showMore");
    expect(filters).not.toContain("searchable={unitOptions.length > 4}");
    expect(filters).toContain("selectedValues={query.overall_stages}");
    expect(filters).not.toContain("overall_stages[0]");
  });

  it("toolbar canônica com href canônico de SC sem is-selected", () => {
    const table = readFileSync(join(dir, "PurchaseRequestsListTable.tsx"), "utf8");
    expect(table).toContain("SuppliesDataListToolbar");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesDataCardsSortBar");
    expect(table).toContain("C.tableMeta");
    expect(table).toContain("C.cardsMeta");
    expect(table).toContain("!showCards");
    expect(table).toContain("SuppliesTableFontSizeControls");
    expect(table).toContain("SuppliesTableColumnVisibilityMenu");
    expect(table).toContain("ExcelExportButton");
    expect(table).toContain("SuppliesCompactPagination");
    expect(table).toContain("SuppliesEntityLink");
    expect(table).toContain("SuppliesPersonIdentity");
    expect(table).toContain("buildPurchaseRequestDetailPath");
    expect(table).toContain("PurchaseRequestsCards");
    expect(table).toContain("nextServerSort");
    expect(table).toContain("PURCHASE_REQUESTS_SORTABLE_COLUMNS");
    expect(table).not.toContain("is-selected");
    expect(table).not.toContain("buildRequestKey");
    expect(table).not.toContain("?request=");

    const cards = readFileSync(join(dir, "PurchaseRequestsCards.tsx"), "utf8");
    expect(cards).toContain("SuppliesPersonIdentity");

    const config = readFileSync(join(dir, "purchaseRequestsTableConfig.ts"), "utf8");
    expect(config).toContain("supplies:purchase-requests:column-prefs:v1");
    expect(config).not.toContain("purchase-orders");
  });

  it("Cards esconde Fonte/Colunas e usa metadata sem colunas", () => {
    const table = readFileSync(join(dir, "PurchaseRequestsListTable.tsx"), "utf8");
    expect(table).toMatch(/showCards[\s\S]*C\.cardsMeta\(total\)/);
    expect(table).toMatch(/!showCards[\s\S]*SuppliesTableFontSizeControls/);
    expect(table).toMatch(/!showCards[\s\S]*SuppliesTableColumnVisibilityMenu/);
    expect(table).toContain("canExport");
    expect(table).toContain("SuppliesDataCardsSortBar");
    expect(table).toContain("SuppliesCompactPagination");
    // Font style only on table region, not on cards sort bar.
    expect(table).not.toMatch(/SuppliesDataCardsSortBar[\s\S]{0,80}style=\{tableStyle\}/);

    const content = readFileSync(join(dir, "content.ts"), "utf8");
    expect(content).toContain("cardsMeta:");
    expect(content).toMatch(/cardsMeta: \(requests: number\) =>/);
    expect(content).toContain("SC(s)");
    expect(content).not.toMatch(/linha\(s\)/);
  });

  it("CSS não recria botão/filtro do kit e usa região de tabela compartilhada", () => {
    const css = readFileSync(join(dir, "../../index.css"), "utf8");
    expect(css).not.toMatch(/sp-purchase-requests__btn\b/);
    expect(css).not.toMatch(/sp-purchase-requests__hero\b/);
    expect(css).toMatch(/sp-list-table-region/);
    expect(css).toMatch(/sp-list-filters/);
    expect(css).toMatch(/sp-purchase-request-detail/);
  });

  it("query Todas vs API effective + sibling + negative", () => {
    const defaults = createDefaultQuery();
    expect(defaults.branches).toEqual([]);

    const scoped = { ...defaults, branches: ["01"], request_number: "100", overall_stages: ["awaiting_order" as const] };
    const params = buildListSearchParams(scoped);
    expect(params.getAll("branch")).toEqual(["01"]);
    expect(params.get("request_number")).toBe("100");

    expect(authorizeQueryBranches(defaults, ["01", "02"]).branches).toEqual(["01", "02"]);
    expect(authorizeQueryBranches({ ...defaults, branches: ["01"] }, ["01", "02"]).branches).toEqual([
      "01",
    ]);

    const emptyUrl = parseQueryFromSearch("?page=1", ["01", "02"]);
    expect(emptyUrl.branches).toEqual([]);

    const both = parseQueryFromSearch("?branch=01&branch=02", ["01", "02"]);
    expect(both.branches).toEqual([]);

    const single = parseQueryFromSearch("?branch=02&request=02:200", ["01", "02"]);
    expect(single.branches).toEqual(["02"]);
    expect(parseRequestKey(single.request)).toEqual({
      branch: "02",
      requestNumber: "200",
    });
    expect(buildUrlSearch(single)).toContain("branch=02");
    expect(buildUrlSearch(single)).toContain("request=02%3A200");

    const sorted = parseQueryFromSearch(
      "?branch=01&sort_by=issue_date&sort_dir=asc",
      ["01", "02"],
    );
    expect(sorted.branches).toEqual(["01"]);
    expect(sorted.sort_by).toBe("issue_date");

    const stageSort = parseQueryFromSearch(
      "?sort_by=overall_stage&sort_dir=desc",
      ["01"],
    );
    expect(stageSort.sort_by).toBe("overall_stage");
    expect(stageSort.sort_dir).toBe("desc");

    const productSort = parseQueryFromSearch(
      "?sort_by=product_code&sort_dir=asc",
      ["01"],
    );
    expect(productSort.sort_by).toBe("product_code");

    expect(parseRequestKey("invalid")).toBeNull();
    expect(buildRequestKey("01", "100")).toBe("01:100");
    expect(parseQueryFromSearch("?overall_stage=not-a-stage", ["01"]).overall_stages).toEqual([]);
    expect(
      parseQueryFromSearch(
        "?overall_stage=awaiting_order&overall_stage=partially_ordered",
        ["01"],
      ).overall_stages,
    ).toEqual(["awaiting_order", "partially_ordered"]);
    expect(attentionQueryPatch("ordering")).toEqual({
      overall_stages: ["awaiting_order", "partially_ordered"],
      page: 1,
    });
    expect(attentionQueryPatch("receiving").overall_stages).toEqual([
      "ordered",
      "awaiting_receipt",
      "partially_received",
    ]);
    expect(attentionQueryPatch("completed").overall_stages).toEqual([
      "completed",
      "residual_closed",
    ]);
    expect(attentionQueryPatch("all")).toEqual({ overall_stages: [], page: 1 });
    expect(activeAttentionBucket([])).toBe("all");
    expect(activeAttentionBucket(["awaiting_order"])).toBeNull();
  });

  it("matriz de sort UI→API cobre item, produto e stage", async () => {
    const { nextServerSort, PURCHASE_REQUESTS_SORTABLE_COLUMNS, tableSortKey } = await import(
      "./query"
    );
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.request_item).toBe("request_item");
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.product).toBe("product_code");
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.stage).toBe("overall_stage");
    expect(PURCHASE_REQUESTS_SORTABLE_COLUMNS.opened).toBe("issue_date");
    expect(tableSortKey("overall_stage")).toBe("stage");
    expect(tableSortKey("product_code")).toBe("product");
    expect(nextServerSort(createDefaultQuery(), "stage")).toEqual({
      sort_by: "overall_stage",
      sort_dir: "asc",
      page: 1,
    });
    expect(nextServerSort(createDefaultQuery(), "product")).toEqual({
      sort_by: "product_code",
      sort_dir: "asc",
      page: 1,
    });
    expect(nextServerSort(createDefaultQuery(), "unknown")).toBeNull();
  });

  it("mapeia 403 positive/sibling e preserva mensagem genérica (negative)", () => {
    expect(mapPurchaseRequestsFetchError("403 Forbidden")).toMatch(/unidade/i);
    expect(mapPurchaseRequestsFetchError("Request failed with status 403")).toMatch(/unidade/i);
    expect(mapPurchaseRequestsFetchError("timeout upstream")).toBe("timeout upstream");
  });

  it("mapeia 422 de ordenação por situação para recorte menor (positive/sibling/negative)", () => {
    expect(
      mapPurchaseRequestsFetchError(
        "Ordenação por situação exige um recorte menor. Reduza o período ou selecione uma unidade.",
      ),
    ).toMatch(/recorte menor/i);
    expect(
      mapPurchaseRequestsFetchError(
        "[upstream_client_error] Ordenação por situação exige um recorte menor. Reduza o período ou selecione uma unidade.",
      ),
    ).toMatch(/recorte menor/i);
    expect(mapPurchaseRequestsFetchError("timeout upstream")).toBe("timeout upstream");
  });

  it("solicitante prefere display_name Minha DELPI (vínculo Core) com fallback honesto", () => {
    const identity = readFileSync(
      join(dir, "../../app/SuppliesDirectoryIdentity.tsx"),
      "utf8",
    );
    expect(identity).toContain("person?.display_name || person?.name");
    const types = readFileSync(join(dir, "types.ts"), "utf8");
    expect(types).toContain("display_name");
  });

  it("identidade do solicitante: nome único com fallback e foto via BFF", () => {
    const identity = readFileSync(
      join(dir, "../../app/SuppliesDirectoryIdentity.tsx"),
      "utf8",
    );
    // Single name — no TOTVS/code secondary line (PR.IDENTITY.S3);
    // the supplier identity above keeps its own secondary={code}.
    expect(identity).toContain("person?.display_name || person?.name || person?.code");
    expect(identity).not.toContain("const secondary");
    expect(identity).toContain("src={photoSrc}");
    expect(identity).toContain("usePersonPhoto(person?.photo_url, {");
    expect(identity).toContain("branches: allowedUnits");
    expect(identity).toContain("photoPeriod");
    const types = readFileSync(join(dir, "types.ts"), "utf8");
    expect(types).toContain("photo_url");
    // Photo loads through the authenticated BFF client, never <img> to Core.
    const hook = readFileSync(
      join(dir, "../../app/usePersonPhoto.ts"),
      "utf8",
    );
    expect(hook).toContain("httpGetBlob");
    expect(hook).toContain("photoCache");
    // Photo proxy is scope-guarded: the hook always sends branch+period.
    expect(hook).toContain("params.append(\"branch\"");
    expect(hook).toContain("date_from");
  });

  it("filtros de solicitante e centro de custo no contrato e na UI", () => {
    const query = readFileSync(join(dir, "query.ts"), "utf8");
    expect(query).toContain("requester_user_id");
    expect(query).toContain("cost_center");
    const filters = readFileSync(join(dir, "PurchaseRequestsFilters.tsx"), "utf8");
    expect(filters).toContain("listPurchaseRequestRequesters");
    expect(filters).toContain("listPurchaseRequestCostCenters");
    expect(filters).toContain("requester_ids");
    expect(filters).toContain("cost_centers");
    const active = readFileSync(join(dir, "hasActiveFilters.ts"), "utf8");
    expect(active).toContain("requester_ids");
    expect(active).toContain("cost_centers");
  });
});
