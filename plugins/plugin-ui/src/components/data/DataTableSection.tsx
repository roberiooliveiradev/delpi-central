import type { ComponentType, ReactNode } from "react";
import { Search } from "lucide-react";
import { useCallback, useMemo, useState } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { buildDataTableSearchText } from "../../utils/dataTableSearch";
import { useClientPagination } from "../../utils/useClientPagination";
import {
  DataTable,
  dataTableBemClasses,
  type DataTableClassNames,
  type DataTableColumn,
  type DataTableLabels,
  type DashboardDataTableProps,
} from "./DataTable";

export type {
  DataTableColumn,
  DataTableProps,
  DashboardDataTableProps,
} from "./DataTable";

export type ServerPaginationConfig = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: readonly number[];
};

export type ServerSortConfig = {
  sortKey: string | null;
  sortDirection: "asc" | "desc";
  onSortChange: (columnKey: string) => void;
};

export type ServerSearchConfig = {
  value: string;
  onChange: (value: string) => void;
};

export type DataTableSectionClassNames = {
  section: string;
  header: string;
  title: string;
  titleHelp: string;
  metaGroup: string;
  meta: string;
  actions: string;
  noPrint: string;
  toolbar: string;
  searchGroup: string;
  search: string;
  searchIcon: string;
  searchInput: string;
  searchHelp: string;
  toolbarExtra: string;
};

export type DataTableSectionLabels = {
  emptyMessage: string;
  loadingMessage: string;
  sortByAriaLabel: (header: string) => string;
  headerHelpAriaLabel: (header: string) => string;
  searchPlaceholder: string;
  searchAriaLabel: string;
  searchHelpAriaLabel: string;
  recordsCount: (total: number) => string;
  refreshLoadingTitle: string;
  refreshLoadingDescription: string;
  initialLoadingTitle: string;
  initialLoadingDescription: string;
  titleHelpAriaLabel: (title: string) => string;
};

export type RequestProgress = {
  completed: number;
  total: number;
};

export type LoadingActivityCardInjectedProps = {
  title: string;
  description: string;
  variant?: "compact" | "panel";
  sticky?: boolean;
  progressPercent?: number;
};

export type PaginationInjectedProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export type TablePageSizeSelectInjectedProps = {
  pageSize: number;
  pageSizeOptions?: readonly number[];
  onPageSizeChange: (pageSize: number) => void;
};

export type DataTableSectionProps<T> = {
  title: string;
  titleHint?: string;
  hint?: string;
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  refreshing?: boolean;
  emptyMessage?: string;
  pageSize?: number;
  searchPlaceholder?: string;
  searchHint?: string;
  getSearchText?: (row: T) => string;
  hideSearch?: boolean;
  serverPagination?: ServerPaginationConfig;
  serverSort?: ServerSortConfig;
  serverSearch?: ServerSearchConfig;
  toolbarExtra?: ReactNode;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
  headerActions?: ReactNode;
  sectionClassNames: DataTableSectionClassNames;
  tableClassNames: DataTableClassNames;
  labels: DataTableSectionLabels;
  defaultPageSize?: number;
  tablePageSizeOptions: readonly number[];
  LoadingActivityCard: ComponentType<LoadingActivityCardInjectedProps>;
  Pagination: ComponentType<PaginationInjectedProps>;
  TablePageSizeSelect: ComponentType<TablePageSizeSelectInjectedProps>;
  useLoadingProgress: (active: boolean, requestProgress: RequestProgress) => number;
  useTrackedSingleFetchProgress: (active: boolean) => RequestProgress;
};

export function dataTableSectionBemClasses(prefix: string): DataTableSectionClassNames {
  return {
    section: `${prefix}-card ${prefix}-table-section`,
    header: `${prefix}-table-section__header`,
    title: `${prefix}-section-title`,
    titleHelp: `${prefix}-table-section__title-help`,
    metaGroup: `${prefix}-table-section__meta-group`,
    meta: `${prefix}-table-section__meta`,
    actions: `${prefix}-table-section__actions`,
    noPrint: `${prefix}-no-print`,
    toolbar: `${prefix}-table-toolbar`,
    searchGroup: `${prefix}-table-toolbar__search-group`,
    search: `${prefix}-table-search`,
    searchIcon: `${prefix}-table-search__icon`,
    searchInput: `${prefix}-table-search__input`,
    searchHelp: `${prefix}-table-search__help`,
    toolbarExtra: `${prefix}-table-toolbar__extra`,
  };
}

