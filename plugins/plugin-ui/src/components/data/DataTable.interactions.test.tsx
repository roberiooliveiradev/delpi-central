import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataTable, dataTableBemClasses } from "./DataTable";

const labels = {
  emptyMessage: "Vazio",
  loadingMessage: "Carregando",
  sortByAriaLabel: (header: string) => `Ordenar ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda ${header}`,
};

afterEach(cleanup);

describe("DataTable grid-preview", () => {
  it("expõe eventos genéricos, seleção, índice e teclado", () => {
    const onHeaderClick = vi.fn();
    const onCellClick = vi.fn();
    const onHeaderContextMenu = vi.fn();
    render(
      <DataTable
        columns={[
          {
            key: "valor",
            header: "Valor",
            headerPrefix: <span data-testid="type-icon">123</span>,
            render: (row: { valor: number }) => row.valor,
          },
        ]}
        rows={[{ valor: 42 }]}
        rowKey={(_, index) => String(index)}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        mode="grid-preview"
        indexColumn={{ ariaLabel: "Linha" }}
        selectedColumnKey="valor"
        onHeaderClick={onHeaderClick}
        onHeaderContextMenu={onHeaderContextMenu}
        onCellClick={onCellClick}
      />,
    );

    const header = screen.getByRole("columnheader", { name: /Valor/ });
    expect(header.getAttribute("aria-selected")).toBe("true");
    expect(screen.getByTestId("type-icon")).toBeTruthy();
    fireEvent.keyDown(header, { key: "Enter" });
    fireEvent.contextMenu(header);
    expect(onHeaderClick).toHaveBeenCalledTimes(1);
    expect(onHeaderContextMenu).toHaveBeenCalledTimes(1);

    const cell = screen.getByRole("cell", { name: "42" });
    expect(cell.getAttribute("aria-selected")).toBe("true");
    fireEvent.keyDown(cell, { key: " " });
    expect(onCellClick).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("cell", { name: "1" })).toBeTruthy();
    expect(document.querySelector(".delpi-ui-table--grid-preview")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-table--wrap")).toBeTruthy();
  });

  it("seleciona célula/linha e expõe resize/reorder", () => {
    const onSelectionChange = vi.fn();
    const onColumnOrderChange = vi.fn();

    render(
      <DataTable
        columns={[
          { key: "a", header: "A", render: (row: { a: string; b: string }) => row.a },
          { key: "b", header: "B", render: (row: { a: string; b: string }) => row.b },
        ]}
        rows={[
          { a: "1", b: "x" },
          { a: "2", b: "y" },
        ]}
        rowKey={(_, index) => String(index)}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        mode="grid-preview"
        wrapText
        resizableColumns
        enableColumnReorder
        indexColumn={{ ariaLabel: "Linha" }}
        selection={null}
        onSelectionChange={onSelectionChange}
        onColumnOrderChange={onColumnOrderChange}
      />,
    );

    fireEvent.click(screen.getByRole("cell", { name: "x" }));
    expect(onSelectionChange).toHaveBeenLastCalledWith({
      kind: "cell",
      cells: [{ rowIndex: 0, columnKey: "b" }],
    });

    const indexCell = document.querySelector(
      "tbody tr:first-child td.delpi-ui-table__index-col",
    );
    expect(indexCell).toBeTruthy();
    fireEvent.click(indexCell!);
    expect(onSelectionChange).toHaveBeenLastCalledWith({
      kind: "row",
      indices: [0],
    });

    expect(document.querySelectorAll("[data-column-resize-handle]")).toHaveLength(2);

    const headerA = document.querySelector('th[data-column-key="a"]');
    const headerB = document.querySelector('th[data-column-key="b"]');
    expect(headerA && headerB).toBeTruthy();
    fireEvent.dragStart(headerB!, {
      dataTransfer: { effectAllowed: "move", setData: vi.fn(), getData: () => "b" },
    });
    fireEvent.drop(headerA!, {
      dataTransfer: { getData: () => "b" },
    });
    expect(onColumnOrderChange).toHaveBeenCalledWith(["b", "a"]);
  });
});
