/**
 * Contratos mínimos do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote; não compilar o source do kit aqui.
 */
declare module "@delpi/plugin-ui/index" {
  import type {
    ComponentType,
    FormEvent,
    InputHTMLAttributes,
    ReactElement,
    ReactNode,
  } from "react";

  export type StatusBadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

  export type DashboardStatusBadgeProps = {
    label: string;
    variant?: StatusBadgeVariant;
    className?: string;
  };

  export function createDashboardStatusBadge(config: {
    prefix: string;
  }): ComponentType<DashboardStatusBadgeProps>;

  export type DashboardSimpleKpiCardProps = {
    title: string;
    titleHint?: string;
    value: string;
    icon: ReactNode;
    loading?: boolean;
    subtitle?: string;
    variant?: string;
    wide?: boolean;
    valueTone?: "default" | "danger";
    valueTag?: "h3" | "p" | "strong";
    className?: string;
  };

  export function createSimpleKpiCard(
    prefix: string,
    options?: {
      withBody?: boolean;
      withSubtitle?: boolean;
      defaultValueTag?: "h3" | "p" | "strong";
      layout?: "iconStart" | "iconEnd";
    },
  ): ComponentType<DashboardSimpleKpiCardProps>;

  export type StateBoxVariant = "loading" | "error" | "empty";

  export type DashboardStateBoxPanelProps = {
    variant: StateBoxVariant;
    title: string;
    message?: string;
    action?: ReactNode;
  };

  export function createStateBoxPanel(config: {
    prefix: string;
    renderIcon: (variant: StateBoxVariant) => ReactNode;
    iconClassName?: (variant: StateBoxVariant) => string | undefined;
  }): ComponentType<DashboardStateBoxPanelProps>;

  export type PageHeaderLayout = "brand" | "titleRow" | "stack";

  export type DashboardPageHeaderProps = {
    layout?: PageHeaderLayout;
    title: ReactNode;
    subtitle?: ReactNode;
    eyebrow?: ReactNode;
    icon?: ReactNode;
    badge?: ReactNode;
    nav?: ReactNode;
    actions?: ReactNode;
    onRefresh?: () => void;
    refreshing?: boolean;
    compact?: boolean;
  };

  export function createDashboardPageHeader(config: {
    layout: PageHeaderLayout;
    classNames: Record<string, string | undefined>;
    labels: { refresh: string; refreshing: string };
  }): ComponentType<DashboardPageHeaderProps>;

  export function pageHeaderTitleRowBemClasses(
    prefix: string,
    options?: { buttonClass?: string; spinClass?: string },
  ): Record<string, string | undefined>;

  export type FiltersRowClassNames = {
    row: string;
    rowExtended: string;
    rowCompact?: string;
    trailingBox?: string;
    filterBoxSpacer: string;
    filterBox: string;
    fieldLabel: string;
  };

  export type FilterInputFieldProps = {
    label: string;
    hint?: string;
    id?: string;
    type: Extract<InputHTMLAttributes<HTMLInputElement>["type"], "month" | "date" | "text" | "search">;
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
    placeholder?: string;
    classNames: Pick<FiltersRowClassNames, "filterBox" | "fieldLabel">;
  };

  export function FilterInputField(props: FilterInputFieldProps): ReactElement;

  export type FilterSelectOption = {
    value: string;
    label: string;
  };

  export type FilterSelectFieldProps = {
    label: string;
    hint?: string;
    id?: string;
    value: string;
    onChange: (value: string) => void;
    options: readonly FilterSelectOption[];
    placeholderOption?: string;
    disabled?: boolean;
    searchable?: boolean;
    classNames: Pick<FiltersRowClassNames, "filterBox" | "fieldLabel">;
    selectClassNames?: Record<string, string>;
    selectLabels?: Record<string, string | ((fieldLabel: string) => string)>;
    portalScopeClassName?: string;
  };

  export function filtersRowBemClasses(prefix: string): FiltersRowClassNames;

