/**
 * Contratos mínimos do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote real.
 */
declare module "@delpi/plugin-ui/index" {
  import type { ComponentType, InputHTMLAttributes, ReactElement, ReactNode } from "react";

  export type StatusBadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

  export type DashboardStatusBadgeProps = {
    label: string;
    variant?: StatusBadgeVariant;
    className?: string;
  };

  export function createDashboardStatusBadge(config: {
    prefix: string;
  }): ComponentType<DashboardStatusBadgeProps>;

  export type StateBannerVariant = "default" | "error" | "success";

  export type DashboardStateBannerProps = {
    children: ReactNode;
    variant?: StateBannerVariant;
    className?: string;
  };

  export function createDashboardStateBanner(config: {
    classNames: Record<string, string>;
  }): ComponentType<DashboardStateBannerProps>;

  export function stateBannerBemClasses(prefix: string): Record<string, string>;

  export type PageHeaderLayout = "brand" | "titleRow" | "stack" | "hero";

  export type PageHeaderMetaItem = {
    icon?: ReactNode;
    label: ReactNode;
  };

  export type PageHeaderProps = {
    layout: PageHeaderLayout;
    title: ReactNode;
    subtitle?: ReactNode;
    eyebrow?: ReactNode;
    icon?: ReactNode;
    onRefresh?: () => void;
    refreshing?: boolean;
    metaItems?: readonly PageHeaderMetaItem[];
    classNames: Record<string, string | undefined>;
    labels: { refresh: string; refreshing: string };
  };

  export function PageHeader(props: PageHeaderProps): ReactElement;

  export type DashboardPageHeaderProps = Omit<PageHeaderProps, "classNames" | "labels" | "layout">;

  export function createDashboardPageHeader(config: {
    layout: PageHeaderLayout;
    classNames: Record<string, string | undefined>;
    labels: { refresh: string; refreshing: string };
  }): ComponentType<DashboardPageHeaderProps>;

  export function pageHeaderTitleRowBemClasses(
    prefix: string,
    options?: { buttonClass?: string; spinClass?: string },
  ): Record<string, string | undefined>;

  export function pageHeaderHeroBemClasses(prefix: string): Record<string, string | undefined>;

  export type DashboardSectionCardProps = {
    title: string;
    children?: ReactNode;
  };

  export function createDashboardSectionCard(config: {
    classNames: Record<string, string>;
    labels: { titleHelpAriaLabel: (title: string) => string };
  }): ComponentType<DashboardSectionCardProps>;

  export function sectionCardPacBemClasses(prefix: string): Record<string, string>;

  export type DashboardEmptyStateProps = {
    title?: string;
    message?: string;
    children?: ReactNode;
  };

  export function createDashboardEmptyState(config: {
    classNames: Record<string, string>;
    defaultMessage: string;
  }): ComponentType<DashboardEmptyStateProps>;

  export function emptyStateCardBemClasses(prefix: string): Record<string, string>;

  export type DashboardLoadingStateProps = {
    message?: string;
  };

  export function createDashboardLoadingState(config: {
    classNames: Record<string, string>;
    defaultMessage: string;
  }): ComponentType<DashboardLoadingStateProps>;

  export function loadingStateCardBemClasses(prefix: string): Record<string, string>;

  export type TimelineItemModel = {
    id: string;
    title: ReactNode;
    occurredAt?: string | null;
    timeLabel?: ReactNode;
    detail?: ReactNode;
  };

  export type DashboardTimelineProps = {
    items: TimelineItemModel[];
  };

  export function createTimeline(config: { prefix: string }): ComponentType<DashboardTimelineProps>;

  export type DashboardDrawerShellProps = {
    open: boolean;
    title: string;
    description?: string;
    onClose: () => void;
    children: ReactNode;
  };

  export function createHostContainedDrawerShell(config: {
    prefix: string;
    portalScopeClassName: string;
  }): ComponentType<DashboardDrawerShellProps>;

  export type DashboardModalShellProps = {
    open: boolean;
    title: string;
    description?: string;
    onClose: () => void;
    children: ReactNode;
  };

  export function createHostContainedModalShell(config: {
    prefix: string;
    portalScopeClassName: string;
    containedLayout?: "fill" | "dialog";
    variant?: "default" | "wide" | "page";
  }): ComponentType<DashboardModalShellProps>;

  export type FilterInputFieldProps = {
    label: string;
    type: Extract<InputHTMLAttributes<HTMLInputElement>["type"], "month" | "date" | "text" | "search">;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    disabled?: boolean;
  };

  export type FilterSelectOption = { value: string; label: string };

