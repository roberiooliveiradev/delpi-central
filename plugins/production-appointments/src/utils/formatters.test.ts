import { describe, expect, it } from "vitest";

import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatProtheusDate,
  formatProtheusTime,
  formatAppointmentDateTime,
  formatOperatorLabel,
  formatQuantity,
  formatResourceLabel,
  appointmentDateTimeSortKey,
} from "./formatters";
import {
  getThisMonthRange,
  getThisWeekRange,
  getTodayRange,
  resolveQuickRangePreset,
  validatePeriodRange,
} from "./dateRange";

describe("formatters", () => {
  it("formata moeda, data e quantidade (sem conversão de unidade)", () => {
    expect(formatCurrencyBrl(10.5)).toMatch(/R\$/);
    expect(formatDatePtBr("2026-04-27")).toBe("27/04/2026");
    expect(formatProtheusDate("20260715")).toBe("15/07/2026");
    expect(formatQuantity(3836)).toBe("3.836,00");
  });

  it("formata data/hora, operador e recurso do apontamento", () => {
    expect(formatProtheusTime("1430")).toBe("14:30");
    expect(formatProtheusTime("14:30:00")).toBe("14:30");
    expect(
      formatAppointmentDateTime({
        appointment_date: "20260716",
        start_time: "0800",
        end_time: "0915",
      }),
    ).toBe("16/07/2026 08:00–09:15");
    expect(
      formatOperatorLabel({ operator_name: "Maria Silva", operator_code: "000177" }),
    ).toBe("Maria Silva (000177)");
    expect(formatOperatorLabel({ operator_code: "000177" })).toBe("000177");
    expect(
      formatResourceLabel({ resource: "MC01", resource_name: "CORTE" }),
    ).toBe("MC01 — CORTE");
    expect(
      appointmentDateTimeSortKey({
        appointment_date: "20260716",
        start_time: "8:00",
      }),
    ).toBe("202607160800");
  });
});

describe("dateRange", () => {
  it("valida período e default do mês", () => {
    expect(validatePeriodRange("2026-04-01", "2026-04-27")).toBeNull();
    expect(validatePeriodRange("2026-05-01", "2026-04-01")).toMatch(/inicial/);
    const range = getThisMonthRange(new Date(2026, 3, 15));
    expect(range.dateStart).toBe("2026-04-01");
    expect(range.dateEnd).toBe("2026-04-15");
  });

  it("resolve hoje e esta semana (segunda → hoje)", () => {
    expect(getTodayRange(new Date(2026, 6, 15))).toEqual({
      dateStart: "2026-07-15",
      dateEnd: "2026-07-15",
    });
    // quarta-feira 15/07/2026 → segunda 13/07
    expect(getThisWeekRange(new Date(2026, 6, 15))).toEqual({
      dateStart: "2026-07-13",
      dateEnd: "2026-07-15",
    });
    // domingo 12/07/2026 → segunda 06/07
    expect(getThisWeekRange(new Date(2026, 6, 12))).toEqual({
      dateStart: "2026-07-06",
      dateEnd: "2026-07-12",
    });
  });

  it("resolveQuickRangePreset cobre atalhos do FiltersBar", () => {
    const ref = new Date(2026, 6, 15);
    expect(resolveQuickRangePreset("today", ref)).toEqual(getTodayRange(ref));
    expect(resolveQuickRangePreset("thisWeek", ref)).toEqual(getThisWeekRange(ref));
    expect(resolveQuickRangePreset("thisMonth", ref)).toEqual(getThisMonthRange(ref));
    expect(resolveQuickRangePreset("12m", ref)).toEqual({
      dateStart: "2025-08-01",
      dateEnd: "2026-07-15",
    });
  });
});