  export type DashboardFiltersKit = {
    FiltersRow: ComponentType<Record<string, unknown>>;
    FilterInputField: ComponentType<Omit<FilterInputFieldProps, "classNames">>;
    FilterSelectField: ComponentType<
      Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">
    >;
  };

  export function createDashboardFiltersKit(config: {
    prefix: string;
    labels: { filtersAriaLabel: string };
    portalScopeClassName?: string;
  }): DashboardFiltersKit;

  export type FilterCheckboxFieldClassNames = {
    root: string;
    labelRow: string;
    checkboxControl: string;
    checkboxRoot: string;
  };

  export type DashboardFilterCheckboxFieldProps = {
    id: string;
    label: string;
    hint?: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
    checkboxLabel?: string;
    disabled?: boolean;
  };

  export function filterCheckboxFieldBemClasses(prefix: string): FilterCheckboxFieldClassNames;

  export function createDashboardFilterCheckboxField(config: {
    classNames: FilterCheckboxFieldClassNames;
    labels: { defaultCheckboxLabel: string };
  }): ComponentType<DashboardFilterCheckboxFieldProps>;

  export type FilterBarShellProps = {
    children: ReactNode;
    leading?: ReactNode;
    onSubmit?: (event: FormEvent<HTMLFormElement>) => void;
    embedded?: boolean;
    layout?: "inline" | "grid";
    className?: string;
    ariaLabel?: string;
  };

  export function createFilterBarShell(config: {
    prefix: string;
    withGrid?: boolean;
    defaultAriaLabel?: string;
    block?: string;
  }): ComponentType<FilterBarShellProps>;

  export type LoadingActivityCardLabels = {
    progressRemaining: (remainingPercent: number) => string;
    progressStarting?: string;
    progressRemainingOnlyAfterStart?: boolean;
    progressAriaDeterminate: (remainingPercent: number) => string;
    progressAriaStarting?: string;
    progressAriaIndeterminate: string;
  };

  export type DashboardLoadingActivityCardProps = {
    title: string;
    description?: string;
    variant?: "compact" | "panel";
    tone?: "neutral" | "info";
    sticky?: boolean;
    progressPercent?: number;
    className?: string;
  };

  export function createDashboardLoadingActivityCard(config: {
    prefix: string;
    labels: LoadingActivityCardLabels;
    withCopyWrapper?: boolean;
    block?: string;
    defaultTone?: "neutral" | "info";
  }): ComponentType<DashboardLoadingActivityCardProps>;

  export type PageJumpValidationReason =
    | "empty"
    | "invalid"
    | "below_min"
    | "above_max";

  export const TABLE_PAGE_SIZE_OPTIONS: readonly number[];

  export type PaginationInjectedProps = {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
    disabled?: boolean;
  };

  export type TablePageSizeSelectInjectedProps = {
    pageSize: number;
    onPageSizeChange: (pageSize: number) => void;
    pageSizeOptions?: readonly number[];
    disabled?: boolean;
  };

  export function createDashboardPaginationKit(config: {
    prefix: string;
    labels: Record<string, string | ((...args: never[]) => string)>;
    tablePageSizeLabels: { label: string; selectAriaLabel: string };
    hints?: Record<string, string>;
  }): {
    Pagination: ComponentType<PaginationInjectedProps>;
    TablePageSizeSelect: ComponentType<TablePageSizeSelectInjectedProps>;
  };

  export type DataTableColumn<T> = {
    key: string;
    header: string;
    headerHint?: string;
    render: (row: T) => ReactNode;
    className?: string;
    align?: "left" | "right" | "center";
    interactive?: boolean;
    sortable?: boolean;
    sortValue?: (row: T) => string | number | null | undefined;
    mobileLabel?: string;
  };

  export type ServerPaginationConfig = {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
    onPageSizeChange?: (pageSize: number) => void;
    pageSizeOptions?: readonly number[];
  };

