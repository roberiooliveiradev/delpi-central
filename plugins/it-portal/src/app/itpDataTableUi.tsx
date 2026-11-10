/** Kit DataTable do Portal de TI — fábricas `@delpi/plugin-ui`, prefixo `itp`. */
import {
  createDashboardDataTableKit,
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type DashboardDataTableSectionProps,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import { ItpLoadingCard, UI_PREFIX } from "./itPortalUi";
import { useLoadingProgress, useTrackedSingleFetchProgress } from "./loadingProgress";

const paginationKit = createDashboardPaginationKit({
  prefix: UI_PREFIX,
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
          return "Informe o número da página.";
        case "invalid":
          return "Use apenas números.";
        case "below_min":
          return "A primeira página é 1.";
        case "above_max":
          return `A página máxima é ${totalPages}.`;
        default:
          return "";
      }
    },
  },
});

const kit = createDashboardDataTableKit({
  prefix: UI_PREFIX,
  labels: {
    emptyMessage: "Nenhum registro encontrado.",
    loadingMessage: "Carregando…",
    sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
    headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
    searchPlaceholder: "Buscar…",
    searchAriaLabel: "Buscar registros",
    searchHelpAriaLabel: "Ajuda: busca",
    recordsCount: (total: number) =>
      `${total.toLocaleString("pt-BR")} ${total === 1 ? "registro" : "registros"}`,
    refreshLoadingTitle: "Atualizando",
    refreshLoadingDescription: "Mantendo os dados visíveis enquanto a consulta é aplicada.",
    initialLoadingTitle: "Carregando registros",
    initialLoadingDescription: "Aguarde enquanto os dados são obtidos.",
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
  LoadingActivityCard: ItpLoadingCard,
  Pagination: paginationKit.Pagination,
  TablePageSizeSelect: paginationKit.TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 20,
});

const KitDataTableSection = kit.DataTableSection;

export function DataTableSection<T>(props: DashboardDataTableSectionProps<T>) {
  return <KitDataTableSection hidePaginationWhenSinglePage {...props} />;
}

export type { DataTableColumn } from "@delpi/plugin-ui/index";
