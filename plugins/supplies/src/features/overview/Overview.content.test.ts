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
import { resolvePeriodPreset } from "./periodPreset";
import {
  formatOperationalUnitCode,
  parseSuppliesBranchCsv,
  resolveApiBranch,
  serializeSuppliesBranchCsv,
  suppliesUnitOptions,
} from "./suppliesBranchFilters";

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
});
