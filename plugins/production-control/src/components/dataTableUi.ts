import {
  createDashboardDataTableKit,
  createDashboardLoadingActivityCard,
  createDashboardPaginationKit,
} from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import { useLoadingProgress, useTrackedSingleFetchProgress } from "../utils/loadingProgress";

const TABLE_PAGE_SIZE_OPTIONS = [25, 50, 100] as const;

const LoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.tableSection.loadingMessage,
  },
});

const paginationKit = createDashboardPaginationKit({
  prefix: "ppc",
  labels: copy.pagination,
  tablePageSizeLabels: {
    label: copy.pagination.pageSizeLabel,
    selectAriaLabel: copy.pagination.pageSizeAria,
  },
});

const kit = createDashboardDataTableKit({
  prefix: "ppc",
  labels: copy.tableSection,
  LoadingActivityCard,
  Pagination: paginationKit.Pagination,
  TablePageSizeSelect: paginationKit.TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 50,
});

export const DataTableSection = kit.DataTableSection;
export type { DataTableColumn } from "@delpi/plugin-ui/index";
