import {
  createDashboardDataTableKit,
  dataTableBemClasses,
  dataTableSectionBemClasses,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import { LoadingActivityCard } from "./LoadingActivityCard";
import { Pagination } from "./Pagination";

export const DEFAULT_TABLE_PAGE_SIZE = 20;
export const TABLE_PAGE_SIZE_OPTIONS = [DEFAULT_TABLE_PAGE_SIZE] as const;

function TablePageSizeSelect(_props: {
  pageSize: number;
  pageSizeOptions?: readonly number[];
  onPageSizeChange: (pageSize: number) => void;
}) {
  return null;
}

/** Dual-class completo do kit — sem overrides que removam classes canônicas. */
const DS_TABLE_CLASS_NAMES = dataTableBemClasses("ds");

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) => `${total} registro(s)`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription: "Mantendo os dados visíveis enquanto a consulta é aplicada.",
  initialLoadingTitle: "Carregando registros",
  initialLoadingDescription: "Aguarde enquanto os dados da tabela são obtidos.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: "ds",
  labels: LABELS,
  LoadingActivityCard,
  Pagination,
  TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: DEFAULT_TABLE_PAGE_SIZE,
  sectionClassNames: {
    ...dataTableSectionBemClasses("ds"),
    toolbarExtra: "ds-table-toolbar__filters",
  },
  tableClassNames: DS_TABLE_CLASS_NAMES,
});

export const DataTable = kit.DataTable;
export const DataTableSection = kit.DataTableSection;

export type { DataTableColumn };
