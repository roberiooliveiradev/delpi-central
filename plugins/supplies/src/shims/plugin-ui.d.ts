/**
 * Contratos do remote `@delpi/plugin-ui` para o tsc do MFE.
 * Runtime: Module Federation. Vitest: pluginUiTestAliases → fonte do kit.
 */
declare module "@delpi/plugin-ui/index" {
  import type { ComponentType, MouseEventHandler, ReactNode, RefObject } from "react";

  export function HelpTooltip(props: {
    content: string;
    ariaLabel?: string;
    children?: ReactNode;
    wrap?: boolean;
    placement?: "top" | "bottom";
  }): ReactNode;

  export function AnchoredPanelPortal(props: {
    open: boolean;
    anchorRef: RefObject<HTMLElement | null>;
    panelRef: RefObject<HTMLDivElement | null>;
    className?: string;
    variant?: "shape" | "bare";
    role?: string;
    "aria-label"?: string;
    preferredPlacement?: string;
    gap?: number;
    portalScopeClassName?: string;
    onDismiss?: () => void;
    children?: ReactNode;
  }): ReactNode;

  export function ContextMenuItem(props: {
    label: string;
    icon?: ComponentType<{ size?: number; strokeWidth?: number; "aria-hidden"?: boolean | "true" }>;
    onSelect?: () => void;
    disabled?: boolean;
  }): ReactNode;

  export function ActionButton(props: {
    children: ReactNode;
    variant?: "default" | "primary" | "ghost" | "link";
    onClick?: () => void;
    disabled?: boolean;
    type?: "button" | "submit";
    className?: string;
    href?: string;
    title?: string;
  }): ReactNode;

  export function createInitialsAvatar(prefix: string): ComponentType<{
    name: string;
    colorKey?: string;
    src?: string | null;
    size?: "sm" | "md" | "lg";
    href?: string;
    onNavigate?: () => void;
    className?: string;
  }>;

  export function emptyStateCardBemClasses(prefix: string): {
    root: string;
    withTitle: boolean;
  };

  export function stateBannerBemClasses(prefix: string): {
    root: string;
    error: string;
    success: string;
  };

  export function sectionCardPacBemClasses(prefix: string): Record<string, string>;
  export function sectionRouteCardBemClasses(prefix: string): Record<string, string>;
  export function catalogSearchBarBemClasses(prefix: string): Record<string, string>;

  export function createDashboardEmptyState(config: {
    classNames: { root: string; withTitle: boolean };
    defaultMessage: string;
    defaultTitle?: string;
  }): ComponentType<{
    title?: string;
    message?: string;
    children?: ReactNode;
    role?: "status" | "alert";
  }>;

  export function createDashboardStateBanner(config: {
    classNames: { root: string; error: string; success: string };
  }): ComponentType<{
    children: ReactNode;
    variant?: "default" | "error" | "success";
    className?: string;
  }>;

  export function createDashboardLoadingActivityCard(config: {
    prefix: string;
    labels: {
      remainingProgress: (remainingPercent: number) => string;
      progressAriaDeterminate: (remainingPercent: number) => string;
      progressAriaIndeterminate: string;
    };
  }): ComponentType<{
    title: string;
    description?: string;
    variant?: "panel" | "inline" | "page";
    className?: string;
  }>;

  export function createDashboardTopBar(config: { prefix: string }): ComponentType<{
    items: Array<{
      id: string;
      label: ReactNode;
      icon?: ReactNode;
      title?: string;
      count?: number;
      onSelect?: () => void;
    }>;
    activeId: string;
    "aria-label"?: string;
    collapsible?: boolean;
    collapseMode?: "rail" | "hamburger";
    collapseTrigger?: "manual" | "overflow";
    storageKey?: string;
    collapseLabel?: string;
    expandLabel?: string;
    menuLabel?: string;
    portalScopeClassName?: string;
    actions?: ReactNode;
    secondary?: ReactNode;
  }>;

