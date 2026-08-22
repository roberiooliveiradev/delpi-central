import {
  createDashboardDataTableKit,
  dataTableBemClasses,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";
import {
  FinTablePageSizeSelect,
  FinTablePagination,
  TABLE_PAGE_SIZE_OPTIONS,
} from "./finPaginationKit";
import { FinLoadingCard } from "./finUiKit";

const TABLE_LABELS = {
  emptyMessage: copy.table.empty,
  loadingMessage: copy.table.loading,
  sortByAriaLabel: copy.table.sortByAriaLabel,
  headerHelpAriaLabel: copy.table.headerHelpAriaLabel,
  searchPlaceholder: copy.table.searchPlaceholder,
  searchAriaLabel: copy.table.searchAriaLabel,
  searchHelpAriaLabel: copy.table.searchHelpAriaLabel,
  recordsCount: copy.table.recordsCount,
  refreshLoadingTitle: copy.table.refreshLoadingTitle,
  refreshLoadingDescription: copy.table.refreshLoadingDescription,
  initialLoadingTitle: copy.table.initialLoadingTitle,
  initialLoadingDescription: copy.table.initialLoadingDescription,
  titleHelpAriaLabel: copy.table.titleHelpAriaLabel,
};

const kit = createDashboardDataTableKit({
  prefix: "fin",
  labels: TABLE_LABELS,
  LoadingActivityCard: FinLoadingCard,
  Pagination: FinTablePagination,
  TablePageSizeSelect: FinTablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 20,
});

export const FIN_TABLE_CLASSES = dataTableBemClasses("fin");

export const FIN_TABLE_LABELS = {
  emptyMessage: copy.table.empty,
  loadingMessage: copy.table.loading,
  sortByAriaLabel: copy.table.sortByAriaLabel,
  headerHelpAriaLabel: copy.table.headerHelpAriaLabel,
};

export const DataTable = kit.DataTable;
export const DataTableSection = kit.DataTableSection;

export type { DataTableColumn };
