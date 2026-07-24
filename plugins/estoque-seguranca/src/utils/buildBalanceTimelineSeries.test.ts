import { describe, expect, it } from "vitest";

import type { SafetyStockProjectionLedgerEntry } from "../types/safetyStock";
import {
  buildBalanceTimelineSeries,
  collectPurchaseInflowsByDate,
  countBusinessDaysInclusive,
  formatIsoDateUtc,
  formatMonthTickPt,
  isBusinessDayUtc,
  resolveAverageDailyConsumption,
} from "./buildBalanceTimelineSeries";

function entry(
  partial: Partial<SafetyStockProjectionLedgerEntry> &
    Pick<SafetyStockProjectionLedgerEntry, "sequence" | "origin" | "running_balance">,
): SafetyStockProjectionLedgerEntry {
  return {
    event_date: null,
    date_status: "unscheduled",
    date_semantics: "test",
    origin_label: partial.origin,
    reference: "",
    warehouse: "01",
    movement: 0,
    inflow: 0,
    outflow: 0,
    unit_compatible: true,
    projection_eligible: true,
    ...partial,
  };
}

describe("business day helpers", () => {
  it("identifica dias úteis em UTC", () => {
    expect(isBusinessDayUtc(new Date(Date.UTC(2026, 6, 20)))).toBe(true); // seg
    expect(isBusinessDayUtc(new Date(Date.UTC(2026, 6, 25)))).toBe(false); // sáb
  });

  it("conta dias úteis inclusivos", () => {
    const start = new Date(Date.UTC(2026, 6, 20));
    const end = new Date(Date.UTC(2026, 6, 26));
    expect(countBusinessDaysInclusive(start, end)).toBe(5);
  });

  it("formata tick mensal", () => {
    expect(formatMonthTickPt(new Date(Date.UTC(2026, 7, 1)))).toBe("ago de 26");
  });
});

describe("resolveAverageDailyConsumption", () => {
  it("divide pelo número de dias úteis do período", () => {
    // 20/07/2026 a 24/07/2026 = 5 dias úteis
    expect(
      resolveAverageDailyConsumption(100, "2026-07-20", "2026-07-24"),
    ).toBeCloseTo(20, 5);
  });

  it("usa 252 dias úteis quando não há período", () => {
    expect(resolveAverageDailyConsumption(252)).toBeCloseTo(1, 5);
  });
});

describe("collectPurchaseInflowsByDate", () => {
  it("agrega pedidos por data e overdue no as_of", () => {
    const map = collectPurchaseInflowsByDate(
      [
        entry({
          sequence: 1,
          origin: "purchase_order",
          running_balance: 0,
          event_date: "2026-08-10",
          date_status: "scheduled",
          inflow: 40,
        }),
        entry({
          sequence: 2,
          origin: "purchase_order",
          running_balance: 0,
          event_date: "2026-05-01",
          date_status: "overdue",
          inflow: 10,
        }),
        entry({
          sequence: 3,
          origin: "commitment",
          running_balance: 0,
          event_date: "2026-08-10",
          date_status: "scheduled",
          outflow: 99,
        }),
      ],
      "2026-07-20",
    );
    expect(map.get("2026-08-10")).toBe(40);
    expect(map.get("2026-07-20")).toBe(10);
  });
});

describe("buildBalanceTimelineSeries", () => {
  it("projeta consumo em dias úteis e entradas de pedidos", () => {
    const series = buildBalanceTimelineSeries(
      [
        entry({
          sequence: 1,
          origin: "initial_balance",
          running_balance: 100,
          event_date: "2026-07-20",
          date_status: "today",
        }),
        entry({
          sequence: 2,
          origin: "purchase_order",
          running_balance: 150,
          event_date: "2026-07-22",
          date_status: "scheduled",
          inflow: 50,
        }),
      ],
      { as_of_date: "2026-07-20", initial_balance: 100 },
      { averageDailyConsumption: 10, calendarDays: 5 },
    );

    expect(series).not.toBeNull();
    expect(series!.periodStart).toBe("2026-07-20");
    expect(series!.periodEnd).toBe("2026-07-25");
    expect(series!.points).toHaveLength(6);

    // 20/07 seg: 100-10=90
    expect(series!.points[0]?.balance).toBeCloseTo(90, 5);
    // 21/07 ter: 90-10=80
    expect(series!.points[1]?.balance).toBeCloseTo(80, 5);
    // 22/07 qua: 80-10+50=120
    expect(series!.points[2]?.balance).toBeCloseTo(120, 5);
    // 25/07 sáb: sem consumo
    expect(series!.points[5]?.isBusinessDay).toBe(false);
  });

  it("marca a primeira ruptura quando o saldo fica negativo", () => {
    const series = buildBalanceTimelineSeries(
      [],
      { as_of_date: "2026-07-20", initial_balance: 15 },
      { averageDailyConsumption: 10, calendarDays: 4 },
    );
    expect(series!.firstShortageDate).toBe("2026-07-21");
    expect(series!.points[0]?.isShortage).toBe(false);
    expect(series!.points[1]?.isShortage).toBe(true);
    expect(series!.points[1]?.balanceNegative).toBeLessThan(0);
    expect(series!.points[1]?.balancePositive).toBe(0);
  });

  it("permite projetar sem entradas de pedidos de compra", () => {
    const items = [
      entry({
        sequence: 1,
        origin: "initial_balance",
        running_balance: 100,
        event_date: "2026-07-20",
        date_status: "today",
      }),
      entry({
        sequence: 2,
        origin: "purchase_order",
        running_balance: 150,
        event_date: "2026-07-22",
        date_status: "scheduled",
        inflow: 50,
      }),
    ];
    const withOrders = buildBalanceTimelineSeries(
      items,
      { as_of_date: "2026-07-20", initial_balance: 100 },
      { averageDailyConsumption: 10, calendarDays: 5, includePurchaseOrders: true },
    );
    const withoutOrders = buildBalanceTimelineSeries(
      items,
      { as_of_date: "2026-07-20", initial_balance: 100 },
      { averageDailyConsumption: 10, calendarDays: 5, includePurchaseOrders: false },
    );

    // 22/07: com pedido 120; sem pedido 70
    expect(withOrders!.points[2]?.balance).toBeCloseTo(120, 5);
    expect(withoutOrders!.points[2]?.balance).toBeCloseTo(70, 5);
    expect(withoutOrders!.firstShortageDate).toBeNull();
  });

  it("preenche monthTick no primeiro ponto", () => {
    const series = buildBalanceTimelineSeries(
      [],
      { as_of_date: "2026-07-20", initial_balance: 1 },
      { averageDailyConsumption: 0, calendarDays: 2 },
    );
    expect(series!.points[0]?.monthTick).toBe("jul de 26");
    expect(formatIsoDateUtc(new Date(Date.UTC(2026, 6, 20)))).toBe("2026-07-20");
  });
});
