import { describe, expect, it } from "vitest";

import { resolveObjectRibbonTab } from "./resolveObjectRibbonTab";

describe("resolveObjectRibbonTab", () => {
  it("Grade (canvas_table) abre aba canvasTable", () => {
    expect(
      resolveObjectRibbonTab({
        selected: {
          id: "g1",
          type: "canvas_table",
          rows: 2,
          cols: 2,
          cells: [],
          frame: { x: 0, y: 0, w: 20, h: 20 },
        } as never,
      }),
    ).toBe("canvasTable");
  });

  it("KPI e tabela live mantêm abas tipadas", () => {
    expect(
      resolveObjectRibbonTab({
        selected: { id: "k1", type: "kpi_view", frame: { x: 0, y: 0, w: 10, h: 10 } } as never,
      }),
    ).toBe("kpi");
    expect(
      resolveObjectRibbonTab({
        selected: { id: "t1", type: "table_view", frame: { x: 0, y: 0, w: 10, h: 10 } } as never,
      }),
    ).toBe("table");
  });
});
