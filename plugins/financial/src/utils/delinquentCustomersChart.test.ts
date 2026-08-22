import { describe, expect, it } from "vitest";

import type { DelinquencyCustomer } from "../types";
import {
  buildTopDelinquentChartRows,
  delinquencyRateByCount,
} from "./delinquentCustomersChart";

const customer = (
  overrides: Partial<DelinquencyCustomer> & Pick<DelinquencyCustomer, "customerCode" | "store">,
): DelinquencyCustomer => ({
  customerName: "Cliente",
  shortName: "CLI",
  totalTitles: 10,
  onTimeTitles: 8,
  lateTitles: 2,
  totalAmount: 0,
  lateAmount: 0,
  onTimePctByCount: 80,
  onTimePctByAmount: 80,
  ...overrides,
});

describe("delinquencyRateByCount", () => {
  it("uses late titles over total titles, not absolute volume", () => {
    const heavy = customer({
      customerCode: "A",
      store: "01",
      totalTitles: 100,
      lateTitles: 20,
      onTimePctByCount: 80,
    });
    const light = customer({
      customerCode: "B",
      store: "01",
      totalTitles: 4,
      lateTitles: 3,
      onTimePctByCount: 25,
    });

    expect(delinquencyRateByCount(heavy)).toBe(20);
    expect(delinquencyRateByCount(light)).toBe(75);
    expect(delinquencyRateByCount(light)).toBeGreaterThan(delinquencyRateByCount(heavy));
  });
});

describe("buildTopDelinquentChartRows", () => {
  it("ranks by proportional delinquency and drops clients without late titles", () => {
    const rows = buildTopDelinquentChartRows([
      customer({ customerCode: "A", store: "01", totalTitles: 50, lateTitles: 10 }),
      customer({ customerCode: "B", store: "01", totalTitles: 5, lateTitles: 4 }),
      customer({ customerCode: "C", store: "01", totalTitles: 8, lateTitles: 0 }),
    ]);

    expect(rows.map((row) => row.customerCode)).toEqual(["B", "A"]);
    expect(rows[0]?.delinquencyPct).toBe(80);
  });
});
