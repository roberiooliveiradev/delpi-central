import { useMemo, useState } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import {
  CompactPagination,
  compactPaginationBemClasses,
  ConfigurablePresentationTable,
  ConfigurableTable,
  ConfigurableTableClassesProvider,
  createDashboardPaginationKit,
  DataRouteCatalogPanel,
  DataTable,
  dataTableBemClasses,
  DataTableSection,
  dataTableSectionBemClasses,
  Pagination,
  paginationBemClasses,
  TABLE_PAGE_SIZE_OPTIONS,
  TableHeaderCell,
  TableHeaderContent,
  tableHeaderCellBemClasses,
  tableHeaderContentBemClasses,
  TablePageSizeSelect,
  TablePaginationNav,
  tablePaginationNavBemClasses,
  type DataTableColumn,
} from "../../components/data";
import { createDashboardLoadingActivityCard } from "../../components/feedback";
import type { CatalogEntry } from "../types";

type RequestProgress = { completed: number; total: number };

type DemoRow = { codigo: string; descricao: string; qtd: number };

const MOCK_ROWS: DemoRow[] = [
  { codigo: "A-100", descricao: "Componente Alfa", qtd: 12 },
  { codigo: "B-200", descricao: "Componente Beta", qtd: 4 },
  { codigo: "C-300", descricao: "Componente Gama", qtd: 27 },
  { codigo: "D-400", descricao: "Componente Delta", qtd: 9 },
  { codigo: "E-500", descricao: "Componente Épsilon", qtd: 15 },
];

const tableCn = dataTableBemClasses(PUC_PREFIX);
const sectionCn = dataTableSectionBemClasses(PUC_PREFIX);
const paginationKit = paginationBemClasses(PUC_PREFIX);
const compactCn = compactPaginationBemClasses(PUC_PREFIX, { ghostBtn: "puc-ghost-btn" });
const navCn = tablePaginationNavBemClasses(PUC_PREFIX);
const headerCellCn = tableHeaderCellBemClasses(PUC_PREFIX);
const headerContentCn = tableHeaderContentBemClasses(PUC_PREFIX);

const TABLE_LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar…",
  searchAriaLabel: "Buscar na tabela",
  searchHelpAriaLabel: "Ajuda: busca",
  recordsCount: (total: number) => `${total} registro(s)`,
  refreshLoadingTitle: "Atualizando…",
  refreshLoadingDescription: "Recarregando dados.",
  initialLoadingTitle: "Carregando tabela…",
  initialLoadingDescription: "Aguarde.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const PAGINATION_LABELS = {
  navigationAriaLabel: "Paginação",
  pagesAriaLabel: "Páginas",
  previous: "Anterior",
  next: "Próxima",
  info: ({ rangeStart, rangeEnd, total }: { rangeStart: number; rangeEnd: number; total: number }) =>
    `${rangeStart}–${rangeEnd} de ${total}`,
  jumpLabel: "Ir para",
  jumpInputAriaLabel: "Número da página",
  jumpError: (reason: string, totalPages: number) =>
    reason === "above_max" || reason === "below_min"
      ? `Informe 1–${totalPages}`
      : "Página inválida",
};

const COLUMNS: DataTableColumn<DemoRow>[] = [
  {
    key: "codigo",
    header: "Código",
    headerHint: "Identificador do item",
    sortable: true,
    sortValue: (row) => row.codigo,
    render: (row) => row.codigo,
  },
  {
    key: "descricao",
    header: "Descrição",
    sortable: true,
    sortValue: (row) => row.descricao,
    render: (row) => row.descricao,
  },
  {
    key: "qtd",
    header: "Qtd.",
    align: "right",
    sortable: true,
    sortValue: (row) => row.qtd,
    render: (row) => row.qtd,
  },
];

