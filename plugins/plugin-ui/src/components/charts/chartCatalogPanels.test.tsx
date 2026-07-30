import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { ChartBar, ChartColumn } from "lucide-react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChartTypeCatalogPanel, DELPI_CHART_TYPE_CATALOG } from "./ChartTypeCatalogPanel";
import { resolveChartCatalogIcon } from "./chartCatalogIcons";
import { TableInsertCatalogPanel } from "./TableInsertCatalogPanel";

afterEach(() => cleanup());

describe("ChartTypeCatalogPanel", () => {
  it("lista todos os tipos do catálogo", () => {
    render(<ChartTypeCatalogPanel onSelect={() => {}} />);
    for (const entry of DELPI_CHART_TYPE_CATALOG) {
      expect(screen.getAllByTitle(entry.label).length).toBeGreaterThan(0);
    }
  });

  it("dispara onSelect com o tipo escolhido", () => {
    const onSelect = vi.fn();
    render(<ChartTypeCatalogPanel onSelect={onSelect} />);
    fireEvent.click(screen.getByTitle("Linhas"));
    expect(onSelect).toHaveBeenCalledWith("line");
  });

  it("Barras usa ícone horizontal (ChartBar), distinto de Colunas", () => {
    const bars = DELPI_CHART_TYPE_CATALOG.find((entry) => entry.type === "horizontal_bar");
    const columns = DELPI_CHART_TYPE_CATALOG.find((entry) => entry.type === "bar");
    expect(bars?.icon).toBe("ChartBar");
    expect(columns?.icon).toBe("ChartColumn");
    expect(resolveChartCatalogIcon(bars?.icon)).toBe(ChartBar);
    expect(resolveChartCatalogIcon(columns?.icon)).toBe(ChartColumn);
  });
});

describe("TableInsertCatalogPanel", () => {
  it("dispara onSelect com linhas e colunas da grade", () => {
    const onSelect = vi.fn();
    render(<TableInsertCatalogPanel onSelect={onSelect} />);
    fireEvent.click(screen.getByLabelText("3 colunas por 2 linhas"));
    expect(onSelect).toHaveBeenCalledWith({ rows: 2, cols: 3, preset: "grid" });
  });

  it("dispara preset minimalista", () => {
    const onSelect = vi.fn();
    render(<TableInsertCatalogPanel onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Minimalista"));
    expect(onSelect).toHaveBeenCalledWith({ rows: 4, cols: 3, preset: "minimal" });
  });
});
