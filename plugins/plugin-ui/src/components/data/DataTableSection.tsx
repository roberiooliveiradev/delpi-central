import type { ComponentType, CSSProperties, ReactNode } from "react";
import { Search } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ExcelExportButton } from "../../export/ExportButtons";
import { usePersistedViewLayout } from "../../hooks/usePersistedViewLayout";
import { useTableColumnVisibility } from "../../hooks/useTableColumnVisibility";
import { useTableFontSize } from "../../hooks/useTableFontSize";
import { buildDataTableSearchText } from "../../utils/dataTableSearch";
import { delpiUiClass } from "../../utils/delpiUiClass";
import { useClientPagination } from "../../utils/useClientPagination";
import { HelpTooltip } from "../help/HelpTooltip";
import { SegmentToggle } from "../forms/SegmentToggle";
import {
  DataTable,
  dataTableBemClasses,
  type DataTableClassNames,
  type DataTableColumn,
  type DataTableLabels,
  type DashboardDataTableProps,
} from "./DataTable";
import {
  createDashboardDataCardsGrid,
  type DashboardDataCardsGridProps,
} from "./DataCardsGrid";
import {
  createDashboardTableFontSizeControls,
  type DashboardTableFontSizeControlsProps,
} from "./TableFontSizeControls";
import { DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS } from "./tableColumnVisibilityLabels";
import { TableColumnVisibilityMenu } from "./TableColumnVisibilityMenu";

export type DataTableSectionExcelExport = {
  onExport: () => void | Promise<void>;
  disabled?: boolean;
  exporting?: boolean;
  label?: string;
  exportingLabel?: string;
};

const DEFAULT_VIEW_LAYOUT_LABELS = {
  ariaLabel: "Modo de visualização",
  table: "Tabela",
  cards: "Cards",
} as const;

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
  toolbarFilters: string;
  searchGroup: string;
  search: string;
  searchIcon: string;
  searchInput: string;
  searchHelp: string;
  toolbarExtra: string;
  footer: string;
  embeddedSection: string;
  interactiveModifier: string;
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
  /** Conteúdo à esquerda da toolbar (além do toggle Tabela/Cards nativo). */
  toolbarLeading?: ReactNode;
  /** Filtros/formulários em linha própria, largura total (FilterBar embedded). */
  toolbarFilters?: ReactNode;
  /**
   * Chave estável de localStorage para preferências de colunas.
   * Quando definida, exibe o menu “Colunas” e filtra a tabela.
   */
  columnPreferencesKey?: string;
  /**
   * Visibilidade inicial (antes de preferências salvas).
   * Ex.: `{ defect_description: false }` oculta a coluna por padrão.
   */
  defaultColumnVisibility?: Record<string, boolean>;
  /** Notifica chaves visíveis (export Excel, etc.). */
  onVisibleColumnKeysChange?: (keys: string[]) => void;
  /**
   * Chave localStorage — ativa controles nativos de tamanho de fonte.
   */
  fontSizePreferencesKey?: string;
  /** Chaves legadas lidas uma vez ao migrar preferência de fonte. */
  fontSizeLegacyStorageKeys?: readonly string[];
  /**
   * Chave localStorage — ativa toggle Tabela/Cards (exige `renderCard`).
   */
  viewLayoutPreferencesKey?: string;
  /** Render de cada linha no modo Cards. */
  renderCard?: (row: T) => ReactNode;
  /** Export Excel nativo na toolbar (opt-in). */
  excelExport?: DataTableSectionExcelExport;
  /**
   * Prefixo BEM do plugin — usado em SegmentToggle / factories internas.
   * `createDashboardDataTableKit` preenche automaticamente.
   */
  uiPrefix?: string;
  onRowClick?: (row: T) => void;
  getRowClassName?: (row: T) => string | undefined;
  headerActions?: ReactNode;
  footer?: ReactNode;
  embedded?: boolean;
  interactive?: boolean;
  hidePageSizeSelect?: boolean;
  defaultSortKey?: string | null;
  defaultSortDirection?: "asc" | "desc";
  clearClientSortOnThirdClick?: boolean;
  sectionClassNames: DataTableSectionClassNames;
  tableClassNames: DataTableClassNames;
  labels: DataTableSectionLabels;
  defaultPageSize?: number;
  tablePageSizeOptions: readonly number[];
  LoadingActivityCard: ComponentType<LoadingActivityCardInjectedProps>;
  Pagination: ComponentType<PaginationInjectedProps>;
  TablePageSizeSelect: ComponentType<TablePageSizeSelectInjectedProps>;
  TableFontSizeControls?: ComponentType<DashboardTableFontSizeControlsProps>;
  DataCardsGrid?: ComponentType<DashboardDataCardsGridProps>;
  useLoadingProgress: (active: boolean, requestProgress: RequestProgress) => number;
  useTrackedSingleFetchProgress: (active: boolean) => RequestProgress;
};