const LoadingActivity = createDashboardLoadingActivityCard({
  prefix: PUC_PREFIX,
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Progresso, faltam ${n}%`,
    progressAriaIndeterminate: "Carregando",
  },
});

const pageKit = createDashboardPaginationKit({
  prefix: PUC_PREFIX,
  labels: PAGINATION_LABELS,
  tablePageSizeLabels: {
    label: "Por página",
    selectAriaLabel: "Itens por página",
  },
  hints: {},
});

function useLoadingProgress(_active: boolean, _req: RequestProgress) {
  return 0;
}

function useTrackedSingleFetchProgress(_active: boolean): RequestProgress {
  return { completed: 0, total: 1 };
}

export const dataCatalogEntries: CatalogEntry[] = [
  {
    id: "data.DataTable",
    family: "data",
    exportName: "DataTable",
    title: "DataTable",
    description: "Tabela de listagem dos dashboards (LMPS, production, etc.) — sort, empty, row click.",
    docAnchor: "datatable",
    propsSummary: ["columns", "rows", "rowKey", "onSortChange", "onRowClick"],
    demos: [
      {
        id: "default",
        label: "Estilo dashboard",
        render: () => <DataTableDemo />,
      },
    ],
  },
  {
    id: "data.DataTableSection",
    family: "data",
    exportName: "DataTableSection",
    title: "DataTableSection",
    description: "Shell com título, busca, paginação e DataTable — padrão listagem operacional.",
    docAnchor: "datatablesection",
    propsSummary: ["title", "columns", "rows", "search", "Pagination"],
    demos: [
      {
        id: "default",
        label: "Com busca",
        render: () => <DataTableSectionDemo />,
      },
    ],
  },
  {
    id: "data.Pagination",
    family: "data",
    exportName: "Pagination",
    title: "Pagination",
    description: "Rodapé de tabela com páginas e salto.",
    propsSummary: ["page", "pageSize", "total", "onPageChange"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <PaginationDemo />,
      },
    ],
  },
  {
    id: "data.CompactPagination",
    family: "data",
    exportName: "CompactPagination",
    title: "CompactPagination",
    description: "Paginação compacta usada no LMPS (info + anterior/próxima + page size).",
    propsSummary: ["page", "pageSize", "total", "layout"],
    demos: [
      {
        id: "default",
        label: "Grouped",
        render: () => <CompactPaginationDemo />,
      },
    ],
  },
  {
    id: "data.TablePaginationNav",
    family: "data",
    exportName: "TablePaginationNav",
    title: "TablePaginationNav",
    description: "Navegação simples anterior / página atual / próxima.",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <TablePaginationNavDemo />,
      },
    ],
  },
  {
    id: "data.TablePageSizeSelect",
    family: "data",
    exportName: "TablePageSizeSelect",
    title: "TablePageSizeSelect",
    description: "Seletor de itens por página.",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <TablePageSizeSelectDemo />,
      },
    ],
  },
  {
    id: "data.TableHeaderCell",
    family: "data",
    exportName: "TableHeaderCell",
    title: "TableHeaderCell",
    description: "Célula de cabeçalho com hint (FieldLabel ou ícone).",
    demos: [
      {
        id: "default",
        label: "Com hint",
        render: () => (
          <table className="puc-table">
            <thead>
              <tr>
                <TableHeaderCell
                  label="Código"
                  hint="Identificador único"
                  classNames={headerCellCn}
                  labels={{ hintAriaLabel: (l) => `Ajuda: ${l}` }}
                />
              </tr>
            </thead>
          </table>
        ),
      },
    ],
  },
  {
    id: "data.TableHeaderContent",
    family: "data",
    exportName: "TableHeaderContent",
    title: "TableHeaderContent",
    description: "Conteúdo de cabeçalho (label + ajuda) para th customizado.",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <TableHeaderContent
            label="Descrição"
            hint="Texto livre"
            classNames={headerContentCn}
            labels={{ hintAriaLabel: (l) => `Ajuda: ${l}` }}
          />
        ),
      },
    ],
  },
  {
    id: "data.ConfigurablePresentationTable",
    family: "data",
    exportName: "ConfigurablePresentationTable",
    title: "ConfigurablePresentationTable",
    description: "Tabela configurável (TV/deck) — schema-driven.",
    demos: [
      {
        id: "default",
        label: "Grid",
        render: () => (
          <ConfigurableTableClassesProvider prefix="delpi-ui-config-table">
            <ConfigurablePresentationTable
              preset="grid"
              options={{ title: "Itens de exemplo" }}
              columns={[
                { key: "codigo", label: "Código" },
                { key: "descricao", label: "Descrição" },
                { key: "qtd", label: "Qtd." },
              ]}
              rows={MOCK_ROWS.slice(0, 3) as unknown as Array<Record<string, unknown>>}
            />
          </ConfigurableTableClassesProvider>
        ),
      },
    ],
  },
  {
    id: "data.ConfigurableTable",
    family: "data",
    exportName: "ConfigurableTable",
    title: "ConfigurableTable",
    description: "Alias de ConfigurablePresentationTable.",
    demos: [
      {
        id: "default",
        label: "Alias",
        render: () => (
          <ConfigurableTableClassesProvider prefix="delpi-ui-config-table">
            <ConfigurableTable
              preset="grid"
              columns={[
                { key: "codigo", label: "Código" },
                { key: "descricao", label: "Descrição" },
              ]}
              rows={[
                { codigo: "X-1", descricao: "Linha alias" },
              ]}
            />
          </ConfigurableTableClassesProvider>
        ),
      },
    ],
  },
  {
    id: "data.DataRouteCatalogPanel",
    family: "data",
    exportName: "DataRouteCatalogPanel",
    title: "DataRouteCatalogPanel",
    description: "Painel de catálogo de rotas de dados (TV / editor).",
    demos: [
      {
        id: "default",
        label: "Lista",
        render: () => (
          <DataRouteCatalogPanel
            items={[
              {
                id: "kpi",
                label: "KPI operacional",
                category: "production",
                displayKinds: ["kpi"],
              },
              {
                id: "table",
                label: "Listagem",
                category: "production",
                displayKinds: ["table"],
              },
              {
                id: "chart",
                label: "Série temporal",
                category: "commercial",
                displayKinds: ["series"],
              },
            ]}
            onSelect={() => undefined}
          />
        ),
      },
    ],
  },
];

function DataTableDemo() {
  const [sortKey, setSortKey] = useState<string | null>("codigo");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const rows = useMemo(() => {
    const sorted = [...MOCK_ROWS];
    if (!sortKey) return sorted;
    const col = COLUMNS.find((c) => c.key === sortKey);
    if (!col?.sortValue) return sorted;
    sorted.sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      const cmp = String(av).localeCompare(String(bv), "pt-BR", { numeric: true });
      return sortDirection === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [sortKey, sortDirection]);

  return (
    <DataTable
      columns={COLUMNS}
      rows={rows}
      rowKey={(row) => row.codigo}
      layout="section"
      sortKey={sortKey}
      sortDirection={sortDirection}
      onSortChange={(key) => {
        if (sortKey === key) {
          setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
        } else {
          setSortKey(key);
          setSortDirection("asc");
        }
      }}
      classNames={tableCn}
      labels={TABLE_LABELS}
    />
  );
}

function DataTableSectionDemo() {
  return (
    <DataTableSection
      title="Itens (estilo dashboard)"
      titleHint="Listagem com busca e paginação client-side"
      columns={COLUMNS}
      rows={MOCK_ROWS}
      rowKey={(row) => row.codigo}
      defaultPageSize={3}
      tablePageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
      sectionClassNames={sectionCn}
      tableClassNames={tableCn}
      labels={TABLE_LABELS}
      LoadingActivityCard={LoadingActivity}
      Pagination={pageKit.Pagination}
      TablePageSizeSelect={pageKit.TablePageSizeSelect}
      useLoadingProgress={useLoadingProgress}
      useTrackedSingleFetchProgress={useTrackedSingleFetchProgress}
    />
  );
}

function PaginationDemo() {
  const [page, setPage] = useState(1);
  return (
    <Pagination
      page={page}
      pageSize={10}
      total={47}
      onPageChange={setPage}
      classNames={paginationKit.pagination}
      labels={PAGINATION_LABELS}
    />
  );
}

function CompactPaginationDemo() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  return (
    <CompactPagination
      page={page}
      pageSize={pageSize}
      total={47}
      onPageChange={setPage}
      onPageSizeChange={setPageSize}
      pageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
      classNames={compactCn}
      labels={{
        info: ({ page: p, totalPages, total }) => `Pág. ${p}/${totalPages} · ${total} itens`,
        pageSizeLabel: "Por página",
        previous: "Anterior",
        next: "Próxima",
        navigationAriaLabel: "Paginação compacta",
      }}
    />
  );
}

function TablePaginationNavDemo() {
  const [page, setPage] = useState(2);
  return (
    <TablePaginationNav
      page={page}
      pageSize={10}
      total={47}
      onPageChange={setPage}
      classNames={navCn}
      labels={{
        previous: "Anterior",
        next: "Próxima",
        navigationAriaLabel: "Navegação",
        infoBeforeCurrent: "Página",
        infoAfterCurrent: (totalPages) => `de ${totalPages}`,
      }}
    />
  );
}

function TablePageSizeSelectDemo() {
  const [pageSize, setPageSize] = useState(20);
  return (
    <TablePageSizeSelect
      pageSize={pageSize}
      onPageSizeChange={setPageSize}
      pageSizeOptions={TABLE_PAGE_SIZE_OPTIONS}
      classNames={paginationKit.tablePageSize}
      labels={{ label: "Por página", selectAriaLabel: "Itens por página"       }}
    />
  );
}
