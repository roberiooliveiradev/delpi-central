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

  it("usa ConfigurableTable banded por padrão em data_table", () => {
    const { container } = render(<TvDataBlockView block={baseBlock} />);
    expect(container.querySelector(".tdp-configurable-table")).toBeTruthy();
    expect(container.querySelector(".tdp-configurable-table--banded")).toBeTruthy();
  });

  it("respeita tableOptions do bloco (header Delpi)", () => {
    const { container } = render(
      <TvDataBlockView
        block={{
          ...baseBlock,
          tablePreset: "banded",
          tableOptions: {
            headerBg: "#003866",
            headerTextColor: "#ffffff",
            cellBg: "#ffffff",
            cellTextColor: "#0f172a",
            showBorders: true,
            zebraStripe: true,
          },
        }}
      />,
    );
    const table = container.querySelector(".tdp-configurable-table") as HTMLElement | null;
    expect(table).toBeTruthy();
    expect(table?.style.getPropertyValue("--tdp-table-header-bg").trim() || table?.getAttribute("style")).toBeTruthy();
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