  export function createDashboardTopBarSearchTrigger(config: {
    prefix: string;
  }): React.ForwardRefExoticComponent<
    {
      onOpen: () => void;
      label: string;
      shortcutLabel: string;
      "aria-label": string;
      title?: string;
      className?: string;
      expanded?: boolean;
    } & React.RefAttributes<HTMLButtonElement>
  >;

  export function createDashboardCommandPalette(config: {
    prefix: string;
    portalScopeClassName: string;
  }): ComponentType<{
    open: boolean;
    onClose: () => void;
    title: string;
    anchorRef: React.RefObject<HTMLElement | null>;
    value: string;
    onChange: (value: string) => void;
    hits?: ReadonlyArray<{ id: string; label: string; groupLabel?: string }>;
    onSelectHit: (id: string) => void;
    placeholder?: string;
    emptyHitsLabel?: string;
    "aria-label"?: string;
  }>;

  export function createDashboardPagePath(config: {
    prefix: string;
    portalScopeClassName?: string;
  }): ComponentType<{
    back: {
      label: string;
      href: string;
      onNavigate?: MouseEventHandler<HTMLAnchorElement>;
    };
    items?: Array<{ id: string; label: string; href: string }>;
    current: string;
  }>;

  export function createDashboardViewTransition(config: { prefix: string }): ComponentType<{
    transitionKey: string;
    tone?: "page" | "panel";
    children: ReactNode;
  }>;

  export function createDashboardPageHero(config: { prefix: string }): ComponentType<{
    eyebrow?: ReactNode;
    title: ReactNode;
    description?: ReactNode;
    badge?: ReactNode;
    actions?: ReactNode;
    highlights?: Array<{
      id: string;
      label: ReactNode;
      value: ReactNode;
      tone?: "neutral" | "warning" | "danger";
    }>;
    density?: "comfortable" | "compact";
    "aria-label"?: string;
    children?: ReactNode;
  }>;

  export function createDashboardSectionCard(config: {
    classNames: Record<string, string>;
    labels: {
      titleHelpAriaLabel: (title: string) => string;
      expandAriaLabel: (title: string) => string;
      collapseAriaLabel: (title: string) => string;
    };
  }): ComponentType<{
    title: string;
    subtitle?: string;
    hint?: string;
    children: ReactNode;
    actions?: ReactNode;
  }>;

  export function createDashboardSectionRouteCard(config: {
    classNames: Record<string, string>;
  }): ComponentType<{
    title: string;
    description?: string;
    hint?: string;
    icon?: ReactNode;
    routes: Array<{
      id: string;
      label: string;
      onClick: () => void;
      pinned?: boolean;
      onPinClick?: () => void;
      pinLabel?: string;
      unpinLabel?: string;
    }>;
  }>;

  export function createDashboardCatalogSearchBar(config: {
    classNames: Record<string, string>;
  }): ComponentType<{
    value: string;
    onChange: (value: string) => void;
    hits?: ReadonlyArray<{ id: string; label: string; groupLabel?: string }>;
    onSelectHit: (id: string) => void;
    placeholder?: string;
    clearLabel?: string;
    emptyHitsLabel?: string;
    "aria-label"?: string;
  }>;

  export function createDashboardHubChipRow(config: {
    prefix: string;
  }): ComponentType<{
    label: ReactNode;
    "aria-label"?: string;
    children: ReactNode;
  }>;

  export function createDashboardRouteChip(config: { prefix: string }): ComponentType<{
    label: string;
    tone?: "pinned" | "recent" | "default";
    leadingIcon?: ReactNode;
    onNavigate: () => void;
    onRemove?: () => void;
    removeLabel?: string;
  }>;

  export function createDashboardStatusBadge(config: { prefix: string }): ComponentType<{
    label: string;
    variant?: "neutral" | "info" | "success" | "warning" | "danger";
  }>;

  export type KpiCardLabels = {
    goalPrefix: string;
    iddScorePrefix: string;
    badgesStatus: string;
  };