  export type FilterSelectFieldProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    options: readonly FilterSelectOption[];
    disabled?: boolean;
  };

  export type DashboardFiltersKit = {
    FiltersRow: ComponentType<{ children?: ReactNode; trailing?: ReactNode }>;
    FilterInputField: ComponentType<FilterInputFieldProps>;
    FilterSelectField: ComponentType<FilterSelectFieldProps>;
  };

  export function createDashboardFiltersKit(config: {
    prefix: string;
    labels: { filtersAriaLabel: string };
    portalScopeClassName?: string;
  }): DashboardFiltersKit;

  export type MultiSelectOption = { value: string; label: string };

  export type MultiSelectFieldLabels = {
    emptyLabel: string;
    searchPlaceholder: string;
    selectVisible: string;
    clear: string;
    emptyOptions: string;
    multipleSelected: (count: number) => string;
    createOption?: (query: string) => string;
    searchAriaLabel?: (label: string) => string;
    selectedCountLabel?: (count: number) => string;
    emptyOptionsCreatable?: string;
    removeTagAriaLabel?: (value: string) => string;
  };

  export type DashboardMultiSelectFieldProps = {
    label: string;
    selectedValues: string[];
    options?: readonly MultiSelectOption[];
    onChange: (values: string[]) => void;
    disabled?: boolean;
    searchable?: boolean;
    showBulkActions?: boolean;
    emptyLabel?: string;
    hint?: string;
    placeholder?: string;
  };

  export type DashboardCreatableMultiSelectFieldProps = Omit<
    DashboardMultiSelectFieldProps,
    "searchable" | "showBulkActions"
  >;

  export function multiSelectBemClasses(prefix: string): Record<string, string>;
  export function multiSelectCreatablePacClasses(prefix: string): Record<string, string>;

  export function createDashboardMultiSelectField(config: {
    prefix?: string;
    classNames?: Record<string, string>;
    labels: MultiSelectFieldLabels;
    portalScopeClassName?: string;
  }): ComponentType<DashboardMultiSelectFieldProps>;

  export function createDashboardCreatableMultiSelectField(config: {
    prefix?: string;
    classNames?: Record<string, string>;
    labels: MultiSelectFieldLabels;
    portalScopeClassName?: string;
  }): ComponentType<DashboardCreatableMultiSelectFieldProps>;

  export type DataTableColumn<T> = {
    key: string;
    header: string;
    render: (row: T) => ReactNode;
  };

  export type DataTableProps<T> = {
    columns: DataTableColumn<T>[];
    rows: T[];
    rowKey: (row: T, index: number) => string;
    loading?: boolean;
    onRowClick?: (row: T) => void;
    layout?: "section" | "embedded" | "scroll";
    classNames: Record<string, string>;
    labels: Record<string, string | ((header: string) => string)>;
  };

  export function DataTable<T>(props: DataTableProps<T>): ReactElement;

  export function dataTableBemClasses(prefix: string): Record<string, string>;
  export function dataTableSectionBemClasses(prefix: string): { section: string };

  export type CompactPaginationLabels = {
    info: (args: {
      page: number;
      totalPages: number;
      total: number;
      pageSize: number;
    }) => string;
    pageSizeLabel?: string;
    previous: string;
    next: string;
    navigationAriaLabel: string;
  };

  export type CompactPaginationProps = {
    page: number;
    pageSize: number;
    total: number;
    totalPages?: number;
    onPageChange: (page: number) => void;
    disabled?: boolean;
    layout?: "grouped" | "flat";
    classNames: Record<string, string>;
    labels: CompactPaginationLabels;
  };

  export function CompactPagination(props: CompactPaginationProps): ReactElement;

  export function compactPaginationBemClasses(
    prefix: string,
    options?: { ghostBtn?: string },
  ): Record<string, string>;

  export type DirectoryUserOption = {
    id: string;
    name: string;
    email: string;
  };

  export type UserDirectoryPickerProps = {
    value: DirectoryUserOption[];
    onChange: (users: DirectoryUserOption[]) => void;
    searchUsers: (
      query: string,
      limit?: number,
      signal?: AbortSignal,
    ) => Promise<DirectoryUserOption[]>;
    disabled?: boolean;
    showSelectedList?: boolean;
    showEmail?: boolean;
    maxSelected?: number;
    labels?: {
      title?: string;
      hint?: string;
      placeholder?: string;
    };
    className?: string;
  };

  export function UserDirectoryPicker(props: UserDirectoryPickerProps): ReactElement;
}

declare module "@delpi/plugin-ui/styles" {}
