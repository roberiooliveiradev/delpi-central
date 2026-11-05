import { describe, expect, it } from "vitest";

import { isDataSourceBlock, isDataViewBlock } from "./comunicadoDataArchitecture";

describe("predicados de bloco de dados", () => {
  it("estreita só data_source", () => {
    const source = { type: "data_source", id: "src" };
    const chart = { type: "chart_view", id: "chart" };
    expect(isDataSourceBlock(source)).toBe(true);
    expect(isDataSourceBlock(chart)).toBe(false);
    expect(isDataSourceBlock({ type: "text" })).toBe(false);
    expect(isDataSourceBlock({ type: "kpi_view" })).toBe(false);
  });

  it("estreita chart, tabela e KPI e rejeita os demais", () => {
    expect(isDataViewBlock({ type: "chart_view" })).toBe(true);
    expect(isDataViewBlock({ type: "table_view" })).toBe(true);
    expect(isDataViewBlock({ type: "kpi_view" })).toBe(true);
    expect(isDataViewBlock({ type: "data_source" })).toBe(false);
    expect(isDataViewBlock({ type: "text" })).toBe(false);
    expect(isDataViewBlock({ type: "canvas_table" })).toBe(false);
    expect(isDataViewBlock({ type: "shape" })).toBe(false);
  });
});