  export type DashboardKpiCardProps = {
    title: string;
    titleHint?: string;
    value: string;
    valueVariant?: "default" | "per-unit";
    comparisonTone?: "positive" | "negative" | "warning" | null;
    contextLabel?: string;
    goalLabel?: string | null;
    goalPrefix?: string | null;
    goalHint?: string | null;
    monthlyGoalLabel?: string | null;
    monthlyGoalPrefix?: string | null;
    monthlyGoalHint?: string | null;
    periodKindBadge?: string | null;
    goalScopeBadge?: { tone?: string; label: string } | null;
    goalScopeHint?: string | null;
    goalPerformanceBadge?: {
      tone: "success" | "warning";
      statusLabel: string;
      directionLabel: string;
    } | null;
    goalPerformanceBadges?: Array<{
      tone: "success" | "warning";
      statusLabel: string;
      directionLabel: string;
    }>;
    iddScoreLabel?: string | null;
    goalVariant?: "default" | "per-unit";
    subtitle?: string;
    icon: ReactNode;
    footer?: ReactNode;
    loading?: boolean;
    className?: string;
    onClick?: () => void;
    "aria-label"?: string;
  };

  export type DashboardGoalFields = Record<string, unknown>;
  export type PerformanceDirection = "higher_is_better" | "lower_is_better";
  export function buildKpiGoalPresentation(
    contextLabel: string,
    goal?: DashboardGoalFields | null,
    formatComparable?: (value: number) => string,
    options?: Record<string, unknown>,
  ): {
    goalLabel: string | null;
    goalPrefix: string | null;
    goalHint: string | null;
    monthlyGoalLabel: string | null;
    monthlyGoalPrefix: string | null;
    monthlyGoalHint: string | null;
    goalScopeBadge: { tone?: string; label: string } | null;
    goalScopeHint: string | null;
    goalPerformanceBadge: {
      tone: "success" | "warning";
      statusLabel: string;
      directionLabel: string;
    } | null;
    iddScoreLabel: string | null;
    contextLabel: string;
  };

  /** Formata `indicators[].score` do SI para o rótulo «Nota IDD». */
  export function resolveIndicatorIddScoreLabelFromSi(
    score: number | null | undefined,
  ): string | null;

  export function createDashboardKpiCard(config: {
    prefix: string;
    labels: KpiCardLabels;
    cardModifier?: string;
  }): ComponentType<DashboardKpiCardProps>;

  export function SectionHintLabel(props: {
    label: string;
    hint: string;
    className?: string;
  }): ReactNode;

  export function createDashboardTitleWithHelp(config: {
    classNames: { root: string };
    labels: { titleHelpAriaLabel: (title: string) => string };
  }): ComponentType<{ title: string; hint?: string; className?: string }>;

  export function titleWithHelpBemClasses(prefix: string): { root: string };

  export function createFilterBarShell(config: {
    prefix: string;
    withGrid?: boolean;
    block?: string;
    embeddedByDefault?: boolean;
    defaultAriaLabel?: string;
  }): ComponentType<{
    ariaLabel?: string;
    embedded?: boolean;
    leading?: ReactNode;
    children?: ReactNode;
  }>;

  export function createDashboardFiltersKit(config: {
    prefix: string;
    portalScopeClassName?: string;
    labels?: { filtersAriaLabel?: string };
  }): {
    FiltersRow: ComponentType<{
      variant?: string;
      children?: ReactNode;
    }>;
  };

  export function selectFieldPacClasses(prefix: string): {
    field: Record<string, string>;
    control: Record<string, string>;
  };

  export function dateFieldBemClasses(prefix: string): Record<string, string>;

  export function createDashboardSelectField(config: {
    field: Record<string, string>;
    control: Record<string, string>;
    labels: Record<string, unknown>;
  }): ComponentType<{
    label: string;
    value: string;
    onChange: (value: string) => void;
    options: Array<{ value: string; label: string }>;
    allowEmpty?: boolean;
    emptyLabel?: string;
    hint?: string;
    searchable?: boolean;
    disabled?: boolean;
  }>;

  export function createDashboardTextField(config: {
    classNames: Record<string, string>;
  }): ComponentType<{
    label: string;
    value: string;
    onChange: (value: string) => void;
    hint?: string;
    placeholder?: string;
    type?: string;
    disabled?: boolean;
  }>;

