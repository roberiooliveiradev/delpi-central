import {
  CompactPagination,
  compactPaginationBemClasses,
  dataTableBemClasses,
  dataTableSectionBemClasses,
} from "@delpi/plugin-ui/index";

const PREFIX = "pr";

export const TABLE_SECTION = dataTableSectionBemClasses(PREFIX);
export const TABLE = dataTableBemClasses(PREFIX);

export const TABLE_LABELS = {
  emptyMessage: "Nenhuma solicitação nesta página.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

export const PAGINATION_CLASS_NAMES = compactPaginationBemClasses(PREFIX, {
  ghostBtn: "pr-btn pr-btn--secondary",
});

export const PAGINATION_LABELS = {
  info: ({
    page,
    totalPages,
    total,
  }: {
    page: number;
    totalPages: number;
    total: number;
    pageSize: number;
  }) => `Página ${page} / ${totalPages} · ${total} solicitações`,
  previous: "Anterior",
  next: "Próxima",
  navigationAriaLabel: "Paginação das solicitações",
};

export const CompactPaginationControl = CompactPagination;
