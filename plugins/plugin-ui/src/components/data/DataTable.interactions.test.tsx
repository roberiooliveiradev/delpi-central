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

    const headerA = document.querySelector('th[data-column-key="a"]') as HTMLElement;
    const headerB = document.querySelector('th[data-column-key="b"]') as HTMLElement;
    expect(headerA && headerB).toBeTruthy();
    headerA.getBoundingClientRect = () =>
      ({
        left: 0,
        width: 100,
        top: 0,
        height: 32,
        right: 100,
        bottom: 32,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }) as DOMRect;

    fireEvent.pointerDown(headerB, { button: 0 });
    expect(headerB.className).toContain("delpi-ui-table__column--dragging");
    expect(
      document.querySelector('td[data-column-key="b"]')?.className,
    ).toContain("delpi-ui-table__column--dragging");

    fireEvent.dragStart(headerB, {
      dataTransfer: {
        effectAllowed: "move",
        setData: vi.fn(),
        getData: () => "b",
        setDragImage: vi.fn(),
      },
    });
    expect(document.querySelector(".delpi-ui-table__column-drag-ghost")).toBeNull();
    fireEvent.dragOver(headerA, {
      clientX: 20,
      dataTransfer: { dropEffect: "move" },
    });
    fireEvent.drop(headerA, {
      clientX: 20,
      dataTransfer: { getData: () => "b" },
    });
    expect(onColumnOrderChange).toHaveBeenCalledWith(["b", "a"]);
  });
});

describe("DataTable row click × interactive", () => {
  it("interactive padrão impede onRowClick (stop)", () => {
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={[
          {
            key: "nome",
            header: "Cliente",
            interactive: true,
            render: (row: { nome: string }) => row.nome,
          },
        ]}
        rows={[{ nome: "Acme" }]}
        rowKey={(_, index) => String(index)}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        onRowClick={onRowClick}
        rowClickRole="button"
      />,
    );

    fireEvent.click(screen.getByRole("cell", { name: "Acme" }));
    expect(onRowClick).not.toHaveBeenCalled();
  });

  it("rowClick propagate permite onRowClick mesmo com interactive", () => {
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={[
          {
            key: "nome",
            header: "Cliente",
            interactive: true,
            rowClick: "propagate",
            render: (row: { nome: string }) => row.nome,
          },
        ]}
        rows={[{ nome: "Acme" }]}
        rowKey={(_, index) => String(index)}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        onRowClick={onRowClick}
        rowClickRole="button"
      />,
    );

    fireEvent.click(screen.getByRole("cell", { name: "Acme" }));
    expect(onRowClick).toHaveBeenCalledTimes(1);
  });

  it("célula sem interactive dispara onRowClick", () => {
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={[
          {
            key: "nome",
            header: "Cliente",
            render: (row: { nome: string }) => row.nome,
          },
        ]}
        rows={[{ nome: "Acme" }]}
        rowKey={(_, index) => String(index)}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        onRowClick={onRowClick}
        rowClickRole="button"
      />,
    );

    fireEvent.click(screen.getByRole("cell", { name: "Acme" }));
    expect(onRowClick).toHaveBeenCalledTimes(1);
  });

  it("renderiza linha de detalhe quando expandedRowKey bate com rowKey", () => {
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={[
          {
            key: "nome",
            header: "Cliente",
            render: (row: { id: string; nome: string }) => row.nome,
          },
        ]}
        rows={[
          { id: "a", nome: "Acme" },
          { id: "b", nome: "Beta" },
        ]}
        rowKey={(row) => row.id}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        onRowClick={onRowClick}
        expandedRowKey="a"
        renderExpandedRow={(row) => <div data-testid="detail">{`detalhe-${row.id}`}</div>}
      />,
    );

    expect(screen.getByTestId("detail").textContent).toBe("detalhe-a");
    expect(document.querySelector(".delpi-ui-table__row--expanded")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-table__detail-row")).toBeTruthy();
    expect(screen.queryByText("detalhe-b")).toBeNull();
  });

  it("isRowExpandable=false omite detalhe mesmo com expandedRowKey", () => {
    render(
      <DataTable
        columns={[
          {
            key: "nome",
            header: "Cliente",
            render: (row: { id: string; nome: string }) => row.nome,
          },
        ]}
        rows={[{ id: "a", nome: "Acme" }]}
        rowKey={(row) => row.id}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        expandedRowKey="a"
        isRowExpandable={() => false}
        renderExpandedRow={() => <div data-testid="detail">x</div>}
      />,
    );

    expect(screen.queryByTestId("detail")).toBeNull();
  });

  it("clique no conteúdo expandido não dispara onRowClick", () => {
    const onRowClick = vi.fn();
    render(
      <DataTable
        columns={[
          {
            key: "nome",
            header: "Cliente",
            render: (row: { id: string; nome: string }) => row.nome,
          },
        ]}
        rows={[{ id: "a", nome: "Acme" }]}
        rowKey={(row) => row.id}
        classNames={dataTableBemClasses("teste")}
        labels={labels}
        onRowClick={onRowClick}
        expandedRowKey="a"
        renderExpandedRow={() => <button type="button">Dentro</button>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Dentro" }));
    expect(onRowClick).not.toHaveBeenCalled();
  });
});
