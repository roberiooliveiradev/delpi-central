import { describe, expect, it } from "vitest";

import {
  applyDashboardPeriodPreset,
  defaultDashboardPeriod,
  effectiveDashboardPeriodPreset,
} from "./dashboardPeriod";

describe("dashboardPeriod", () => {
  const now = new Date("2026-08-13T18:00:00.000Z");
  const current = {
    dataInicial: "2026-08-01",
    dataFinal: "2026-08-13",
    competence: "2026-08",
  };

  it("default is this_month first day through today", () => {
    const defaults = defaultDashboardPeriod(now);
    expect(defaults).toEqual({
      dataInicial: "2026-08-01",
      dataFinal: "2026-08-13",
      competence: "2026-08",
      periodPreset: "this_month",
    });
  });

  it("applies today", () => {
    expect(applyDashboardPeriodPreset("today", current, now)).toEqual({
      dataInicial: "2026-08-13",
      dataFinal: "2026-08-13",
      competence: "2026-08",
      storedPreset: "today",
      forceCustom: false,
    });
  });

  it("applies this_week Monday through today", () => {
    expect(applyDashboardPeriodPreset("this_week", current, now)).toEqual({
      dataInicial: "2026-08-10",
      dataFinal: "2026-08-13",
      competence: "",
      storedPreset: "this_week",
      forceCustom: false,
    });
  });

  it("applies last_month full civil month", () => {
    expect(applyDashboardPeriodPreset("last_month", current, now)).toEqual({
      dataInicial: "2026-07-01",
      dataFinal: "2026-07-31",
      competence: "2026-07",
      storedPreset: "last_month",
      forceCustom: false,
    });
  });

  it("applies this_quarter full civil quarter", () => {
    expect(applyDashboardPeriodPreset("this_quarter", current, now)).toEqual({
      dataInicial: "2026-07-01",
      dataFinal: "2026-09-30",
      competence: "",
      storedPreset: "this_quarter",
      forceCustom: false,
    });
  });

  it("applies this_year Jan 1 through today", () => {
    expect(applyDashboardPeriodPreset("this_year", current, now)).toEqual({
      dataInicial: "2026-01-01",
      dataFinal: "2026-08-13",
      competence: "",
      storedPreset: "this_year",
      forceCustom: false,
    });
  });

  it("applies last_12_months first day 11 months back through today", () => {
    expect(applyDashboardPeriodPreset("last_12_months", current, now)).toEqual({
      dataInicial: "2025-09-01",
      dataFinal: "2026-08-13",
      competence: "",
      storedPreset: "last_12_months",
      forceCustom: false,
    });
  });

  it("custom keeps current dates", () => {
    expect(applyDashboardPeriodPreset("custom", current, now)).toEqual({
      ...current,
      storedPreset: null,
      forceCustom: true,
    });
  });

  it("manual range that no longer matches stored preset becomes custom", () => {
    expect(
      effectiveDashboardPeriodPreset(
        { dataInicial: "2026-01-01", dataFinal: "2026-02-01", competence: "" },
        "this_month",
        false,
        now,
      ),
    ).toBe("custom");
  });

  it("forceCustom stays Personalizado even when dates match this_month", () => {
    expect(effectiveDashboardPeriodPreset(current, null, true, now)).toBe("custom");
  });
});
