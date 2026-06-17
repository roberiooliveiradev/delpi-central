import { describe, expect, it } from "vitest";
import {
  buildChartPresentationFromTable,
  tableSupportsChart,
} from "./buildChartPresentationFromTable";

describe("buildChartPresentationFromTable", () => {
  it("builds chart from eficiencia fabril rows", () => {
    const table = {
      type: "table" as const,
      title: "Eficiência fabril",
      columns: [
        { key: "filial", label: "Filial" },
        { key: "eficiencia_percentual", label: "Eficiência (%)" },
      ],
      rows: [
        { filial: "01", eficiencia_percentual: 98.5 },
        { filial: "02", eficiencia_percentual: 88.2 },
      ],
    };

    expect(tableSupportsChart(table)).toBe(true);

    const chart = buildChartPresentationFromTable(table);

    expect(chart?.type).toBe("chart");
    expect(chart?.data).toHaveLength(2);
    expect(chart?.config?.yAxis).toContain("eficiencia_percentual");
  });

  it("returns null for single row", () => {
    const table = {
      type: "table" as const,
      title: "X",
      columns: [{ key: "a", label: "A" }],
      rows: [{ a: 1 }],
    };

    expect(buildChartPresentationFromTable(table)).toBeNull();
  });
});