export function dataTableSectionBemClasses(prefix: string): DataTableSectionClassNames {
  const section = `${prefix}-table-section`;
  const uiSection = "delpi-ui-table-section";
  const toolbar = `${prefix}-table-toolbar`;
  const uiToolbar = "delpi-ui-table-toolbar";
  const search = `${prefix}-table-search`;
  const uiSearch = "delpi-ui-table-search";
  return {
    section: delpiUiClass(`${prefix}-card ${section}`, `delpi-ui-card ${uiSection}`),
    header: delpiUiClass(`${section}__header`, `${uiSection}__header`),
    title: delpiUiClass(`${prefix}-section-title`, "delpi-ui-section-title"),
    titleHelp: delpiUiClass(`${section}__title-help`, `${uiSection}__title-help`),
    metaGroup: delpiUiClass(`${section}__meta-group`, `${uiSection}__meta-group`),
    meta: delpiUiClass(`${section}__meta`, `${uiSection}__meta`),
    actions: delpiUiClass(`${section}__actions`, `${uiSection}__actions`),
    noPrint: delpiUiClass(`${prefix}-no-print`, "delpi-ui-no-print"),
    toolbar: delpiUiClass(toolbar, uiToolbar),
    toolbarFilters: delpiUiClass(
      `${section}__toolbar-filters`,
      `${uiSection}__toolbar-filters`,
    ),
    searchGroup: delpiUiClass(`${toolbar}__search-group`, `${uiToolbar}__search-group`),
    search: delpiUiClass(search, uiSearch),
    searchIcon: delpiUiClass(`${search}__icon`, `${uiSearch}__icon`),
    searchInput: delpiUiClass(`${search}__input`, `${uiSearch}__input`),
    searchHelp: delpiUiClass(`${search}__help`, `${uiSearch}__help`),
    toolbarExtra: delpiUiClass(`${toolbar}__extra`, `${uiToolbar}__extra`),
    footer: delpiUiClass(`${section}__footer`, `${uiSection}__footer`),
    embeddedSection: delpiUiClass(
      `${section} ${section}--embedded`,
      `${uiSection} ${uiSection}--embedded`,
    ),
    interactiveModifier: delpiUiClass(
      `${section}--interactive`,
      `${uiSection}--interactive`,
    ),
  };
}