  export type DashboardDataTableSectionProps<T> = {
    title?: string;
    hint?: string;
    columns: DataTableColumn<T>[];
    rows: T[];
    rowKey: (row: T) => string;
    loading?: boolean;
    refreshing?: boolean;
    emptyMessage?: string;
    hideSearch?: boolean;
    columnPreferencesKey?: string;
    serverPagination?: ServerPaginationConfig;
    onRowClick?: (row: T) => void;
    interactive?: boolean;
  };

  export type DashboardDrawerShellProps = {
    open: boolean;
    title: string;
    description?: string;
    footer?: ReactNode;
    onClose: () => void;
    children: ReactNode;
    className?: string;
  };

  export function createDrawerShell(config: {
    prefix: string;
    closeAriaLabel?: string;
    backdropAriaLabel?: string;
    portalScopeClassName?: string;
  }): ComponentType<DashboardDrawerShellProps>;

  export type DashboardModalShellProps = {
    open: boolean;
    title: string;
    description?: string;
    footer?: ReactNode;
    headerActions?: ReactNode;
    onClose: () => void;
    children: ReactNode;
    className?: string;
    closeAriaLabel?: string;
  };

  export function createModalShell(config: {
    prefix: string;
    overlayClassName?: string;
    closeAriaLabel?: string;
    portalScopeClassName?: string;
    variant?: "default" | "wide" | "page";
  }): ComponentType<DashboardModalShellProps>;

  export type DetailField = {
    label: string;
    value?: ReactNode;
    hint?: string;
    wide?: boolean;
  };

  export function createDashboardDetailFieldGrid(config: {
    prefix?: string;
    labels: { fieldHelpAriaLabel: (label: string) => string; emptyMessage?: string };
    valueFallback?: string;
  }): ComponentType<{ fields: DetailField[] }>;

  export type LoadingActivityCardInjectedProps = DashboardLoadingActivityCardProps;

  export function createDashboardDataTableKit(config: {
    prefix: string;
    labels: Record<string, string | ((...args: never[]) => string)>;
    LoadingActivityCard: ComponentType<LoadingActivityCardInjectedProps>;
    Pagination: ComponentType<PaginationInjectedProps>;
    TablePageSizeSelect: ComponentType<TablePageSizeSelectInjectedProps>;
    tablePageSizeOptions: readonly number[];
    useLoadingProgress: (...args: never[]) => unknown;
    useTrackedSingleFetchProgress: (...args: never[]) => unknown;
    defaultPageSize?: number;
    sectionClassNames?: Record<string, string>;
    tableClassNames?: Record<string, string>;
  }): {
    DataTable: ComponentType<Record<string, unknown>>;
    DataTableSection: <T>(props: DashboardDataTableSectionProps<T>) => ReactElement;
  };

  export type SeriesChartValueFormat =
    | "auto"
    | "number"
    | "currency"
    | "currency4"
    | "percent";

  export type SeriesChartPoint = {
    label?: string;
    value?: number | null;
  };

  export type SeriesChartOptions = {
    title?: string;
    showTitle?: boolean;
    seriesName?: string;
    showLegend?: boolean;
    showAxes?: boolean;
    showXAxisLabels?: boolean;
    showYAxisLabels?: boolean;
    showXAxisTitle?: boolean;
    showYAxisTitle?: boolean;
    xAxisTitle?: string;
    yAxisTitle?: string;
    showDataLabels?: boolean;
    showGrid?: boolean;
    showVerticalGrid?: boolean;
    showMarkers?: boolean;
    valueFormat?: SeriesChartValueFormat;
    seriesColor?: string;
    categoryPaddingPercent?: number;
  };

  export type LineSeriesChartProps = {
    points: SeriesChartPoint[];
    options?: SeriesChartOptions | null;
    emptyMessage?: string;
    className?: string;
  };

  export function LineSeriesChart(props: LineSeriesChartProps): ReactElement;
}

declare module "@delpi/plugin-ui/styles" {}
