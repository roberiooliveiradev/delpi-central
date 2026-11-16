/**
 * Binding do kit DataTable do Plugin UI para Minhas Solicitações —
 * mesma mecânica dos demais MFEs (`createDashboardDataTableKit`
 * + `createDashboardPaginationKit` + `createDashboardLoadingActivityCard`),
 * com labels/hints do domínio. Fonte única de DataTable/DataTableSection.
 */

import {
  createDashboardDataTableKit,
  createDashboardLoadingActivityCard,
  createDashboardPaginationKit,
} from "@delpi/plugin-ui/index";

import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";

const MR_TABLE_PREFIX = "my-requests";

export const MY_REQUESTS_TABLE_PAGE_SIZE_OPTIONS = [10, 20, 50] as const;

const paginationKit = createDashboardPaginationKit({
  prefix: MR_TABLE_PREFIX,
  labels: {
    navigationAriaLabel: "Paginação da lista",
    pagesAriaLabel: "Páginas",
    previous: "Página anterior",
    next: "Próxima página",
    info: ({ rangeStart, rangeEnd, total, page, totalPages }) =>
      `${rangeStart}–${rangeEnd} de ${total} · página ${page} de ${totalPages}`,
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Número da página",
    jumpError: (_reason, totalPages) =>
      `Informe uma página entre 1 e ${totalPages}.`,
  },
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Itens por página",
  },
  /* UX V3: sem ícones "?" na paginação — os labels/aria dos próprios
   * controles já carregam a ajuda essencial (AC06). */
});

export const MyRequestsPagination = paginationKit.Pagination;
export const MyRequestsTablePageSizeSelect = paginationKit.TablePageSizeSelect;

const MyRequestsLoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: MR_TABLE_PREFIX,
  labels: {
    progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
    progressAriaDeterminate: (remainingPercent: number) =>
      `Carregando: faltam ${remainingPercent}%`,
    progressAriaIndeterminate: "Carregando…",
  },
});

const dataTableKit = createDashboardDataTableKit({
  prefix: MR_TABLE_PREFIX,
  labels: {
    emptyMessage: "Nenhum registro encontrado.",
    loadingMessage: "Carregando…",
    sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
    headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
    searchPlaceholder: "Buscar na lista…",
    searchAriaLabel: "Filtrar registros da lista",
    searchHelpAriaLabel: "Ajuda: busca na lista",
    recordsCount: (total: number) => `${total} registro(s)`,
    refreshLoadingTitle: "Atualizando lista",
    refreshLoadingDescription:
      "Mantendo os dados visíveis enquanto a nova consulta é aplicada.",
    initialLoadingTitle: "Carregando registros",
    initialLoadingDescription:
      "Aguarde enquanto os dados da lista são obtidos.",
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
  LoadingActivityCard: MyRequestsLoadingActivityCard,
  Pagination: MyRequestsPagination,
  TablePageSizeSelect: MyRequestsTablePageSizeSelect,
  tablePageSizeOptions: MY_REQUESTS_TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 20,
});

export const MyRequestsDataTable = dataTableKit.DataTable;
export const MyRequestsDataTableSection = dataTableKit.DataTableSection;
