import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { BarChartHorizontal, ChartColumn } from "lucide-react";
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

  it("Barras usa BarChartHorizontal, distinto de Colunas", () => {
    const bars = DELPI_CHART_TYPE_CATALOG.find((entry) => entry.type === "horizontal_bar");
    const columns = DELPI_CHART_TYPE_CATALOG.find((entry) => entry.type === "bar");
    expect(bars?.icon).toBe("BarChartHorizontal");
    expect(columns?.icon).toBe("ChartColumn");
    expect(resolveChartCatalogIcon(bars?.icon)).toBe(BarChartHorizontal);
    expect(resolveChartCatalogIcon(columns?.icon)).toBe(ChartColumn);
  });

  it("destaca selectedType no item atual", () => {
    render(<ChartTypeCatalogPanel selectedType="line" onSelect={() => {}} />);
    expect(screen.getByTitle("Linhas").getAttribute("aria-current")).toBe("true");
    expect(screen.getByTitle("Colunas").getAttribute("aria-current")).toBeNull();
  });

  it("filtra por allowedTypes", () => {
    render(
      <ChartTypeCatalogPanel
        allowedTypes={["line", "area", "bar"]}
        onSelect={() => {}}
      />,
    );
    expect(screen.getByTitle("Linhas")).toBeTruthy();
    expect(screen.getByTitle("Área")).toBeTruthy();
    expect(screen.getByTitle("Colunas")).toBeTruthy();
    expect(screen.queryByTitle("Pizza")).toBeNull();
    expect(screen.queryByTitle("Funil")).toBeNull();
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
