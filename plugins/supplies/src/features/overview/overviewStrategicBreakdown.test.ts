import { describe, expect, it } from "vitest";

import type { OverviewKpiStrategic } from "../../api/overview";
import {
  buildStrategicUnitRows,
  formatDepartmentScore,
  periodGoalCaption,
} from "./overviewStrategicBreakdown";

function strategic(overrides: Partial<OverviewKpiStrategic> = {}): OverviewKpiStrategic {
  return {
    indicatorId: "supplies-otd",
    score: 6.57,
    realized: { consolidated: 95.2, "01": 96.1, "02": null },
    goals: { consolidated: 97, "01": 97, "02": null },
    goalValue: 98,
    comparableGoal: 30,
    referenceGoal: 90,
    goalMode: "standard",
    goalPeriodKind: "partial",
    goalPeriodPartial: true,
    performanceDirection: "higher_is_better",
    valueUnit: "percent",
    valuePrefix: null,
    valueSuffix: "%",
    valueDecimals: 1,
    ...overrides,
  };
}

describe("overview strategic breakdown", () => {
  it("shows only the consolidated row when Todas is active, even if other units exist", () => {
    const rows = buildStrategicUnitRows(strategic(), "consolidated");
    expect(rows.map((row) => row.key)).toEqual(["consolidated"]);
    expect(rows.map((row) => row.label)).toEqual(["Consolidado"]);
    expect(rows.some((row) => row.label === "Santa Catarina")).toBe(false);
    expect(rows.some((row) => row.label === "Espírito Santo")).toBe(false);
  });

  it("shows only the selected unit", () => {
    expect(buildStrategicUnitRows(strategic(), "01").map((row) => row.key)).toEqual(["01"]);
    expect(buildStrategicUnitRows(strategic(), "02").map((row) => row.label)).toEqual([
      "Espírito Santo",
    ]);
  });

  it("does not turn a missing department score into zero", () => {
    expect(formatDepartmentScore(null)).toBeNull();
    expect(formatDepartmentScore(undefined)).toBeNull();
    expect(formatDepartmentScore(7.25)).toBe("7,25");
  });

  it("uses accumulated and exact goal captions from SI", () => {
    expect(periodGoalCaption("accumulated")).toBe("Meta acumulada");
    expect(periodGoalCaption("exact")).toBe("Meta");
    expect(periodGoalCaption("partial")).toBe("Meta parcial");
  });

  it("does not invent a strategic block without an indicator id or scope", () => {
    expect(buildStrategicUnitRows(null, "consolidated")).toEqual([]);
    expect(buildStrategicUnitRows(strategic({ indicatorId: null }), "01")).toEqual([]);
    expect(buildStrategicUnitRows(strategic(), null)).toEqual([]);
  });
});