  export function textFieldBemClasses(prefix: string): Record<string, string>;

  export function createDashboardDateField(config: {
    classNames: Record<string, string>;
  }): ComponentType<{
    label: string;
    value: string;
    onChange: (value: string) => void;
    hint?: string;
    type?: string;
  }>;

  export function createDashboardMultiSelectField(config: {
    prefix: string;
    portalScopeClassName?: string;
    labels: Record<string, unknown>;
  }): ComponentType<{
    label: string;
    selectedValues: string[];
    onChange: (value: string[]) => void;
    options: Array<{ value: string; label: string }>;
    emptyLabel?: string;
    searchable?: boolean;
    hint?: string;
    className?: string;
  }>;

  export function createDashboardScopeChipBar(config: {
    prefix: string;
  }): ComponentType<{
    chips: Array<{
      id: string;
      label: ReactNode;
      active?: boolean;
      onSelect?: () => void;
    }>;
    label?: ReactNode;
    className?: string;
    "aria-label"?: string;
  }>;

  export function createCompactPagination(config: {
    prefix: string;
    layout?: string;
    labels: Record<string, unknown>;
  }): ComponentType<{
    page: number;
    pageSize: number;
    total: number;
    totalPages?: number;
    pageSizeOptions?: readonly number[];
    onPageChange: (page: number) => void;
    onPageSizeChange?: (pageSize: number) => void;
    disabled?: boolean;
  }>;

  export function createDashboardDataListToolbar(config: {
    prefix: string;
  }): ComponentType<{
    actions?: ReactNode;
    leading?: ReactNode;
    hint?: ReactNode;
  }>;

  export function createDashboardTableFontSizeControls(config: {
    prefix: string;
  }): ComponentType<{
    fontSize: number;
    canIncrease: boolean;
    canDecrease: boolean;
    isDefault: boolean;
    onIncrease: () => void;
    onDecrease: () => void;
    onReset: () => void;
  }>;

  export function useTableFontSize(options: {
    storageKey: string;
    enabled?: boolean;
  }): {
    fontSize: number;
    increase: () => void;
    decrease: () => void;
    reset: () => void;
    canIncrease: boolean;
    canDecrease: boolean;
    isDefault: boolean;
  };

  export function useTableColumnVisibility(options: {
    storageKey: string;
    columns: ReadonlyArray<{ key: string; label: string }>;
    emptyFallbackKeys?: readonly string[];
  }): {
    visibility: Record<string, boolean>;
    orderedColumns: ReadonlyArray<{ key: string; label: string }>;
    visibleKeys: string[];
    setColumnVisible: (key: string, visible: boolean) => void;
    reorderColumns: (fromKey: string, toKey: string) => void;
    reset: () => void;
  };

  export const DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS: Record<string, unknown>;

  export function TableColumnVisibilityMenu(props: {
    columns: ReadonlyArray<{ key: string; label: string }>;
    visibility: Record<string, boolean>;
    onToggleColumn: (key: string, visible: boolean) => void;
    onReset: () => void;
    onReorderColumns?: (fromKey: string, toKey: string) => void;
    labels: Record<string, unknown>;
  }): ReactNode;

  export type DataTableColumn<T> = {
    key: string;
    header: string;
    render: (row: T) => ReactNode;
    sortable?: boolean;
  };

  export type DashboardDataTableProps<T> = {
    columns: Array<DataTableColumn<T>>;
    rows: T[];
    rowKey: (row: T, index: number) => string;
    emptyMessage?: string;
    loading?: boolean;
    onRowClick?: (row: T) => void;
    getRowClassName?: (row: T, index: number) => string | undefined;
    getRowProps?: (row: T, index: number) => Record<string, unknown> | undefined;
    layout?: "section" | "embedded" | "scroll";
  };

  export function DataTable<T>(
    props: DashboardDataTableProps<T> & {
      classNames: Record<string, string>;
      labels: Record<string, unknown>;
    },
  ): ReactNode;

  export function dataTableBemClasses(prefix: string): Record<string, string>;

