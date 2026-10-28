import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

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

const baseProps = {
  title: "Itens",
  rowKey: (row: { codigo: string; nome: string }) => row.codigo,
  hidePageSizeSelect: true,
  sectionClassNames: sectionCn,
  tableClassNames: tableCn,
  labels: LABELS,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  LoadingActivityCard,
  Pagination: PaginationStub,
  TablePageSizeSelect: TablePageSizeSelectStub,
  useLoadingProgress: noopProgress,
  useTrackedSingleFetchProgress: noopTracked,
};

const columns = [
  { key: "codigo", header: "Código", render: (row: { codigo: string }) => row.codigo },
  { key: "nome", header: "Nome", render: (row: { nome: string }) => row.nome },
];

const rows = [
  { codigo: "A1", nome: "Alfa" },
  { codigo: "B2", nome: "Beta" },
];

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe("DataTableSection toolbarPortalTarget", () => {
  it("renderiza a toolbar no host externo e o estado continua único", () => {
    const host = document.createElement("div");
    host.setAttribute("data-testid", "hero-toolbar");
    document.body.appendChild(host);
    try {
      render(
        <DataTableSection
          {...baseProps}
          columns={columns}
          rows={rows}
          toolbarPortalTarget={host}
          columnPreferencesKey="test:datatable-portal:v1"
        />,
      );

      // Toolbar renderizada DENTRO do host, não na seção.
      const searchInHost = host.querySelector("input[type='search']");
      expect(searchInHost).toBeTruthy();
      expect(host.querySelector("button")).toBeTruthy();
      const sectionEl = document.querySelector(".test-table-section");
      expect(sectionEl?.querySelector("input[type='search']")).toBeNull();

      // A busca no host filtra as linhas reais da tabela.
      fireEvent.change(searchInHost!, { target: { value: "Beta" } });
      expect(screen.queryByRole("cell", { name: "Alfa" })).toBeNull();
      expect(screen.getByRole("cell", { name: "Beta" })).toBeTruthy();
    } finally {
      host.remove();
    }
  });

  it("sem toolbarPortalTarget mantém a toolbar dentro da seção", () => {
    render(
      <DataTableSection {...baseProps} columns={columns} rows={rows} />,
    );
    const sectionEl = document.querySelector(".test-table-section");
    expect(sectionEl?.querySelector("input[type='search']")).toBeTruthy();
  });
});

describe("DataTableSection tableLayout", () => {
  it("tableLayout='scroll' aplica o wrap flexível com header fixo", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={rows}
        tableLayout="scroll"
        hideSearch
      />,
    );
    expect(document.querySelector(".delpi-ui-table-wrap--scroll")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-table-wrap--section")).toBeNull();
  });
});

describe("DataTableSection hidePaginationWhenSinglePage", () => {
  const manyRows = [
    { codigo: "A1", nome: "Alfa" },
    { codigo: "B2", nome: "Beta" },
    { codigo: "C3", nome: "Gama" },
  ];

  it("oculta a paginação com zero registros", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={[]}
        hidePaginationWhenSinglePage
        hideSearch
      />,
    );
    expect(screen.queryByTestId("pagination")).toBeNull();
  });

  it("oculta a paginação quando cabe uma única página", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={rows}
        pageSize={50}
        hidePaginationWhenSinglePage
        hideSearch
      />,
    );
    expect(screen.queryByTestId("pagination")).toBeNull();
  });

  it("oculta a paginação com exatamente uma página cheia", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={rows}
        pageSize={2}
        hidePaginationWhenSinglePage
        hideSearch
      />,
    );
    expect(screen.queryByTestId("pagination")).toBeNull();
  });

  it("exibe a paginação com mais de uma página", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={manyRows}
        pageSize={2}
        hidePaginationWhenSinglePage
        hideSearch
      />,
    );
    expect(screen.getByTestId("pagination")).toBeTruthy();
  });

  it("recalcula após busca reduzir o conjunto a uma página", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={manyRows}
        pageSize={2}
        hidePaginationWhenSinglePage
      />,
    );
    expect(screen.getByTestId("pagination")).toBeTruthy();
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Gama" },
    });
    expect(screen.queryByTestId("pagination")).toBeNull();
    expect(screen.getByRole("cell", { name: "Gama" })).toBeTruthy();
  });

  it("sem a prop mantém a paginação sempre visível (retrocompatível)", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={rows}
        pageSize={50}
        hideSearch
      />,
    );
    expect(screen.getByTestId("pagination")).toBeTruthy();
  });

  it("usa o total autoritativo no modo server-side", () => {
    render(
      <DataTableSection
        {...baseProps}
        columns={columns}
        rows={rows}
        serverPagination={{
          page: 1,
          pageSize: 50,
          total: 120,
          onPageChange: () => {},
        }}
        hidePaginationWhenSinglePage
        hideSearch
      />,
    );
    expect(screen.getByTestId("pagination")).toBeTruthy();
  });
});
