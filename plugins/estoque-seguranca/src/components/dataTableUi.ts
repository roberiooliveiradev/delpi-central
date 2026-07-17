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
  emptyMessage: "Nenhuma matéria-prima encontrada para os filtros selecionados.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) => `${total} registro(s)`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription:
    "Mantendo os dados visíveis enquanto a nova consulta é aplicada.",
  initialLoadingTitle: "Carregando matérias-primas",
  initialLoadingDescription: "Aguarde enquanto os dados da tabela são obtidos.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: "ess",
  labels: LABELS,
  LoadingActivityCard,
  Pagination,
  TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 50,
});

export const DataTable = kit.DataTable;
export const DataTableSection = kit.DataTableSection;

export type { DataTableColumn } from "@delpi/plugin-ui/index";
export type {
  DashboardDataTableSectionProps as DataTableSectionProps,
  ServerPaginationConfig,
} from "@delpi/plugin-ui/index";
