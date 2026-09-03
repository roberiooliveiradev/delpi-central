/**
 * Contratos tipados do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote real.
 * Em vitest: alias `pluginUiTestAliases` aponta para o fonte do kit.
 */
declare module "@delpi/plugin-ui/index" {
  import type {
    ComponentType,
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

  export function statusBadgeBemClasses(prefix: string): Record<string, string>;

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

  export type DashboardSectionCardProps = {
    title: string;
    subtitle?: string;
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

  export type FormActionsAlign = "start" | "end";

  export type FormActionsClassNames = {
    root: string;
    alignEndModifier: string;
  };

  export type DashboardFormActionsProps = {
    children: ReactNode;
    align?: FormActionsAlign;
    className?: string;
  };

  export function createDashboardFormActions(config: {
    classNames: FormActionsClassNames;
  }): ComponentType<DashboardFormActionsProps>;

  export function formActionsBemClasses(prefix: string): FormActionsClassNames;

  export type ActionButtonVariant = "default" | "primary" | "ghost" | "link";

  export type ActionButtonProps = {
    children: ReactNode;
    variant?: ActionButtonVariant;
    disabled?: boolean;
    className?: string;
    "aria-label"?: string;
    title?: string;
    type?: "button" | "submit";
    href?: string;
    onClick?: () => void;
  };

  export function ActionButton(props: ActionButtonProps): ReactElement;

  export type FieldLabelProps = {
    label: string;
    hint?: string;
    htmlFor?: string;
    className?: string;
  };

  export function FieldLabel(props: FieldLabelProps): ReactElement;

  export type NativeTextAreaControlProps = {
    value: string;
    onChange?: (value: string) => void;
    onChangeEvent?: InputHTMLAttributes<HTMLTextAreaElement>["onChange"];
    className?: string;
    rows?: number;
    disabled?: boolean;
    id?: string;
    placeholder?: string;
  };

  export function NativeTextAreaControl(props: NativeTextAreaControlProps): ReactElement;

  export type NativeCheckboxControlProps = {
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
    id?: string;
    className?: string;
    "aria-label"?: string;
  };

  export function NativeCheckboxControl(props: NativeCheckboxControlProps): ReactElement;

  export type TextFieldClassNames = Record<string, string>;

  export type DashboardTextFieldProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    hint?: string;
    placeholder?: string;
    disabled?: boolean;
    type?: string;
    id?: string;
  };

  export function createDashboardTextField(config: {
    classNames: TextFieldClassNames;
  }): ComponentType<DashboardTextFieldProps>;

  export function textFieldPacClasses(prefix: string): TextFieldClassNames;
  export function textFieldBemClasses(prefix: string): TextFieldClassNames;

  export type SelectFieldOption = { value: string; label: string };

  export type SelectFieldClassNames = Record<string, string>;
  export type SelectControlClassNames = Record<string, string>;

  export type SelectFieldLabels = {
    placeholder: string;
    emptyLabel: string;
    control: {
      searchPlaceholder: string;
      emptyOptions: string;
      searchAriaLabel: (label?: string) => string;
    };
  };

  export type DashboardSelectFieldProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    options: readonly SelectFieldOption[];
    hint?: string;
    disabled?: boolean;
    searchable?: boolean;
  };

  export function createDashboardSelectField(config: {
    field: SelectFieldClassNames;
    control: SelectControlClassNames;
    labels: SelectFieldLabels;
  }): ComponentType<DashboardSelectFieldProps>;

  export function selectFieldPacClasses(prefix: string): {
    field: SelectFieldClassNames;
    control: SelectControlClassNames;
  };

  export type SegmentToggleOption<T extends string = string> = {
    value: T;
    label: ReactNode;
    ariaLabel?: string;
    disabled?: boolean;
  };

  export type DashboardSegmentToggleProps<T extends string = string> = {
    options: readonly SegmentToggleOption<T>[];
    value: T;
    onChange: (value: T) => void;
    ariaLabel: string;
    disabled?: boolean;
  };

  export function createDashboardSegmentToggle(
    prefix: string,
  ): <T extends string>(props: DashboardSegmentToggleProps<T>) => ReactElement;

  export type DetailField = {
    label: string;
    hint?: string;
    value: ReactNode;
    wide?: boolean;
  };

  export type DashboardDetailFieldGridProps = {
    fields: DetailField[];
  };

  export function createDashboardDetailFieldGrid(config: {
    prefix: string;
    labels: { fieldHelpAriaLabel: (label: string) => string };
    valueFallback?: string;
    wrapLabels?: boolean;
  }): ComponentType<DashboardDetailFieldGridProps>;

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
}

declare module "@delpi/plugin-ui/styles" {}
