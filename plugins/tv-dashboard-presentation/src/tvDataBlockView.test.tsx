import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ComunicadoDataBlock } from "./comunicadoTypes";
import { TvDataBlockView } from "./tvDataBlockView";

describe("TvDataBlockView", () => {
  const baseBlock: ComunicadoDataBlock = {
    id: "b1",
    type: "data_table",
    frame: { x: 0, y: 0, w: 50, h: 30 },
    dataBinding: {
      operationId: "search_products",
      displayMode: "table",
      label: "Produtos",
    },
    resolved: {
      label: "Produtos",
      table: {
        columns: [
          { key: "code", label: "Código" },
          { key: "name", label: "Nome" },
        ],
        rows: [{ code: "90123456", name: "Produto A" }],
      },
    },
  };

  it("renderiza colunas dinâmicas conforme resolved.table.columns", () => {
    render(<TvDataBlockView block={baseBlock} />);
    expect(screen.getByText("Código")).toBeTruthy();
    expect(screen.getByText("Nome")).toBeTruthy();
    expect(screen.getByText("90123456")).toBeTruthy();
    expect(screen.getByText("Produto A")).toBeTruthy();
  });

  it("renderiza gráfico de barras quando displayMode é bar_chart", () => {
    const block: ComunicadoDataBlock = {
      ...baseBlock,
      type: "data_chart",
      dataBinding: { operationId: "get_oee_series", displayMode: "bar_chart" },
      resolved: {
        chart: {
          chartType: "bar",
          points: [
            { label: "Jan", value: 10 },
            { label: "Fev", value: 20 },
          ],
        },
      },
    };
    const { container } = render(<TvDataBlockView block={block} />);
    expect(container.querySelector(".tdp-data-block--chart-bar")).toBeTruthy();
    expect(container.querySelector("rect")).toBeTruthy();
  });
});
