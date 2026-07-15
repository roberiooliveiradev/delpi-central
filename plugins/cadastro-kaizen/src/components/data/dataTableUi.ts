import {
  createDashboardDataTableKit,
  dataTableBemClasses,
  type DataTableClassNames,
} from "@delpi/plugin-ui/index";

import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../utils/loadingProgress";
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

const KZ_TABLE_CLASS_NAMES: DataTableClassNames = {
  ...dataTableBemClasses("kz"),
  wrapSection: "kz-table-wrap",
  wrapEmbedded: "kz-table-wrap",
  sortButton: "kz-table__sort",
  sortButtonActive: "kz-table__sort kz-table__sort--active",
  sortIndicator: "kz-table__sort-indicator",
};

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
  prefix: "kz",
  labels: LABELS,
  LoadingActivityCard,
  Pagination,
  TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: DEFAULT_TABLE_PAGE_SIZE,
  tableClassNames: KZ_TABLE_CLASS_NAMES,
});

export const DataTable = kit.DataTable;
export const DataTableSection = kit.DataTableSection;

export type { DataTableColumn } from "@delpi/plugin-ui/index";
