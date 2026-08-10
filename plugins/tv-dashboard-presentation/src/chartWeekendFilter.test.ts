import { describe, expect, it } from "vitest";

import {
  EXCLUDE_WEEKENDS_PARAM,
  applyExcludeWeekendsToChart,
  filterSeriesPointsExcludingWeekends,
  isDailyGranularityValue,
  isEffectiveDailyGranularity,
  mergeChartViewFilterParams,
  omitVisualOnlyDataParams,
  parseCategoryPointDate,
  routeSupportsDailyGranularity,
  shouldApplyExcludeWeekends,
} from "./chartWeekendFilter";

describe("parseCategoryPointDate", () => {
  it("lê ISO e DD/MM/AA sem deslocar fuso", () => {
    const iso = parseCategoryPointDate("2026-08-08");
    expect(iso?.getFullYear()).toBe(2026);
    expect(iso?.getMonth()).toBe(7);
    expect(iso?.getDate()).toBe(8);
    const br = parseCategoryPointDate("09/08/26");
    expect(br?.getFullYear()).toBe(2026);
    expect(br?.getDate()).toBe(9);
  });

  it("ignora rótulos que não são dia", () => {
    expect(parseCategoryPointDate("ago/2026")).toBeNull();
    expect(parseCategoryPointDate("S32")).toBeNull();
    expect(parseCategoryPointDate("Produto A")).toBeNull();
  });
});

describe("filterSeriesPointsExcludingWeekends", () => {
  it("remove sábado e domingo e mantém dia útil e rótulo opaco", () => {
    const points = filterSeriesPointsExcludingWeekends([
      { label: "08/08/26", value: 1 },
      { label: "09/08/26", value: 2 },
      { label: "10/08/26", value: 3 },
      { label: "Centro 01", value: 4 },
    ]);
    expect(points.map((item) => item.label)).toEqual(["10/08/26", "Centro 01"]);
  });
});

describe("shouldApplyExcludeWeekends", () => {
  it("só aplica com flag e granularidade diária (ou sem granularidade)", () => {
    expect(shouldApplyExcludeWeekends({ excludeWeekends: true, granularity: "day" })).toBe(true);
    expect(shouldApplyExcludeWeekends({ excludeWeekends: true, granularity: "month" })).toBe(false);
    expect(shouldApplyExcludeWeekends({ excludeWeekends: false, granularity: "day" })).toBe(false);
    expect(shouldApplyExcludeWeekends({ excludeWeekends: "true" })).toBe(true);
  });
});

describe("routeSupportsDailyGranularity / isEffectiveDailyGranularity", () => {
  it("reconhece enum com day e granularidade fixa", () => {
    expect(
      routeSupportsDailyGranularity({ granularity: { enum: ["day", "week", "month"] } }),
    ).toBe(true);
    expect(routeSupportsDailyGranularity({ granularity: { enum: ["week", "month"] } })).toBe(false);
    expect(routeSupportsDailyGranularity({}, { granularity: "day" })).toBe(true);
    expect(isDailyGranularityValue("dia")).toBe(true);
  });

  it("mostra o filtro só quando o valor efetivo é dia ou a rota é diária fixa", () => {
    expect(
      isEffectiveDailyGranularity(
        { granularity: { enum: ["day", "week"], default: "week" } },
        {},
      ),
    ).toBe(false);
    expect(
      isEffectiveDailyGranularity(
        { granularity: { enum: ["day", "week"], default: "week" } },
        { granularity: "day" },
      ),
    ).toBe(true);
    expect(
      isEffectiveDailyGranularity({ [EXCLUDE_WEEKENDS_PARAM]: { type: "boolean" } }, {}),
    ).toBe(true);
  });
});

describe("applyExcludeWeekendsToChart", () => {
  it("filtra pontos e séries", () => {
    const next = applyExcludeWeekendsToChart({
      points: [
        { label: "2026-08-08", value: 10 },
        { label: "2026-08-10", value: 20 },
      ],
      series: [
        {
          name: "OEE",
          points: [
            { label: "2026-08-08", value: 10 },
            { label: "2026-08-10", value: 20 },
          ],
        },
      ],
      chartType: "bar",
    });
    expect(next?.points?.map((item) => item.label)).toEqual(["2026-08-10"]);
    expect(next?.series?.[0]?.points.map((item) => item.label)).toEqual(["2026-08-10"]);
  });
});

describe("mergeChartViewFilterParams / omitVisualOnlyDataParams", () => {
  it("camada posterior vence e omite só o param visual", () => {
    expect(
      mergeChartViewFilterParams([
        { excludeWeekends: false, granularity: "day" },
        { excludeWeekends: true },
      ]),
    ).toEqual({ excludeWeekends: true, granularity: "day" });
    expect(omitVisualOnlyDataParams({ branch: "01", excludeWeekends: true, granularity: "day" })).toEqual({
      branch: "01",
      granularity: "day",
    });
  });
});
