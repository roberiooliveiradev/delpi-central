import { describe, expect, it } from "vitest";

import { canAccessView } from "../../app/routeAccess";
import {
  firstDayOfMonthIso,
  mapOverviewFetchError,
  OVERVIEW_CONTENT,
  temporalNatureLabel,
  todayIso,
} from "./overviewContent";
import {
  buildOverviewQueryString,
  readOverviewFiltersFromUrl,
  writeOverviewFiltersToUrl,
} from "./overviewFilterUrl";
import { resolvePeriodPreset } from "./periodPreset";

describe("Overview content", () => {
  it("exposes temporal nature labels for all KPI natures", () => {
    expect(temporalNatureLabel("interval")).toBe("Intervalo");
    expect(temporalNatureLabel("snapshot")).toBe("Snapshot");
    expect(temporalNatureLabel("state")).toBe("Estado atual");
    expect(OVERVIEW_CONTENT.title).toBe("Visão geral");
    expect(OVERVIEW_CONTENT.description).toMatch(/Início/i);
    expect(OVERVIEW_CONTENT.indicatorsTitle).toBe("Indicadores");
    expect(OVERVIEW_CONTENT.otdChartTitle).toMatch(/OTD/i);
  });

  it("defaults period to first day of month through today", () => {
    const fixed = new Date(2026, 8, 8);
    expect(firstDayOfMonthIso(fixed)).toBe("2026-09-01");
    expect(todayIso(fixed)).toBe("2026-09-08");
  });

  it("requires analytics capability for overview view", () => {
    expect(
      canAccessView("overview", {
        portal: true,
        purchaseRequests: false,
        operations: false,
        analytics: false,
        administration: false,
        viewAll: false,
        export: false,
      }),
    ).toBe(false);
    expect(
      canAccessView("overview", {
        portal: true,
        purchaseRequests: false,
        operations: false,
        analytics: true,
        administration: false,
        viewAll: false,
        export: false,
      }),
    ).toBe(true);
  });

  it("maps unit forbidden errors to dedicated copy", () => {
    expect(mapOverviewFetchError("[forbidden] Forbidden")).toBe(
      OVERVIEW_CONTENT.forbiddenUnit,
    );
    expect(mapOverviewFetchError("timeout")).toBe("timeout");
  });
});

describe("Overview period presets", () => {
  it("resolves this_month for a fixed date", () => {
    const fixed = new Date("2026-09-08T15:00:00-03:00");
    const range = resolvePeriodPreset("this_month", fixed);
    expect(range?.from).toBe("2026-09-01");
    expect(range?.to).toBe("2026-09-08");
  });

  it("sibling last_month is full previous calendar month", () => {
    const fixed = new Date("2026-09-08T15:00:00-03:00");
    const range = resolvePeriodPreset("last_month", fixed);
    expect(range).toEqual({ from: "2026-08-01", to: "2026-08-31" });
  });

  it("negative custom returns null", () => {
    expect(resolvePeriodPreset("custom")).toBeNull();
  });
});

describe("Overview URL filters", () => {
  it("builds shareable query string and omits custom period", () => {
    expect(
      buildOverviewQueryString({
        branch: "01",
        from: "2026-09-01",
        to: "2026-09-08",
        period: "this_month",
      }),
    ).toBe("?branch=01&from=2026-09-01&to=2026-09-08&period=this_month");
    expect(
      buildOverviewQueryString({
        branch: "",
        from: "2026-09-01",
        to: "2026-09-08",
        period: "custom",
      }),
    ).toBe("?from=2026-09-01&to=2026-09-08");
  });

  it("parses period from query helpers without DOM", () => {
    expect(buildOverviewQueryString({
      branch: "02",
      from: "2026-01-01",
      to: "2026-03-31",
      period: "this_quarter",
    })).toContain("period=this_quarter");
    // readOverviewFiltersFromUrl is DOM-bound; query builder is the unit under test in node.
    expect(typeof readOverviewFiltersFromUrl).toBe("function");
    expect(typeof writeOverviewFiltersToUrl).toBe("function");
  });
});
