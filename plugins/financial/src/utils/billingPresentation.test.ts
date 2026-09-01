import { describe, expect, it } from "vitest";

import {
  billingSeriesKeys,
  clampPercent,
  compositionStatementRows,
  customerPieRows,
  waterfallBarWidth,
  waterfallPeak,
} from "./billingPresentation";

describe("billingPresentation", () => {
  it("clamps attainment to 0–100 for the meter", () => {
    expect(clampPercent(90.91)).toBe(90.91);
    expect(clampPercent(140)).toBe(100);
    expect(clampPercent(-8)).toBe(0);
    expect(clampPercent(null)).toBe(0);
  });

  it("selects series keys by unit", () => {
    expect(billingSeriesKeys("01")).toEqual(["rol01"]);
    expect(billingSeriesKeys("02")).toEqual(["rol02"]);
    expect(billingSeriesKeys("all")).toEqual(["rol01", "rol02"]);
  });

  it("sizes waterfall bars from the peak line", () => {
    const peak = waterfallPeak([
      { key: "gross", label: "Bruto", value: 100, role: "add" },
      { key: "tax", label: "Imposto", value: 25, role: "subtract" },
    ]);
    expect(peak).toBe(100);
    expect(waterfallBarWidth(25, peak)).toBe(25);
    expect(waterfallBarWidth(0, peak)).toBe(0);
    expect(waterfallBarWidth(1, peak)).toBe(6);
  });

  it("builds pie slices from ranked customers and others", () => {
    const palette = ["#111", "#222", "#333"];
    const rows = customerPieRows(
      [
        {
          customerCode: "000001",
          customerStore: "01",
          customerName: "WEG MOTORES",
          rol: 100,
          grossRevenue: 120,
          sharePct: 50,
          rank: 1,
        },
        {
          customerCode: "000001",
          customerStore: "02",
          customerName: "WEG MOTORES",
          rol: 40,
          grossRevenue: 50,
          sharePct: 20,
          rank: 2,
        },
        {
          customerCode: "000099",
          customerStore: "01",
          customerName: "Zerado",
          rol: 0,
          grossRevenue: 0,
          sharePct: 0,
          rank: 3,
        },
      ],
      {
        customerCode: "",
        customerStore: "",
        customerName: "others",
        rol: 60,
        grossRevenue: 70,
        sharePct: 30,
        rank: 0,
      },
      "Demais clientes",
      palette,
    );
    expect(rows.map((row) => row.label)).toEqual(["WEG MOTORES", "WEG MOTORES · 02", "Demais clientes"]);
    expect(rows.map((row) => row.fill)).toEqual(["#111", "#222", "#333"]);
    expect(rows[2]?.rol).toBe(60);
  });

  it("walks the ROL statement with running balance", () => {
    const rows = compositionStatementRows([
      { key: "gross", label: "Bruto", value: 100, role: "add" },
      { key: "disc", label: "Descontos", value: 10, role: "subtract" },
      { key: "tax", label: "Impostos", value: 15, role: "subtract" },
      { key: "rol", label: "ROL", value: 75, role: "result" },
    ]);
    expect(rows.map((row) => row.balance)).toEqual([100, 90, 75, 75]);
    expect(rows[3]?.role).toBe("result");
  });
});
