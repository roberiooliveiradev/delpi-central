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
  });
});
