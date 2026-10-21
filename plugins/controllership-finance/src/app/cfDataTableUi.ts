/** Kit DataTable do Portal — fábricas `@delpi/plugin-ui`, prefixo `cf`. */
import {
  createDashboardDataTableKit,
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";
import { CF_HELP } from "../content/helpTooltips";
import { CfLoadingCard, UI_PREFIX } from "./controllershipFinanceUi";

const P = CF_HELP.closing.pagination;

const paginationKit = createDashboardPaginationKit({
  prefix: UI_PREFIX,
  hints: {
    pageSize: P.pageSize,
    previous: P.previous,
    next: P.next,
    info: P.info,
    jump: P.jump,
  },
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Quantidade de itens por página",
  },
  labels: {
    navigationAriaLabel: "Paginação da tabela",
    pagesAriaLabel: "Páginas",
    previous: "Anterior",
    next: "Próxima",
    info: ({ rangeStart, rangeEnd, total, page, totalPages }) =>
      `Exibindo ${rangeStart}–${rangeEnd} de ${total} · Página ${page} de ${totalPages}`,
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Ir para página",
    jumpError: (reason: PageJumpValidationReason, totalPages: number) => {
      switch (reason) {
        case "empty":
          return P.jumpEmpty;
        case "invalid":
          return P.jumpInvalid;
        case "below_min":
          return P.jumpBelowMin;
        case "above_max":
          return `A página máxima é ${totalPages}.`;
        default:
          return "";
      }
    },
  },
});

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) =>
    `${total.toLocaleString("pt-BR")} ${total === 1 ? "registro" : "registros"}`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription:
    "Mantendo os dados visíveis enquanto a nova consulta é aplicada.",
  initialLoadingTitle: "Carregando registros",
  initialLoadingDescription: "Aguarde enquanto os dados da tabela são obtidos.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: UI_PREFIX,
  labels: LABELS,
  LoadingActivityCard: CfLoadingCard,
  Pagination: paginationKit.Pagination,
  TablePageSizeSelect: paginationKit.TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 50,
});

export const DataTableSection = kit.DataTableSection;
export { TABLE_PAGE_SIZE_OPTIONS };

export type { DataTableColumn } from "@delpi/plugin-ui/index";
export type {
  DashboardDataTableSectionProps as DataTableSectionProps,
  ServerPaginationConfig,
} from "@delpi/plugin-ui/index";