export function DataTableSection<T>({
  title,
  titleHint,
  hint,
  columns,
  rows,
  rowKey,
  loading = false,
  refreshing = false,
  emptyMessage,
  pageSize,
  searchPlaceholder,
  searchHint,
  getSearchText,
  hideSearch = false,
  serverPagination,
  serverSort,
  serverSearch,
  toolbarExtra,
  onRowClick,
  getRowClassName,
  headerActions,
  sectionClassNames,
  tableClassNames,
  labels,
  defaultPageSize = 20,
  tablePageSizeOptions,
  LoadingActivityCard,
  Pagination,
  TablePageSizeSelect,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
}: DataTableSectionProps<T>) {
  const [localSearch, setLocalSearch] = useState("");
  const [localPageSize, setLocalPageSize] = useState(pageSize ?? defaultPageSize);
  const search = serverSearch?.value ?? localSearch;
  const handleSearchChange = serverSearch?.onChange ?? setLocalSearch;
  const effectivePageSize = serverPagination?.pageSize ?? localPageSize;
  const pageSizeOptions = serverPagination?.pageSizeOptions ?? tablePageSizeOptions;
  const tableLabels: DataTableLabels = labels;

  const filteredRows = useMemo(() => {
    if (serverPagination) return rows;

    const query = search.trim().toLowerCase();
    if (!query) return rows;

    return rows.filter((row) => {
      const haystack = (getSearchText ?? ((item) => buildDataTableSearchText(item, columns)))(
        row,
      ).toLowerCase();
      return haystack.includes(query);
    });
  }, [rows, search, columns, getSearchText, serverPagination]);

  const { page, setPage, slice, total } = useClientPagination(filteredRows, effectivePageSize);
  const displayRows = serverPagination ? rows : slice;
  const paginationPage = serverPagination?.page ?? page;
  const paginationTotal = serverPagination?.total ?? total;
  const paginationSize = serverPagination?.pageSize ?? effectivePageSize;
  const handlePageChange = serverPagination?.onPageChange ?? setPage;
  const handlePageSizeChange = useCallback(
    (nextPageSize: number) => {
      if (serverPagination?.onPageSizeChange) {
        serverPagination.onPageSizeChange(nextPageSize);
        return;
      }

      setLocalPageSize(nextPageSize);
      setPage(1);
    },
    [serverPagination, setPage],
  );

  const showInitialLoading = loading && rows.length === 0;
  const showRefreshLoading = refreshing && rows.length > 0;
  const initialFetchProgress = useTrackedSingleFetchProgress(showInitialLoading);
  const refreshFetchProgress = useTrackedSingleFetchProgress(showRefreshLoading);
  const initialLoadingProgress = useLoadingProgress(showInitialLoading, initialFetchProgress);
  const refreshLoadingProgress = useLoadingProgress(showRefreshLoading, refreshFetchProgress);

  return (
    <section className={sectionClassNames.section} aria-busy={loading || refreshing}>
      <div className={sectionClassNames.header}>
        <h2 className={sectionClassNames.title}>
          {title}
          {titleHint ? (
            <HelpTooltip
              content={titleHint}
              ariaLabel={labels.titleHelpAriaLabel(title)}
              className={sectionClassNames.titleHelp}
            />
          ) : null}
        </h2>
        <div className={sectionClassNames.metaGroup}>
          {hint ? <span className={sectionClassNames.meta}>{hint}</span> : null}
          <span className={sectionClassNames.meta}>{labels.recordsCount(paginationTotal)}</span>
          {headerActions ? (
            <div
              className={`${sectionClassNames.actions} ${sectionClassNames.noPrint}`.trim()}
            >
              {headerActions}
            </div>
          ) : null}
        </div>
      </div>

      {showRefreshLoading ? (
        <LoadingActivityCard
          title={labels.refreshLoadingTitle}
          description={labels.refreshLoadingDescription}
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {showInitialLoading ? (
        <LoadingActivityCard
          title={labels.initialLoadingTitle}
          description={labels.initialLoadingDescription}
          progressPercent={initialLoadingProgress}
        />
      ) : (
        <>
          <div className={sectionClassNames.toolbar}>
            <TablePageSizeSelect
              pageSize={paginationSize}
              pageSizeOptions={pageSizeOptions}
              onPageSizeChange={handlePageSizeChange}
            />

            {!hideSearch ? (
              <div className={sectionClassNames.searchGroup}>
                <div className={sectionClassNames.search} role="search">
                  <Search size={16} aria-hidden="true" className={sectionClassNames.searchIcon} />
                  <input
                    type="search"
                    className={sectionClassNames.searchInput}
                    value={search}
                    placeholder={searchPlaceholder ?? labels.searchPlaceholder}
                    onChange={(event) => handleSearchChange(event.target.value)}
                    aria-label={labels.searchAriaLabel}
                  />
                </div>
                {searchHint ? (
                  <HelpTooltip
                    content={searchHint}
                    ariaLabel={labels.searchHelpAriaLabel}
                    className={sectionClassNames.searchHelp}
                  />
                ) : null}
              </div>
            ) : null}

            {toolbarExtra ? (
              <div className={sectionClassNames.toolbarExtra}>{toolbarExtra}</div>
            ) : null}
          </div>

          <DataTable
            columns={columns}
            rows={displayRows}
            rowKey={rowKey}
            emptyMessage={emptyMessage}
            onRowClick={onRowClick}
            getRowClassName={getRowClassName}
            sortKey={serverSort?.sortKey}
            sortDirection={serverSort?.sortDirection}
            onSortChange={serverSort?.onSortChange}
            layout="section"
            classNames={tableClassNames}
            labels={tableLabels}
          />

          <Pagination
            page={paginationPage}
            pageSize={paginationSize}
            total={paginationTotal}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </section>
  );
}

export type DashboardDataTableSectionProps<T> = Omit<
  DataTableSectionProps<T>,
  | "sectionClassNames"
  | "tableClassNames"
  | "labels"
  | "defaultPageSize"
  | "tablePageSizeOptions"
  | "LoadingActivityCard"
  | "Pagination"
  | "TablePageSizeSelect"
  | "useLoadingProgress"
  | "useTrackedSingleFetchProgress"
>;

export function createDashboardDataTableKit(config: {
  prefix: string;
  labels: DataTableSectionLabels;
  LoadingActivityCard: ComponentType<LoadingActivityCardInjectedProps>;
  Pagination: ComponentType<PaginationInjectedProps>;
  TablePageSizeSelect: ComponentType<TablePageSizeSelectInjectedProps>;
  tablePageSizeOptions: readonly number[];
  useLoadingProgress: DataTableSectionProps<unknown>["useLoadingProgress"];
  useTrackedSingleFetchProgress: DataTableSectionProps<unknown>["useTrackedSingleFetchProgress"];
  defaultPageSize?: number;
}) {
  const sectionClassNames = dataTableSectionBemClasses(config.prefix);
  const tableClassNames = dataTableBemClasses(config.prefix);

  function DashboardDataTable<T>(props: DashboardDataTableProps<T>) {
    return <DataTable classNames={tableClassNames} labels={config.labels} {...props} />;
  }

  function DashboardDataTableSection<T>(props: DashboardDataTableSectionProps<T>) {
    return (
      <DataTableSection
        sectionClassNames={sectionClassNames}
        tableClassNames={tableClassNames}
        labels={config.labels}
        defaultPageSize={config.defaultPageSize}
        tablePageSizeOptions={config.tablePageSizeOptions}
        LoadingActivityCard={config.LoadingActivityCard}
        Pagination={config.Pagination}
        TablePageSizeSelect={config.TablePageSizeSelect}
        useLoadingProgress={config.useLoadingProgress}
        useTrackedSingleFetchProgress={config.useTrackedSingleFetchProgress}
        {...props}
      />
    );
  }

  return {
    DataTable: DashboardDataTable,
    DataTableSection: DashboardDataTableSection,
  };
}