  export function createDashboardSegmentToggle(prefix: string): ComponentType<{
    ariaLabel?: string;
    idPrefix?: string;
    size?: string;
    value: string;
    onChange: (value: string) => void;
    options: Array<{ value: string; label: string }>;
  }>;

  export const OPERATIONAL_UNIT_FIELD_LABEL: string;
  export const OPERATIONAL_UNIT_COLUMN_LABEL: string;
  export const OPERATIONAL_UNIT_OPTIONS: Array<{ value: string; label: string }>;
  export function formatOperationalUnitCode(
    code: string | null | undefined,
    fallback?: string,
  ): string;
  export function formatOperationalUnitsFilterLabel(
    branches: readonly string[],
    options?: { allSelectedCount?: number },
  ): string | null;
  export function normalizeOperationalUnitCode(value: string | null | undefined): string;

  export function ChartViewShell(props: {
    prefix?: string;
    children?: ReactNode;
    granularity?: ReactNode;
    typeToggle?: ReactNode;
    overlays?: ReactNode;
    seriesColors?: ReactNode;
    exportActions?: ReactNode;
    granularityLabel?: string;
    typeToggleLabel?: string;
    overlaysLabel?: string;
    seriesColorsLabel?: string;
  }): ReactNode;

  export function MultiTypeSeriesChart(props: {
    data: ReadonlyArray<Record<string, unknown>>;
    categoryKey: string;
    series: ReadonlyArray<{ dataKey: string; name: string; fill: string }>;
    chartType: string;
    height?: number;
    formatY?: (value: number) => string;
    formatTooltipValue?: (value: number) => string;
    showLegend?: boolean;
  }): ReactNode;

  export function ChartTypeSegmentToggle(props: Record<string, unknown>): ReactNode;
  export function ChartOverlayOptionsPopover(props: Record<string, unknown>): ReactNode;
  export function ChartSeriesColorsPopover(props: Record<string, unknown>): ReactNode;
  export function applySeriesFillPreferences(
    series: ReadonlyArray<{ dataKey: string; name: string; fill: string }>,
    fills?: Record<string, string>,
  ): Array<{ dataKey: string; name: string; fill: string }>;
  export function useChartGranularitySelection(
    dateStart?: string,
    dateEnd?: string,
    options?: { resolveAutoGranularity?: (suggested: string) => string },
  ): { granularity: string; setGranularity: (value: string) => void };
  export function usePersistedChartPreferences(config: Record<string, unknown>): {
    preferences: {
      chartType?: string;
      comparePriorYear?: boolean;
      seriesFills?: Record<string, string>;
    };
    setPreferences: (
      next:
        | Record<string, unknown>
        | ((prev: Record<string, unknown>) => Record<string, unknown>),
    ) => void;
    setChartType: (value: string) => void;
  };
  export const TIME_MULTI_SERIES_TYPES: readonly string[];
  export const PERIOD_COMPARE_TYPES: readonly string[];
  export type ChartGranularity = string;
  export type ChartOverlayOption = Record<string, unknown>;
  export type MultiTypeSeriesSpec = { dataKey: string; name: string; fill: string };
  export function runTabularExport(input: Record<string, unknown>): void;
  export function createDashboardChartToolbarKit(config: {
    prefix: string;
    labels: Record<string, unknown>;
  }): {
    ChartToolbar: ComponentType<Record<string, unknown>>;
    ChartGranularityToggle: ComponentType<{
      value: string;
      onChange: (value: string) => void;
      options: Array<{ value: string; label: string }>;
      modes?: string[];
      idPrefix?: string;
    }>;
  };
  export function createDashboardTabularExportButtons(config: {
    prefix: string;
    groupAriaLabel?: string;
  }): ComponentType<{
    compact?: boolean;
    disabled?: boolean;
    onExport: (format: string) => void;
  }>;
  export type SpeedometerGaugeProps = {
    prefix?: string;
    size?: number;
    value?: number | null;
    goal?: number | null;
    showZonesLegend?: boolean;
    tip?: string;
  };
  export function SpeedometerGauge(props: SpeedometerGaugeProps): ReactNode;
}

declare module "@delpi/plugin-ui/styles";
