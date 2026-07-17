import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

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

  it("aplica quebra automática e colgroup quando há larguras", () => {
    const { container } = render(
      <ConfigurablePresentationTable
        columns={[
          { key: "name", label: "Produto", widthPct: 60 },
          { key: "value", label: "Valor", widthPct: 40 },
        ]}
        rows={[{ name: "Texto longo para quebrar na célula", value: 100 }]}
        options={{ wrapText: false, rowHeightPx: 32 }}
      />,
    );
    const root = container.querySelector(".delpi-ui-config-table");
    expect(root?.className).toMatch(/--wrap/);
    expect(root?.className).toMatch(/--fixed-cols/);
    expect(container.querySelectorAll("col")).toHaveLength(2);
    expect((container.querySelector("col") as HTMLElement | null)?.style.width).toBe("60%");
  });

  it("exibe alças na coluna selecionada e emite largura ao arrastar", () => {
    const onColumnResize = vi.fn();
    const { container } = render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        interaction={{
          selectedPart: { kind: "headerCell", colIndex: 0 },
          onColumnResize,
        }}
      />,
    );
    const table = screen.getByRole("table");
    const header = screen.getByRole("columnheader", { name: "Produto" });
    const handle = container.querySelector(
      '[data-column-resize-handle="top"]',
    ) as HTMLElement | null;
    expect(handle).toBeTruthy();
    expect(container.querySelectorAll("[data-column-resize-handle]")).toHaveLength(2);
    expect(container.querySelectorAll(".delpi-ui-config-table__column--selected")).toHaveLength(1);

    table.getBoundingClientRect = () => ({ width: 400 }) as DOMRect;
    header.getBoundingClientRect = () => ({ width: 100 }) as DOMRect;
    fireEvent.pointerDown(handle!, { clientX: 100, pointerId: 1 });
    fireEvent.pointerMove(handle!, { clientX: 140, pointerId: 1 });

    expect(onColumnResize).toHaveBeenLastCalledWith("name", 35);
  });

  it("destaca todas as colunas da multi-seleção", () => {
    const { container } = render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        interaction={{
          selectedPart: { kind: "headerCell", colIndex: 1 },
          selectedParts: [
            { kind: "headerCell", colIndex: 0 },
            { kind: "headerCell", colIndex: 1 },
          ],
          onColumnResize: vi.fn(),
        }}
      />,
    );
    expect(container.querySelectorAll(".delpi-ui-config-table__column--selected")).toHaveLength(2);
    const selectedHeaders = container.querySelectorAll('th[aria-selected="true"]');
    expect(selectedHeaders).toHaveLength(2);
    expect(container.querySelectorAll("[data-column-resize-handle]")).toHaveLength(4);
  });

  it("duplo clique na alça ajusta a largura ao conteúdo", () => {
    const onColumnResize = vi.fn();
    const { container } = render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        interaction={{
          selectedPart: { kind: "headerCell", colIndex: 0 },
          onColumnResize,
        }}
      />,
    );
    const table = screen.getByRole("table");
    const frame = table.parentElement as HTMLElement;
    const header = screen.getByRole("columnheader", { name: "Produto" });
    const handle = container.querySelector(
      '[data-column-resize-handle="top"]',
    ) as HTMLElement;

    frame.getBoundingClientRect = () => ({ width: 400 }) as DOMRect;
    header.getBoundingClientRect = () => ({ width: 120 }) as DOMRect;
    fireEvent.doubleClick(handle);

    expect(onColumnResize).toHaveBeenCalledWith("name", 30);
  });

  it("solicita a próxima página ao chegar ao fim do scroll", () => {
    const onLoadMoreRows = vi.fn();
    const { container } = render(
      <ConfigurablePresentationTable
        columns={columns}
        rows={[{ name: "Item A", value: 100 }]}
        interaction={{ hasMoreRows: true, onLoadMoreRows }}
      />,
    );
    const frame = container.querySelector(
      ".delpi-ui-config-table__frame",
    ) as HTMLDivElement;
    Object.defineProperties(frame, {
      scrollHeight: { value: 500, configurable: true },
      clientHeight: { value: 200, configurable: true },
      scrollTop: { value: 270, writable: true, configurable: true },
    });
    fireEvent.scroll(frame);
    expect(onLoadMoreRows).toHaveBeenCalledTimes(1);
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
