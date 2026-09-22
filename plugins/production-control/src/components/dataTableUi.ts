import {
  createDashboardDataTableKit,
  createDashboardLoadingActivityCard,
  createDashboardPaginationKit,
  dataTableBemClasses,
  type DataTableClassNames,
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

function withSentenceHeaders(classNames: DataTableClassNames): DataTableClassNames {
  const extra = classNames.sentenceHeadersWrap;
  if (!extra) return classNames;
  return {
    ...classNames,
    wrap: [classNames.wrap, extra].filter(Boolean).join(" "),
    wrapSection: [classNames.wrapSection, extra].filter(Boolean).join(" "),
    wrapEmbedded: [classNames.wrapEmbedded, extra].filter(Boolean).join(" "),
    scrollWrap: classNames.scrollWrap
      ? [classNames.scrollWrap, extra].filter(Boolean).join(" ")
      : classNames.scrollWrap,
  };
}

const kitConfig = {
  prefix: "ppc",
  labels: copy.tableSection,
  LoadingActivityCard,
  Pagination: paginationKit.Pagination,
  TablePageSizeSelect: paginationKit.TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: 50,
};

const kit = createDashboardDataTableKit(kitConfig);
const sentenceHeaderKit = createDashboardDataTableKit({
  ...kitConfig,
  tableClassNames: withSentenceHeaders(dataTableBemClasses("ppc")),
});

export const DataTableSection = kit.DataTableSection;
export const SentenceHeaderDataTableSection = sentenceHeaderKit.DataTableSection;
export type { DataTableColumn } from "@delpi/plugin-ui/index";
