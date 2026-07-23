import { describe, expect, it } from "vitest";

import { canLinkBlockToProjectDataSource } from "./DataSourceLinkSection";

describe("DataSourceLinkSection flow", () => {
  it("texto, forma, KPI, gráfico e tabela podem usar fontes do slide", () => {
    expect(canLinkBlockToProjectDataSource({ type: "text" })).toBe(true);
    expect(canLinkBlockToProjectDataSource({ type: "heading" })).toBe(true);
    expect(canLinkBlockToProjectDataSource({ type: "shape" })).toBe(true);
    expect(canLinkBlockToProjectDataSource({ type: "kpi_view" })).toBe(true);
    expect(canLinkBlockToProjectDataSource({ type: "chart_view" })).toBe(true);
    expect(canLinkBlockToProjectDataSource({ type: "table_view" })).toBe(true);
    expect(canLinkBlockToProjectDataSource({ type: "canvas_table" })).toBe(true);
  });

  it("imagem e fonte pura não usam o seletor de vínculo", () => {
    expect(canLinkBlockToProjectDataSource({ type: "image" })).toBe(false);
    expect(canLinkBlockToProjectDataSource({ type: "data_source" })).toBe(false);
    expect(canLinkBlockToProjectDataSource(null)).toBe(false);
  });
});
