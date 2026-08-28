import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataTableSection, dataTableSectionBemClasses } from "./DataTableSection";
import { dataTableBemClasses } from "./DataTable";
import { TABLE_PAGE_SIZE_OPTIONS } from "../../utils/paginationPages";

const sectionCn = dataTableSectionBemClasses("test");
const tableCn = dataTableBemClasses("test");

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar…",
  searchAriaLabel: "Buscar",
  searchHelpAriaLabel: "Ajuda",
  recordsCount: (total: number) => `${total} registro(s)`,
  refreshLoadingTitle: "Atualizando",
  refreshLoadingDescription: "…",
  initialLoadingTitle: "Carregando",
  initialLoadingDescription: "…",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

function LoadingActivityCard() {
  return <div data-testid="loading" />;
}

function PaginationStub() {
  return <div data-testid="pagination" />;
}

function TablePageSizeSelectStub() {
  return <div data-testid="page-size" />;
}

const noopProgress = () => 0;
const noopTracked = () => ({ completed: 0, total: 0 });

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe("DataTableSection columnPreferencesKey", () => {
  it("exibe menu Colunas e oculta coluna ao desmarcar", () => {
    const onVisible = vi.fn();
    render(
      <DataTableSection
        title="Itens"
        columnPreferencesKey="test:datatable-section:v1"
        onVisibleColumnKeysChange={onVisible}
        columns={[
          { key: "codigo", header: "Código", render: (row: { codigo: string }) => row.codigo },
          { key: "nome", header: "Nome", render: (row: { nome: string }) => row.nome },
        ]}
        rows={[
          { codigo: "A1", nome: "Alfa" },
          { codigo: "B2", nome: "Beta" },
        ]}
        rowKey={(row) => row.codigo}
        hideSearch
        sectionClassNames={sectionCn}
        tableClassNames={tableCn}
        labels={LABELS}
        tablePageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
        LoadingActivityCard={LoadingActivityCard}
        Pagination={PaginationStub}
        TablePageSizeSelect={TablePageSizeSelectStub}
        useLoadingProgress={noopProgress}
        useTrackedSingleFetchProgress={noopTracked}
      />,
    );

    expect(screen.getByRole("columnheader", { name: /Código/i })).toBeTruthy();
    expect(screen.getByRole("columnheader", { name: /Nome/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Colunas" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Colunas" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Exibir coluna Nome" }));

    expect(screen.queryByRole("columnheader", { name: /Nome/i })).toBeNull();
    expect(screen.getByRole("columnheader", { name: /Código/i })).toBeTruthy();
    expect(onVisible).toHaveBeenCalled();
    const lastKeys = onVisible.mock.calls.at(-1)?.[0] as string[];
    expect(lastKeys).toEqual(["codigo"]);
  });

  it("sem columnPreferencesKey não mostra menu Colunas", () => {
    render(
      <DataTableSection
        title="Itens"
        columns={[
          { key: "codigo", header: "Código", render: (row: { codigo: string }) => row.codigo },
        ]}
        rows={[{ codigo: "A1" }]}
        rowKey={(row) => row.codigo}
        hideSearch
        hidePageSizeSelect
        sectionClassNames={sectionCn}
        tableClassNames={tableCn}
        labels={LABELS}
        tablePageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
        LoadingActivityCard={LoadingActivityCard}
        Pagination={PaginationStub}
        TablePageSizeSelect={TablePageSizeSelectStub}
        useLoadingProgress={noopProgress}
        useTrackedSingleFetchProgress={noopTracked}
      />,
    );

    expect(screen.queryByRole("button", { name: "Colunas" })).toBeNull();
  });
});

describe("DataTableSection chrome nativo (fonte / cards / excel)", () => {
  it("liga Fonte, Excel e Tabela/Cards quando as props opt-in estão definidas", async () => {
    const onExport = vi.fn();
    render(
      <DataTableSection
        title="Itens"
        columnPreferencesKey="test:chrome:columns:v1"
        fontSizePreferencesKey="test:chrome:font:v1"
        viewLayoutPreferencesKey="test:chrome:layout:v1"
        excelExport={{ onExport }}
        uiPrefix="test"
        renderCard={(row: { codigo: string }) => <div>Card {row.codigo}</div>}
        columns={[
          { key: "codigo", header: "Código", render: (row: { codigo: string }) => row.codigo },
        ]}
        rows={[{ codigo: "A1" }]}
        rowKey={(row) => row.codigo}
        hideSearch
        hidePageSizeSelect
        sectionClassNames={sectionCn}
        tableClassNames={tableCn}
        labels={LABELS}
        tablePageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
        LoadingActivityCard={LoadingActivityCard}
        Pagination={PaginationStub}
        TablePageSizeSelect={TablePageSizeSelectStub}
        useLoadingProgress={noopProgress}
        useTrackedSingleFetchProgress={noopTracked}
      />,
    );

    expect(screen.getByRole("button", { name: "Colunas" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Excel" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Excel" }).className).toContain(
      "delpi-ui-table-toolbar-action",
    );
    expect(screen.getByRole("button", { name: "Colunas" }).className).toContain(
      "delpi-ui-table-toolbar-action",
    );
    expect(screen.getByText("Fonte")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tabela" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cards" })).toBeTruthy();
    expect(screen.getByRole("columnheader", { name: /Código/i })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Cards" }));
    expect(screen.getByText("Card A1")).toBeTruthy();
    expect(screen.queryByRole("columnheader", { name: /Código/i })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Excel" }));
    expect(onExport).toHaveBeenCalledTimes(1);
  });

  it("sem props opt-in não mostra chrome operacional", () => {
    render(
      <DataTableSection
        title="Itens"
        columns={[
          { key: "codigo", header: "Código", render: (row: { codigo: string }) => row.codigo },
        ]}
        rows={[{ codigo: "A1" }]}
        rowKey={(row) => row.codigo}
        hideSearch
        hidePageSizeSelect
        sectionClassNames={sectionCn}
        tableClassNames={tableCn}
        labels={LABELS}
        tablePageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
        LoadingActivityCard={LoadingActivityCard}
        Pagination={PaginationStub}
        TablePageSizeSelect={TablePageSizeSelectStub}
        useLoadingProgress={noopProgress}
        useTrackedSingleFetchProgress={noopTracked}
      />,
    );

    expect(screen.queryByRole("button", { name: "Excel" })).toBeNull();
    expect(screen.queryByText("Fonte")).toBeNull();
    expect(screen.queryByRole("button", { name: "Cards" })).toBeNull();
  });
});
