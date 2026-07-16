import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ConfigurablePresentationTable } from "./ConfigurablePresentationTable";
import { mergeConfigurableTableOptions } from "./configurableTableOptions";

afterEach(() => {
  cleanup();
});

describe("ConfigurablePresentationTable", () => {
  const columns = [
    { key: "name", label: "Produto" },
    { key: "value", label: "Valor" },
  ];

  it("renderiza cabeçalho e células", () => {
    render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[
          { name: "Item A", value: 1200 },
          { name: "Item B", value: 3400 },
        ]}
      />,
    );
    expect(screen.getByText("Produto")).toBeTruthy();
    expect(screen.getByText("Item A")).toBeTruthy();
    expect(screen.getByRole("table")).toBeTruthy();
  });

  it("renderiza título quando habilitado", () => {
    render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        options={{ showTitle: true, title: "Top produtos" }}
      />,
    );
    expect(screen.getByText("Top produtos")).toBeTruthy();
  });

  it("oculta cabeçalho quando desabilitado", () => {
    render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        options={{ showHeader: false }}
      />,
    );
    expect(screen.queryByRole("columnheader")).toBeNull();
    expect(screen.getByText("Item A")).toBeTruthy();
  });

  it("mostra estado vazio sem linhas", () => {
    render(<ConfigurablePresentationTable columns={columns} rows={[]} />);
    expect(screen.getByText("Sem linhas")).toBeTruthy();
  });

  it("aplica estilo de parte no cabeçalho e na célula", () => {
    render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        options={{ showTitle: true, title: "Topo" }}
        tableParts={{
          title: { visible: true, content: "Topo", style: { color: "#112233" } },
          header: { visible: true, style: { fill: "#abcdef" } },
          "cell:0:0": { style: { fill: "#fedcba" } },
        }}
      />,
    );
    const title = screen.getByText("Topo");
    expect(title.getAttribute("style") ?? "").toMatch(/color:\s*rgb\(17,\s*34,\s*51\)|#112233/i);
    const header = screen.getByText("Produto");
    expect(header.getAttribute("style") ?? "").toMatch(/background|#abcdef/i);
  });

  it("envolve a grade em área com scroll (frame)", () => {
    const { container } = render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
      />,
    );
    const frame = container.querySelector(".delpi-ui-config-table__frame");
    expect(frame).toBeTruthy();
    expect(frame?.querySelector("table")).toBeTruthy();
  });

  it("renderiza linha de totais quando habilitada", () => {
    render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[
          { name: "Item A", value: 100 },
          { name: "Item B", value: 50 },
        ]}
        options={{ showTotalRow: true }}
      />,
    );
    expect(screen.getByText("Total")).toBeTruthy();
    expect(screen.getByText("150")).toBeTruthy();
  });

  it("aplica quebra de texto e colgroup com larguras", () => {
    const { container } = render(
      <ConfigurablePresentationTable
        columns={[
          { key: "name", label: "Produto", widthPct: 60 },
          { key: "value", label: "Valor", widthPct: 40 },
        ]}
        rows={[{ name: "Texto longo para quebrar na célula", value: 100 }]}
        options={{ wrapText: true, rowHeightPx: 32 }}
      />,
    );
    const root = container.querySelector(".delpi-ui-config-table");
    expect(root?.className).toMatch(/--wrap/);
    expect(root?.className).toMatch(/--fixed-cols/);
    expect(container.querySelectorAll("col")).toHaveLength(2);
    expect((container.querySelector("col") as HTMLElement | null)?.style.width).toBe("60%");
  });
});

describe("mergeConfigurableTableOptions", () => {
  it("aplica defaults do preset banded", () => {
    const merged = mergeConfigurableTableOptions(undefined, "banded");
    expect(merged.zebraStripe).toBe(true);
  });

  it("aplica defaults do preset minimal", () => {
    const merged = mergeConfigurableTableOptions(undefined, "minimal");
    expect(merged.showBorders).toBe(false);
  });
});
