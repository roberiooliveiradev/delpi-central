import { describe, expect, it } from "vitest";

import { canAccessView } from "../../app/routeAccess";
import {
  firstDayOfMonthIso,
  mapOverviewFetchError,
  OVERVIEW_CONTENT,
  temporalNatureLabel,
  todayIso,
} from "./overviewContent";
import { buildOverviewQueryString } from "./overviewFilterUrl";
import { resolvePeriodPreset, resolvePeriodKindChip } from "./periodPreset";
import {
  formatOperationalUnitCode,
  parseSuppliesBranchCsv,
  resolveApiBranch,
  serializeSuppliesBranchCsv,
  suppliesUnitOptions,
} from "./suppliesBranchFilters";
import { mergeSeriesWithPriorYear, shiftPeriodRangeByYears } from "./periodShift";

describe("Overview content", () => {
  it("exposes temporal nature labels for all KPI natures", () => {
    expect(temporalNatureLabel("interval")).toBe("Intervalo");
    expect(temporalNatureLabel("snapshot")).toBe("Snapshot");
    expect(temporalNatureLabel("state")).toBe("Estado atual");
    expect(OVERVIEW_CONTENT.title).toBe("Visão geral");
    expect(OVERVIEW_CONTENT.description).toMatch(/Início/i);
    expect(OVERVIEW_CONTENT.indicatorsTitle).toBe("Indicadores");
    expect(OVERVIEW_CONTENT.otdChartTitle).toMatch(/OTD/i);
    expect(OVERVIEW_CONTENT.branchLabel).toBe("Unidade");
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

describe("Overview URL filters + unit MultiSelect", () => {
  it("builds shareable query with branch CSV codes", () => {
    expect(
      buildOverviewQueryString({
        branches: ["01"],
        from: "2026-09-01",
        to: "2026-09-08",
        period: "this_month",
      }),
    ).toBe("?branch=01&from=2026-09-01&to=2026-09-08&period=this_month");
    expect(
      buildOverviewQueryString({
        branches: ["01", "02"],
        from: "2026-09-01",
        to: "2026-09-08",
        period: "custom",
      }),
    ).toBe("?branch=01%2C02&from=2026-09-01&to=2026-09-08");
    expect(
      buildOverviewQueryString({
        branches: [],
        from: "2026-09-01",
        to: "2026-09-08",
        period: "custom",
      }),
    ).toBe("?from=2026-09-01&to=2026-09-08");
  });

  it("labels units as Santa Catarina and Espírito Santo", () => {
    expect(formatOperationalUnitCode("01")).toBe("Santa Catarina");
    expect(formatOperationalUnitCode("02")).toBe("Espírito Santo");
    const options = suppliesUnitOptions(["01", "02"]);
    expect(options.map((o) => o.label)).toEqual(["Santa Catarina", "Espírito Santo"]);
  });

  it("resolves API branch single vs consolidated", () => {
    expect(resolveApiBranch(["01"], ["01", "02"])).toBe("01");
    expect(resolveApiBranch(["01", "02"], ["01", "02"])).toBeUndefined();
    expect(resolveApiBranch([], ["01", "02"])).toBeUndefined();
    expect(parseSuppliesBranchCsv("01,02")).toEqual(["01", "02"]);
    expect(serializeSuppliesBranchCsv(["01", "02"])).toBe("01,02");
  });

  it("maps period presets to MTD/YTD chips", () => {
    expect(resolvePeriodKindChip("this_month")).toBe("MTD");
    expect(resolvePeriodKindChip("this_year")).toBe("YTD");
    expect(resolvePeriodKindChip("this_quarter")).toBeNull();
    expect(resolvePeriodKindChip("custom")).toBeNull();
  });

  it("shifts period range for YoY overlay", () => {
    expect(shiftPeriodRangeByYears({ from: "2026-09-01", to: "2026-09-30" }, -1)).toEqual({
      from: "2025-09-01",
      to: "2025-09-30",
    });
    expect(
      mergeSeriesWithPriorYear([{ period: "2026-09", otdPct: 90 }], [{ otdPct: 88 }], (p) => ({
        otdPctPrior: p?.otdPct ?? null,
      })),
    ).toEqual([{ period: "2026-09", otdPct: 90, otdPctPrior: 88 }]);
  });
});

describe("overview KPI presentation", () => {
  const ctx = {
    from: "2026-09-01",
    to: "2026-09-08",
    scopeLabel: "Consolidado (unidades liberadas)",
    consolidated: true,
  };

  it("positive: uses SI iddScore (not local recalc) and goal badges", async () => {
    const { buildOverviewKpiPresentation } = await import("./overviewKpiPresentation");
    const presentation = buildOverviewKpiPresentation(
      {
        id: "KPI-OTD",
        viewId: "overview",
        title: "OTD compras",
        description: "Pontualidade",
        temporalNature: "interval",
        periodLabel: "2026-09-01 → 2026-09-08",
        value: 92,
        displayValue: "92,0%",
        unit: "%",
        meta: 98,
        iddScore: 6.57,
        status: "available",
        source: "api-delpi",
      },
      ctx,
    );
    expect(presentation.goalLabel).toBeTruthy();
    expect(presentation.goalPerformanceBadge?.statusLabel).toMatch(/meta/i);
    expect(presentation.goalPerformanceBadge?.directionLabel).toMatch(/maior|menor/i);
    expect(presentation.iddScoreLabel).toBe("6,57");
    expect(presentation.contextLabel).toMatch(/Consolidado/);
  });

  it("sibling: formats another SI score for stock KPI", async () => {
    const { buildOverviewKpiPresentation } = await import("./overviewKpiPresentation");
    const presentation = buildOverviewKpiPresentation(
      {
        id: "KPI-STOCK-VALUE",
        viewId: "overview",
        title: "Estoque",
        description: "Valor",
        temporalNature: "interval",
        periodLabel: "…",
        value: 1_000_000,
        displayValue: "R$ 1.000.000,00",
        unit: "R$",
        meta: 1_200_000,
        iddScore: 8.2,
        status: "available",
        source: "api-delpi",
      },
      ctx,
    );
    expect(presentation.iddScoreLabel).toBe("8,20");
  });

  it("negative: without SI score does not invent local IDD", async () => {
    const { buildOverviewKpiPresentation } = await import("./overviewKpiPresentation");
    const presentation = buildOverviewKpiPresentation(
      {
        id: "KPI-OTD",
        viewId: "overview",
        title: "OTD compras",
        description: "Pontualidade",
        temporalNature: "interval",
        periodLabel: "…",
        value: 92,
        displayValue: "92,0%",
        unit: "%",
        meta: 98,
        iddScore: null,
        status: "available",
        source: "api-delpi",
      },
      ctx,
    );
    expect(presentation.iddScoreLabel).toBeNull();
  });
});
