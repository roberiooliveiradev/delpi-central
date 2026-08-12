import { createDashboardDataTableKit } from "@delpi/plugin-ui/index";

import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";
import { LoadingActivityCard } from "./LoadingActivityCard";
import {
  Pagination,
  TABLE_PAGE_SIZE_OPTIONS,
  TablePageSizeSelect,
} from "./Pagination";

const LABELS = {
  emptyMessage: "Nenhuma remessa encontrada para os filtros selecionados.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) => `${total} remessa(s)`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription:
    "Mantendo os dados visíveis enquanto a nova consulta é aplicada.",
  initialLoadingTitle: "Carregando remessas",
  initialLoadingDescription: "Aguarde enquanto as remessas são obtidas.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: "mt",
  labels: LABELS,
  LoadingActivityCard,
  Pagination,
  TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 20,
});

export const DataTable = kit.DataTable;
export const DataTableSection = kit.DataTableSection;

export type { DataTableColumn } from "@delpi/plugin-ui/index";
export type {
  DashboardDataTableSectionProps as DataTableSectionProps,
  ServerPaginationConfig,
} from "@delpi/plugin-ui/index";
