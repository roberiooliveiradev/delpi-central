import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TableViewBlockView } from "./tableViewBlockView";
import type { ComunicadoTableViewBlock } from "./comunicadoTypes";

function baseTable(overrides: Partial<ComunicadoTableViewBlock> = {}): ComunicadoTableViewBlock {
  return {
    id: "tbl-1",
    type: "table_view",
    tablePreset: "banded",
    frame: { x: 0, y: 0, w: 40, h: 30 },
    ...overrides,
  };
}

describe("TableViewBlockView empty chrome", () => {
  it("sem resolved mas com tableProjection mostra título/cabeçalho", () => {
    const block = baseTable({
      dataSourceId: "src-1",
      tableOptions: { title: "Carteira semanal", showTitle: true, showHeader: true },
      tableProjection: {
        columns: [
          { key: "branch", label: "Filial", visible: true },
          { key: "forecast_value", label: "Previsto", visible: true },
        ],
      },
    });
    const { container } = render(<TableViewBlockView block={block} />);
    expect(container.querySelector(".tdp-data-block--placeholder")).toBeNull();
    expect(container.querySelector(".tdp-data-block--table")).toBeTruthy();
    expect(screen.getByText("Carteira semanal")).toBeTruthy();
    expect(screen.getByText("Filial")).toBeTruthy();
    expect(screen.getByText("Previsto")).toBeTruthy();
    expect(screen.getByText("Sem linhas")).toBeTruthy();
  });

  it("sem resolved e sem schema cai no placeholder de conexão", () => {
    const block = baseTable({ dataSourceId: undefined });
    render(<TableViewBlockView block={block} interactive />);
    expect(screen.getByText("Conecte uma fonte de dados")).toBeTruthy();
  });
});
