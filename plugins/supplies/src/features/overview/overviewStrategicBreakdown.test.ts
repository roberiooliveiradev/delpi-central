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
  it("renders consolidated, SC and ES when Todas payload includes them", () => {
    const rows = buildStrategicUnitRows(strategic());
    expect(rows.map((row) => row.label)).toEqual([
      "Consolidado",
      "Santa Catarina",
      "Espírito Santo",
    ]);
    expect(rows[0]?.realizedLabel).toContain("95,2");
    expect(rows[0]?.goalCaption).toBe("Meta parcial");
    expect(rows[2]?.realizedLabel).toBe("—");
    expect(rows[2]?.goalLabel).toBe("Meta não cadastrada");
  });

  it("shows only the selected unit", () => {
    const sc = buildStrategicUnitRows(
      strategic({ realized: { "01": 96.1 }, goals: { "01": 97 } }),
    );
    expect(sc.map((row) => row.key)).toEqual(["01"]);
    const es = buildStrategicUnitRows(
      strategic({ realized: { "02": 94.3 }, goals: { "02": 97 } }),
    );
    expect(es.map((row) => row.key)).toEqual(["02"]);
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

  it("does not invent a strategic block without an indicator id", () => {
    expect(buildStrategicUnitRows(null)).toEqual([]);
    expect(buildStrategicUnitRows(strategic({ indicatorId: null }))).toEqual([]);
  });

  it("does not sum units in the portal", () => {
    const rows = buildStrategicUnitRows(strategic());
    const source = buildStrategicUnitRows.toString();
    expect(source).not.toContain("reduce");
    expect(rows[0]?.realizedLabel).not.toContain("191");
  });
});
