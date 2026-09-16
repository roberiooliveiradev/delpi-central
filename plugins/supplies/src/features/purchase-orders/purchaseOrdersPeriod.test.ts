import { describe, expect, it } from "vitest";

import { resolvePeriodPreset } from "../../app/periodPreset";
import {
  buildListSearchParams,
  createDefaultQuery,
  parseQueryFromSearch,
} from "./query";
import {
  matchPurchaseOrdersPeriod,
  PURCHASE_ORDERS_PERIOD_OPTIONS,
  PURCHASE_ORDERS_UNBOUNDED_PERIOD,
  resolvePurchaseOrdersPeriod,
} from "./purchaseOrdersPeriod";

describe("purchaseOrdersPeriod", () => {
  const fixed = new Date(2026, 8, 16); // 2026-09-16 local

  it("empty from/to => Sem filtro (unbounded), not Personalizado", () => {
    expect(matchPurchaseOrdersPeriod("", "")).toBe(PURCHASE_ORDERS_UNBOUNDED_PERIOD);
    expect(matchPurchaseOrdersPeriod("  ", "  ")).toBe(PURCHASE_ORDERS_UNBOUNDED_PERIOD);
    expect(PURCHASE_ORDERS_PERIOD_OPTIONS[0]).toEqual({
      value: "unbounded",
      label: "Sem filtro",
    });
  });

  it("Este mês fills dates and matches this_month chip", () => {
    const range = resolvePeriodPreset("this_month", fixed);
    expect(range).toEqual({ from: "2026-09-01", to: "2026-09-16" });
    expect(matchPurchaseOrdersPeriod(range!.from, range!.to, fixed)).toBe("this_month");
    expect(resolvePurchaseOrdersPeriod("this_month", fixed)).toEqual(range);
  });

  it("manual range that is not a preset => Personalizado", () => {
    expect(matchPurchaseOrdersPeriod("2026-01-01", "2026-01-15", fixed)).toBe("custom");
  });

  it("partial range (only one date) => Personalizado", () => {
    expect(matchPurchaseOrdersPeriod("2026-09-01", "", fixed)).toBe("custom");
    expect(matchPurchaseOrdersPeriod("", "2026-09-16", fixed)).toBe("custom");
  });

  it("select Sem filtro resolves to unbounded sentinel", () => {
    expect(resolvePurchaseOrdersPeriod("unbounded")).toBe("unbounded");
    expect(resolvePurchaseOrdersPeriod("custom")).toBeNull();
  });

  it("exact preset range on F5 recovers the preset chip", () => {
    const quarter = resolvePeriodPreset("this_quarter", fixed)!;
    expect(matchPurchaseOrdersPeriod(quarter.from, quarter.to, fixed)).toBe("this_quarter");
  });

  it("default query and clear baseline keep empty delivery dates (no backend period filter)", () => {
    const defaults = createDefaultQuery();
    expect(defaults.expected_delivery_from).toBe("");
    expect(defaults.expected_delivery_to).toBe("");
    expect(matchPurchaseOrdersPeriod(defaults.expected_delivery_from, defaults.expected_delivery_to)).toBe(
      PURCHASE_ORDERS_UNBOUNDED_PERIOD,
    );

    const params = buildListSearchParams(defaults);
    expect(params.has("expected_delivery_from")).toBe(false);
    expect(params.has("expected_delivery_to")).toBe(false);
  });

  it("F5 without dates reconstructs Sem filtro; with dates reconstructs preset/custom", () => {
    const empty = parseQueryFromSearch("?page=1&page_size=50");
    expect(empty.expected_delivery_from).toBe("");
    expect(empty.expected_delivery_to).toBe("");
    expect(
      matchPurchaseOrdersPeriod(empty.expected_delivery_from, empty.expected_delivery_to),
    ).toBe(PURCHASE_ORDERS_UNBOUNDED_PERIOD);

    const month = resolvePeriodPreset("this_month", fixed)!;
    const withMonth = parseQueryFromSearch(
      `?expected_delivery_from=${month.from}&expected_delivery_to=${month.to}&page=2`,
    );
    expect(matchPurchaseOrdersPeriod(withMonth.expected_delivery_from, withMonth.expected_delivery_to, fixed)).toBe(
      "this_month",
    );

    const custom = parseQueryFromSearch(
      "?expected_delivery_from=2026-02-01&expected_delivery_to=2026-02-10&page=3",
    );
    expect(
      matchPurchaseOrdersPeriod(custom.expected_delivery_from, custom.expected_delivery_to, fixed),
    ).toBe("custom");
  });

  it("selecting a bounded preset implies page reset contract via caller patch shape", () => {
    const resolved = resolvePurchaseOrdersPeriod("this_month", fixed);
    expect(resolved).not.toBe("unbounded");
    expect(resolved).not.toBeNull();
    if (resolved === "unbounded" || resolved === null) return;
    const patch = {
      expected_delivery_from: resolved.from,
      expected_delivery_to: resolved.to,
      page: 1,
    };
    expect(patch.page).toBe(1);
    expect(patch.expected_delivery_from).toBe("2026-09-01");
  });
});