function sortRowsClientSide<T>(
  rows: T[],
  columns: DataTableColumn<T>[],
  sortKey: string | null,
  sortDirection: "asc" | "desc",
): T[] {
  if (!sortKey) return rows;

  const column = columns.find((item) => item.key === sortKey);
  if (!column) return rows;

  const getSortValue =
    column.sortValue ??
    ((row: T): string | number | boolean | null | undefined => {
      const value = column.render(row);
      if (value == null || value === false) return "";
      if (typeof value === "number" || typeof value === "boolean") return value;
      if (typeof value === "string") return value.toLowerCase();
      return String(value).toLowerCase();
    });

  const directionFactor = sortDirection === "asc" ? 1 : -1;

  return [...rows].sort((first, second) => {
    const firstValue = getSortValue(first);
    const secondValue = getSortValue(second);

    if (firstValue == null && secondValue == null) return 0;
    if (firstValue == null) return 1 * directionFactor;
    if (secondValue == null) return -1 * directionFactor;
    if (typeof firstValue === "number" && typeof secondValue === "number") {
      return (firstValue - secondValue) * directionFactor;
    }

    const firstText = String(firstValue);
    const secondText = String(secondValue);
    return (
      firstText.localeCompare(secondText, "pt-BR", {
        numeric: true,
        sensitivity: "base",
      }) * directionFactor
    );
  });
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
  toolbarLeading,
  toolbarFilters,
  columnPreferencesKey,
  defaultColumnVisibility,
  onVisibleColumnKeysChange,
  fontSizePreferencesKey,
  fontSizeLegacyStorageKeys,
  viewLayoutPreferencesKey,
  renderCard,
  excelExport,
  uiPrefix = "ds",
  onRowClick,
  getRowClassName,
  headerActions,
  footer,
  embedded = false,
  interactive,
  hidePageSizeSelect = false,
  defaultSortKey = null,
  defaultSortDirection = "asc",
  clearClientSortOnThirdClick = false,
  sectionClassNames,
  tableClassNames,
  labels,
  defaultPageSize = 20,
  tablePageSizeOptions,
  LoadingActivityCard,
  Pagination,
  TablePageSizeSelect,
  TableFontSizeControls: TableFontSizeControlsProp,
  DataCardsGrid: DataCardsGridProp,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
}: DataTableSectionProps<T>) {
  const [localSearch, setLocalSearch] = useState("");
  const [localPageSize, setLocalPageSize] = useState(pageSize ?? defaultPageSize);
  const [localSortKey, setLocalSortKey] = useState<string | null>(defaultSortKey);
  const [localSortDirection, setLocalSortDirection] = useState<"asc" | "desc">(
    defaultSortDirection,
  );
  const search = serverSearch?.value ?? localSearch;
  const handleSearchChange = serverSearch?.onChange ?? setLocalSearch;
  const effectivePageSize = serverPagination?.pageSize ?? localPageSize;
  const pageSizeOptions = serverPagination?.pageSizeOptions ?? tablePageSizeOptions;
  const tableLabels: DataTableLabels = labels;
  const resolvedInteractive = interactive ?? Boolean(onRowClick);

  const columnCatalog = useMemo(
    () => columns.map((column) => ({ key: column.key, label: column.header })),
    [columns],
  );
  const columnVisibilityEnabled = Boolean(columnPreferencesKey);
  const fontSizeEnabled = Boolean(fontSizePreferencesKey);
  const viewLayoutEnabled = Boolean(viewLayoutPreferencesKey && renderCard);
  const excelExportEnabled = Boolean(excelExport?.onExport);

  const FontSizeControls =
    TableFontSizeControlsProp ??
    createDashboardTableFontSizeControls({ prefix: uiPrefix });
  const CardsGrid =
    DataCardsGridProp ?? createDashboardDataCardsGrid({ prefix: uiPrefix });

  const {
    visibility,
    orderedColumns,
    visibleKeys,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    reset: resetColumnVisibility,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: columnPreferencesKey ?? "",
    columns: columnCatalog,
    enabled: columnVisibilityEnabled,
    defaultVisibility: defaultColumnVisibility,
  });

  const fontSizeControls = useTableFontSize({
    storageKey: fontSizePreferencesKey ?? "",
    legacyStorageKeys: fontSizeLegacyStorageKeys,
    enabled: fontSizeEnabled,
  });

  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: viewLayoutPreferencesKey ?? "",
    enabled: viewLayoutEnabled,
  });

  const visibleColumns = useMemo(
    () => (columnVisibilityEnabled ? filterColumns(columns) : columns),
    [columnVisibilityEnabled, columns, filterColumns],
  );

  useEffect(() => {
    if (!columnVisibilityEnabled || !onVisibleColumnKeysChange) return;
    onVisibleColumnKeysChange(visibleKeys);
  }, [columnVisibilityEnabled, onVisibleColumnKeysChange, visibleKeys]);

  useEffect(() => {
    setLocalSortKey(defaultSortKey);
  }, [defaultSortKey]);

  useEffect(() => {
    setLocalSortDirection(defaultSortDirection);
  }, [defaultSortDirection]);

  const effectiveSortKey = serverSort?.sortKey ?? localSortKey;
  const effectiveSortDirection = serverSort?.sortDirection ?? localSortDirection;

  const handleSortChange = useCallback(
    (columnKey: string) => {
      if (serverSort) {
        serverSort.onSortChange(columnKey);
        return;
      }

      const isSameColumn = localSortKey === columnKey;
      if (clearClientSortOnThirdClick && isSameColumn && localSortDirection === "desc") {
        setLocalSortKey(null);
        return;
      }

      setLocalSortKey(columnKey);
      setLocalSortDirection(
        isSameColumn ? (localSortDirection === "asc" ? "desc" : "asc") : "asc",
      );
    },
    [clearClientSortOnThirdClick, localSortDirection, localSortKey, serverSort],
  );

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

  const sortedRows = useMemo(() => {
    if (serverSort || serverPagination) return filteredRows;
    return sortRowsClientSide(filteredRows, columns, effectiveSortKey, effectiveSortDirection);
  }, [
    columns,
    effectiveSortDirection,
    effectiveSortKey,
    filteredRows,
    serverPagination,
    serverSort,
  ]);

  const { page, setPage, slice, total } = useClientPagination(sortedRows, effectivePageSize);

  useEffect(() => {
    if (!serverPagination) {
      setPage(1);
    }
  }, [search, serverPagination, setPage]);

  useEffect(() => {
    if (!serverSort && !serverPagination) {
      setPage(1);
    }
  }, [effectiveSortKey, effectiveSortDirection, serverPagination, serverSort, setPage]);
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

  const sectionClass = [
    embedded ? sectionClassNames.embeddedSection : sectionClassNames.section,
    resolvedInteractive ? sectionClassNames.interactiveModifier : "",
  ]
    .filter(Boolean)
    .join(" ");

  const showHeader = Boolean(title.trim() || hint);
  const showNativeChrome =
    columnVisibilityEnabled ||
    fontSizeEnabled ||
    viewLayoutEnabled ||
    excelExportEnabled;
  const showToolbar =
    !hidePageSizeSelect ||
    !hideSearch ||
    Boolean(toolbarExtra) ||
    Boolean(toolbarLeading) ||
    showNativeChrome;

  const sectionStyle: CSSProperties | undefined = fontSizeEnabled
    ? ({ "--delpi-ui-table-font-size": `${fontSizeControls.fontSize}px` } as CSSProperties)
    : undefined;

  const showCards = viewLayoutEnabled && layout === "cards";
  const resolvedEmpty = emptyMessage ?? labels.emptyMessage;

  const viewToggle = viewLayoutEnabled ? (
    <SegmentToggle
      prefix={uiPrefix}
      size="sm"
      ariaLabel={DEFAULT_VIEW_LAYOUT_LABELS.ariaLabel}
      idPrefix={`${uiPrefix}-datatable-layout`}
      value={layout}
      onChange={setLayout}
      options={[
        { value: "table", label: DEFAULT_VIEW_LAYOUT_LABELS.table },
        { value: "cards", label: DEFAULT_VIEW_LAYOUT_LABELS.cards },
      ]}
    />
  ) : null;

  const nativeToolbarExtra = (
    <>
      {excelExportEnabled && excelExport ? (
        <ExcelExportButton
          density="toolbar"
          onExport={excelExport.onExport}
          disabled={excelExport.disabled}
          exporting={excelExport.exporting}
          label={excelExport.label}
          exportingLabel={excelExport.exportingLabel}
        />
      ) : null}
      {fontSizeEnabled ? (
        <FontSizeControls
          fontSize={fontSizeControls.fontSize}
          canIncrease={fontSizeControls.canIncrease}
          canDecrease={fontSizeControls.canDecrease}
          isDefault={fontSizeControls.isDefault}
          onIncrease={fontSizeControls.increase}
          onDecrease={fontSizeControls.decrease}
          onReset={fontSizeControls.reset}
        />
      ) : null}
      {columnVisibilityEnabled ? (
        <TableColumnVisibilityMenu
          columns={orderedColumns}
          visibility={visibility}
          onToggleColumn={setColumnVisible}
          onReorderColumns={reorderColumns}
          onReset={resetColumnVisibility}
          labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
        />
      ) : null}
      {toolbarExtra}
    </>
  );

  const hasToolbarExtra =
    excelExportEnabled ||
    fontSizeEnabled ||
    columnVisibilityEnabled ||
    Boolean(toolbarExtra);

  return (
    <section
      className={sectionClass || sectionClassNames.section}
      style={sectionStyle}
      aria-busy={loading || refreshing}
    >
      {showHeader ? (
        <div className={sectionClassNames.header}>
          {title.trim() ? (
            <h2 className={sectionClassNames.title}>
              {titleHint ? (
                <HelpTooltip
                  content={titleHint}
                  ariaLabel={labels.titleHelpAriaLabel(title)}
                  wrap
                  placement="bottom"
                  className={sectionClassNames.titleHelp}
                >
                  <span className="delpi-ui-section-hint-label">{title}</span>
                </HelpTooltip>
              ) : (
                title
              )}
            </h2>
          ) : (
            <span />
          )}
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
      ) : null}

      {footer ? <div className={sectionClassNames.footer}>{footer}</div> : null}

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
          {showToolbar ? (
            <div className={sectionClassNames.toolbar}>
              {viewToggle || toolbarLeading ? (
                <div className={sectionClassNames.searchGroup}>
                  {viewToggle}
                  {toolbarLeading}
                </div>
              ) : null}

              {!hidePageSizeSelect ? (
                <TablePageSizeSelect
                  pageSize={paginationSize}
                  pageSizeOptions={pageSizeOptions}
                  onPageSizeChange={handlePageSizeChange}
                />
              ) : null}

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

            {hasToolbarExtra ? (
              <div className={sectionClassNames.toolbarExtra}>{nativeToolbarExtra}</div>
            ) : null}
            </div>
          ) : null}

          {toolbarFilters ? (
            <div className={sectionClassNames.toolbarFilters}>{toolbarFilters}</div>
          ) : null}

          {showCards ? (
            <CardsGrid
              ariaLabel={title.trim() || DEFAULT_VIEW_LAYOUT_LABELS.cards}
              empty={displayRows.length === 0 ? resolvedEmpty : undefined}
              style={sectionStyle}
            >
              {displayRows.map((row) => (
                <div key={rowKey(row)}>{renderCard?.(row)}</div>
              ))}
            </CardsGrid>
          ) : (
            <DataTable
              columns={visibleColumns}
              rows={displayRows}
              rowKey={(row, _index) => rowKey(row)}
              emptyMessage={resolvedEmpty}
              onRowClick={onRowClick}
              getRowClassName={getRowClassName}
              sortKey={effectiveSortKey}
              sortDirection={effectiveSortDirection}
              onSortChange={
                serverSort?.onSortChange ?? (serverPagination ? undefined : handleSortChange)
              }
              layout="section"
              enableColumnReorder={columnVisibilityEnabled}
              onColumnOrderChange={
                columnVisibilityEnabled ? applyVisibleOrder : undefined
              }
              classNames={tableClassNames}
              labels={tableLabels}
            />
          )}

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
  | "TableFontSizeControls"
  | "DataCardsGrid"
  | "uiPrefix"
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
  sectionClassNames?: Partial<DataTableSectionClassNames>;
  tableClassNames?: DataTableClassNames;
}) {
  const sectionClassNames = {
    ...dataTableSectionBemClasses(config.prefix),
    ...config.sectionClassNames,
  };
  const tableClassNames = config.tableClassNames ?? dataTableBemClasses(config.prefix);
  const TableFontSizeControls = createDashboardTableFontSizeControls({
    prefix: config.prefix,
  });
  const DataCardsGrid = createDashboardDataCardsGrid({ prefix: config.prefix });

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
        TableFontSizeControls={TableFontSizeControls}
        DataCardsGrid={DataCardsGrid}
        uiPrefix={config.prefix}
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
