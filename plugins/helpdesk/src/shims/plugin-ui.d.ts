/**
 * Contratos tipados do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote real.
 * Em vitest: alias `pluginUiTestAliases` aponta para o fonte do kit.
 */
declare module "@delpi/plugin-ui/index" {
  import type {
    ComponentType,
    ForwardRefExoticComponent,
    FormEvent,
    HTMLAttributes,
    MouseEvent,
    InputHTMLAttributes,
    ReactElement,
    ReactNode,
    RefAttributes,
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
    nav?: ReactNode;
    actions?: ReactNode;
    onRefresh?: () => void;
    refreshing?: boolean;
    compact?: boolean;
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
    hint?: string;
    children?: ReactNode;
    actions?: ReactNode;
    className?: string;
    fill?: boolean;
  };

  export function createDashboardSectionCard(config: {
    classNames: Record<string, string>;
    labels: { titleHelpAriaLabel: (title: string) => string };
  }): ComponentType<DashboardSectionCardProps>;

  export function sectionCardPacBemClasses(prefix: string): Record<string, string>;

  export type ProgressTrackerStepState =
    | "complete"
    | "current"
    | "available"
    | "locked"
    | "error";

  export type ProgressTrackerDensity = "default" | "compact";

  export type ProgressTrackerStep = {
    id: string;
    label: string;
    state: ProgressTrackerStepState;
    statusLabel?: string;
  };

  export type DashboardProgressTrackerProps = {
    steps: ProgressTrackerStep[];
    currentStepId: string;
    interactive?: boolean;
    onStepChange?: (stepId: string) => void;
    ariaLabel?: string;
    density?: ProgressTrackerDensity;
    compactSummary?: string;
    className?: string;
  };

  export function createDashboardProgressTracker(config: {
    prefix: string;
  }): ComponentType<DashboardProgressTrackerProps>;

  export type DashboardJourneyProgressBarProps = {
    value: number;
    label?: string;
    summary?: string;
    ariaLabel?: string;
    className?: string;
  };

  export function createDashboardJourneyProgressBar(config?: {
    prefix?: string;
    defaultLabel?: string;
  }): ComponentType<DashboardJourneyProgressBarProps>;

  export type NavigationCardDensity = "default" | "featured";

  export type NavigationCardClassNames = {
    root: string;
    rootHorizontal: string;
    rootFeatured: string;
    rootFeaturedHorizontal: string;
    icon: string;
    body: string;
    eyebrow: string;
    title: string;
    description: string;
    meta: string;
  };

  export type DashboardNavigationCardProps = {
    title: string;
    onClick: () => void;
    icon?: ReactNode;
    eyebrow?: string;
    description?: string;
    meta?: string;
    disabled?: boolean;
    orientation?: "vertical" | "horizontal";
    density?: NavigationCardDensity;
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardNavigationCard(config: {
    classNames: NavigationCardClassNames;
  }): ComponentType<DashboardNavigationCardProps>;

  export function navigationCardBemClasses(prefix: string): NavigationCardClassNames;

  export type UnderlineNavItem = {
    id: string;
    label: ReactNode;
    icon?: ReactNode;
    count?: number;
    title?: string;
    controlId?: string;
    tabId?: string;
    onSelect?: () => void;
  };

  export type TopBarCollapseMode = "rail" | "hamburger";
  export type TopBarCollapseTrigger = "manual" | "overflow";

  export type DashboardTopBarProps = {
    items: UnderlineNavItem[];
    activeId: string;
    secondary?: ReactNode;
    actions?: ReactNode;
    bleed?: boolean;
    sticky?: boolean;
    surface?: boolean;
    collapsible?: boolean;
    collapseMode?: TopBarCollapseMode;
    collapseTrigger?: TopBarCollapseTrigger;
    storageKey?: string;
    collapsed?: boolean;
    defaultCollapsed?: boolean;
    onCollapsedChange?: (collapsed: boolean) => void;
    collapseLabel?: string;
    expandLabel?: string;
    menuLabel?: string;
    portalScopeClassName?: string;
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardTopBar(config: {
    prefix: string;
  }): ComponentType<DashboardTopBarProps>;

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

  export type DashboardLoadingActivityCardProps = {
    title?: string;
    description?: string;
    variant?: "panel" | "inline" | "badge";
    className?: string;
  };

  export function createDashboardLoadingActivityCard(config: {
    prefix: string;
    labels?: {
      progressRemaining?: (remainingPercent: number) => string;
      progressAriaDeterminate?: (remainingPercent: number) => string;
      progressAriaIndeterminate?: string;
    };
  }): ComponentType<DashboardLoadingActivityCardProps>;

  export type PageHeroDensity = "comfortable" | "compact";

  export type DashboardPageHeroProps = {
    eyebrow?: ReactNode;
    title: ReactNode;
    description?: ReactNode;
    badge?: ReactNode;
    actions?: ReactNode;
    highlights?: readonly {
      id: string;
      label: ReactNode;
      value: ReactNode;
      description?: ReactNode;
      tone?: "neutral" | "warning" | "danger";
      loading?: boolean;
    }[];
    children?: ReactNode;
    density?: PageHeroDensity;
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardPageHero(config: {
    prefix: string;
  }): ComponentType<DashboardPageHeroProps>;

  export type ScopeChip = {
    id: string;
    label: ReactNode;
    active?: boolean;
    onSelect?: () => void;
  };

  export type DashboardScopeChipBarProps = {
    chips: ScopeChip[];
    label?: ReactNode;
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardScopeChipBar(config: {
    prefix: string;
  }): ComponentType<DashboardScopeChipBarProps>;

  export type DashboardFilterBarShellProps = {
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
    block?: string;
    forceRootOnly?: boolean;
  }): ComponentType<DashboardFilterBarShellProps>;

  export type DashboardDrawerShellProps = {
    open: boolean;
    title: string;
    description?: string;
    footer?: ReactNode;
    onClose: () => void;
    children: ReactNode;
    closeAriaLabel?: string;
    backdropAriaLabel?: string;
    closeOnBackdropClick?: boolean;
  };

  export function createHostContainedDrawerShell(config: {
    prefix: string;
    portalScopeClassName: string;
    closeAriaLabel?: string;
    backdropAriaLabel?: string;
    closeOnBackdropClick?: boolean;
  }): ComponentType<DashboardDrawerShellProps>;

  export type SectionHintLabelProps = {
    label: ReactNode;
    hint?: string;
    className?: string;
  };

  export function SectionHintLabel(props: SectionHintLabelProps): ReactElement;

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

  export type IconButtonTone = "default" | "danger" | "primary";

  export type IconButtonProps = {
    children: ReactNode;
    "aria-label": string;
    tone?: IconButtonTone;
    type?: "button" | "submit";
    disabled?: boolean;
    onClick?: () => void;
  };

  export function IconButton(props: IconButtonProps): ReactElement;

  export type FilePreviewModalProps = {
    open: boolean;
    title: string;
    onClose: () => void;
    source?: File | Blob | (() => Promise<Blob>) | string | null;
    mimeType?: string | null;
    fileName?: string | null;
    metaItems?: Array<string | null | undefined>;
    headerActions?: ReactNode;
    portalScopeClassName?: string;
    containInHost?: boolean;
    enabled?: boolean;
  };

  export function FilePreviewModal(props: FilePreviewModalProps): ReactElement;

  export type FilePreviewKind = "image" | "pdf" | "text" | "docx" | "spreadsheet" | "none";

  export function resolveFilePreviewKind(input: {
    mimeType?: string | null;
    fileName?: string | null;
    declaredType?: string | null;
  }): FilePreviewKind;

  export type FieldLabelProps = {
    label: string;
    hint?: string;
    htmlFor?: string;
    className?: string;
    icon?: ReactNode;
  };

  export function FieldLabel(props: FieldLabelProps): ReactElement;

  export type RichTextEditorMode = "edit" | "preview";

  export type RichTextInlineImageInsert = {
    src: string;
    alt?: string;
    pendingId?: string;
    documentId?: number | string;
    attachmentHref?: string;
  };

  export type RichTextPasteImagesHandler = (
    files: File[],
  ) =>
    | void
    | Promise<void>
    | RichTextInlineImageInsert[]
    | Promise<RichTextInlineImageInsert[]>;

  export type RichTextEditorHandle = {
    insertInlineImages: (items: readonly RichTextInlineImageInsert[]) => void;
  };

  export type MentionMenuHit = {
    id: string;
    kind: string;
    label: string;
    subtitle?: string;
    groupLabel?: string;
    avatarSrc?: string | null;
    avatarName?: string | null;
  };

  export type RichTextMentionLabels = {
    listAriaLabel: string;
    emptyLabel: string;
  };

  export type RichTextEditorProps = {
    value: string;
    onChange: (next: string) => void;
    mode?: RichTextEditorMode;
    disabled?: boolean;
    className?: string;
    ariaLabel?: string;
    portalScopeClassName?: string;
    minHeight?: number;
    fill?: boolean;
    resolveAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
    persistAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
    onPasteImages?: RichTextPasteImagesHandler;
    onPasteImagesError?: (error: unknown) => void;
    mentionHits?: readonly MentionMenuHit[];
    onMentionQueryChange?: (query: string | null) => void;
    mentionLabels?: RichTextMentionLabels;
  };

  export const RichTextEditor: ForwardRefExoticComponent<
    RichTextEditorProps & RefAttributes<RichTextEditorHandle>
  >;


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
    label?: ReactNode;
    children?: ReactNode;
    hint?: ReactNode;
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
    required?: boolean;
    type?: string;
    id?: string;
    icon?: ReactNode;
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
    required?: boolean;
    disabled?: boolean;
    searchable?: boolean;
    icon?: ReactNode;
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
    idPrefix?: string;
    disabled?: boolean;
    size?: "sm" | "md";
    widthMode?: "fill" | "content";
    direction?: "row" | "column";
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
    headerHint?: string;
    render: (row: T) => ReactNode;
    sortable?: boolean;
    className?: string;
    interactive?: boolean;
    rowClick?: "stop" | "propagate";
  };

  export type DataTableProps<T> = {
    columns: DataTableColumn<T>[];
    rows: T[];
    rowKey: (row: T, index: number) => string;
    loading?: boolean;
    onRowClick?: (row: T) => void;
    getRowClassName?: (row: T, index: number) => string | undefined;
    getRowProps?: (row: T, index: number) => HTMLAttributes<HTMLTableRowElement> | undefined;
    layout?: "section" | "embedded" | "scroll";
    compact?: boolean;
    sortKey?: string | null;
    sortDirection?: "asc" | "desc";
    onSortChange?: (columnKey: string) => void;
    emptyMessage?: string;
    classNames: Record<string, string>;
    labels: {
      emptyMessage: string;
      loadingMessage: string;
      sortByAriaLabel: (header: string) => string;
      headerHelpAriaLabel: (header: string) => string;
    };
  };

  export function DataTable<T>(props: DataTableProps<T>): ReactElement;

  export function dataTableBemClasses(prefix: string): Record<string, string>;

  export type FilterInputFieldProps = {
    label: string;
    hint?: string;
    type: Extract<InputHTMLAttributes<HTMLInputElement>["type"], "month" | "date" | "text" | "search">;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    disabled?: boolean;
  };

  export type FilterSelectOption = { value: string; label: string };

  export type FilterSelectFieldProps = {
    label: string;
    hint?: string;
    value: string;
    onChange: (value: string) => void;
    options: readonly FilterSelectOption[];
    disabled?: boolean;
  };

  export type DashboardFiltersKit = {
    FiltersRow: ComponentType<{
      children?: ReactNode;
      trailing?: ReactNode;
      variant?: "default" | "extended";
      compact?: boolean;
    }>;
    FilterInputField: ComponentType<FilterInputFieldProps>;
    FilterSelectField: ComponentType<FilterSelectFieldProps>;
  };

  export function createDashboardFiltersKit(config: {
    prefix: string;
    labels: { filtersAriaLabel: string };
    portalScopeClassName?: string;
  }): DashboardFiltersKit;

  export type CompactPaginationLabels = {
    info: (args: {
      page: number;
      totalPages: number;
      total: number;
      pageSize: number;
    }) => string;
    pageSizeLabel?: string;
    previous: ReactNode;
    next: ReactNode;
    previousAriaLabel?: string;
    nextAriaLabel?: string;
    navigationAriaLabel: string;
  };

  export type DashboardCompactPaginationProps = {
    page: number;
    pageSize: number;
    total: number;
    totalPages?: number;
    pageSizeOptions?: readonly number[];
    onPageChange: (page: number) => void;
    onPageSizeChange?: (pageSize: number) => void;
    disabled?: boolean;
    hideWhenSinglePage?: boolean;
  };

  export function createCompactPagination(config: {
    prefix: string;
    labels: CompactPaginationLabels;
    layout?: "grouped" | "flat";
    ghostBtn?: string;
    withHints?: boolean;
  }): ComponentType<DashboardCompactPaginationProps>;

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
    labels: {
      navigationAriaLabel: string;
      pagesAriaLabel: string;
      previous: string;
      next: string;
      info: (args: {
        rangeStart: number;
        rangeEnd: number;
        total: number;
        page: number;
        totalPages: number;
      }) => string;
      jumpLabel: string;
      jumpInputAriaLabel: string;
      jumpError: (reason: PageJumpValidationReason, totalPages: number) => string;
    };
    tablePageSizeLabels: { label: string; selectAriaLabel: string };
    hints?: {
      pageSize?: string;
      previous?: string;
      next?: string;
      info?: string;
      jump?: string;
    };
  }): {
    Pagination: ComponentType<PaginationInjectedProps>;
    TablePageSizeSelect: ComponentType<TablePageSizeSelectInjectedProps>;
  };

  export type DashboardDataCardsGridProps = {
    children?: ReactNode;
    empty?: ReactNode;
    ariaLabel?: string;
    className?: string;
  };

  export function createDashboardDataCardsGrid(config: {
    prefix: string;
  }): ComponentType<DashboardDataCardsGridProps>;

  export function usePersistedViewLayout(options: {
    storageKey: string;
    defaultMode?: "table" | "cards" | "board";
    mobileMaxWidthPx?: number;
    enabled?: boolean;
  }): {
    layout: "table" | "cards" | "board";
    setLayout: (layout: "table" | "cards" | "board") => void;
  };

  export type DashboardModalShellProps = {
    open: boolean;
    title: string;
    description?: string;
    footer?: ReactNode;
    onClose: () => void;
    children: ReactNode;
    closeAriaLabel?: string;
  };

  export function createHostContainedModalShell(config: {
    prefix: string;
    portalScopeClassName: string;
    containedLayout?: "fill" | "dialog";
    variant?: "default" | "wide" | "page";
  }): ComponentType<DashboardModalShellProps>;

  export type FileDropzoneClassNames = Record<string, string>;
  export type FileDropzoneLabels = { title: string; hint: string };
  export type DashboardFileDropzoneProps = {
    disabled?: boolean;
    busy?: boolean;
    multiple?: boolean;
    accept?: string;
    onFilesSelected: (files: File[]) => void;
    labels?: Partial<FileDropzoneLabels>;
    fieldLabel?: string;
    ariaLabel?: string;
  };

  export function fileDropzoneBemClasses(
    prefix: string,
    block?: string,
  ): FileDropzoneClassNames;

  export function createDashboardFileDropzone(config: {
    classNames: FileDropzoneClassNames;
    labels: FileDropzoneLabels;
  }): ComponentType<DashboardFileDropzoneProps>;

  export const CONVERSATION_FILE_DROP_MAX_BYTES: number;

  export type ConversationFileDropLayerClassNames = {
    root: string;
    overlay: string;
  };

  export type ConversationFileDropLayerProps = {
    children: ReactNode;
    classNames: ConversationFileDropLayerClassNames;
    overlayLabel: string;
    onFiles: (files: File[]) => void;
    disabled?: boolean;
    maxBytes?: number;
    accept?: string;
    className?: string;
  };

  export type DashboardConversationFileDropLayerProps = Omit<
    ConversationFileDropLayerProps,
    "classNames"
  >;

  export function conversationFileDropLayerBemClasses(
    prefix: string,
  ): ConversationFileDropLayerClassNames;

  export function ConversationFileDropLayer(
    props: ConversationFileDropLayerProps,
  ): ReactElement;

  export function createDashboardConversationFileDropLayer(
    prefix: string,
  ): ComponentType<DashboardConversationFileDropLayerProps>;

  export type AttachmentPreviewStripMode = "preview" | "manage";
  export type AttachmentPreviewStripItem = {
    id: string;
    fileName: string;
    contentType?: string | null;
    previewUrl?: string | null;
    detail?: string;
    busy?: boolean;
  };
  export type AttachmentPreviewStripClassNames = Record<string, string>;
  export type AttachmentPreviewStripLabels = {
    empty: string;
    openAriaLabel: (fileName: string) => string;
    removeAriaLabel: (fileName: string) => string;
  };
  export type DashboardAttachmentPreviewStripProps = {
    items: AttachmentPreviewStripItem[];
    onOpen: (item: AttachmentPreviewStripItem) => void;
    mode?: AttachmentPreviewStripMode;
    onRemove?: (item: AttachmentPreviewStripItem) => void;
    heading?: ReactNode;
    emptyMessage?: string;
    className?: string;
    labels?: Partial<AttachmentPreviewStripLabels>;
  };

  export function attachmentPreviewStripBemClasses(
    prefix: string,
  ): AttachmentPreviewStripClassNames;

  export function createDashboardAttachmentPreviewStrip(config: {
    classNames: AttachmentPreviewStripClassNames;
    labels: AttachmentPreviewStripLabels;
  }): ComponentType<DashboardAttachmentPreviewStripProps>;

  export type EntityDirectoryOption = {
    id: string;
    label: string;
    secondary?: string;
  };

  export type EntityDirectoryPickerProps = {
    value: EntityDirectoryOption[];
    onChange: (entities: EntityDirectoryOption[]) => void;
    searchEntities: (
      query: string,
      limit?: number,
      signal?: AbortSignal,
    ) => Promise<EntityDirectoryOption[]>;
    disabled?: boolean;
    showSelectedList?: boolean;
    maxSelected?: number;
    renderOptionLeading?: (entity: EntityDirectoryOption) => ReactNode;
    renderSelectedChip?: (args: {
      entity: EntityDirectoryOption;
      label: string;
      disabled: boolean;
      onRemove: () => void;
    }) => ReactNode;
    labels?: {
      title?: string;
      hint?: string;
      placeholder?: string;
      searching?: string;
      empty?: string;
    emptySelected?: string;
    selectedAriaLabel?: string;
    };
    onSearchingChange?: (searching: boolean) => void;
    className?: string;
  };

  export function EntityDirectoryPicker(props: EntityDirectoryPickerProps): ReactElement;

  export function entityDirectoryLabel(entity: EntityDirectoryOption): string;

  export type DirectoryUserOption = {
    id: string;
    name: string;
    email: string;
    directoryUserId?: string;
    hasPhoto?: boolean;
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
    renderOptionLeading?: (user: DirectoryUserOption) => ReactNode;
    renderSelectedChip?: (args: {
      user: DirectoryUserOption;
      label: string;
      disabled: boolean;
      onRemove: () => void;
    }) => ReactNode;
    labels?: {
      title?: string;
      hint?: string;
      placeholder?: string;
      searching?: string;
      empty?: string;
    };
    onSearchingChange?: (searching: boolean) => void;
    className?: string;
  };

  export function UserDirectoryPicker(props: UserDirectoryPickerProps): ReactElement;

  export type InitialsAvatarSize = "sm" | "md" | "lg";

  export type DashboardInitialsAvatarProps = {
    name: string;
    colorKey?: string;
    src?: string | null;
    alt?: string;
    size?: InitialsAvatarSize;
    className?: string;
    previewable?: boolean;
    previewTitle?: string;
    previewAriaLabel?: string;
  };

  export function createInitialsAvatar(
    prefix: string,
  ): ComponentType<DashboardInitialsAvatarProps>;

  export type HintActionProps = {
    hint: string;
    ariaLabel: string;
    placement?: "top" | "bottom";
    suppressed?: boolean;
    children: ReactElement;
  };

  export function HintAction(props: HintActionProps): ReactNode;

  export type MessageThreadItem = {
    id: string;
    kind: string;
    bodyText: string;
    bodyHtml?: string | null;
    createdAtLabel: string;
    authorName?: string | null;
    authorUserId?: string | null;
    authorSrc?: string | null;
    mine?: boolean;
    headingText?: string | null;
    belowBody?: ReactNode;
  };

  export type MessageThreadAction = {
    id: string;
    label: string;
    onClick: () => void;
    danger?: boolean;
    title?: string;
  };

  export type DashboardMessageThreadProps = {
    messages: readonly MessageThreadItem[];
    listAriaLabel: string;
    emptyLabel: string;
    bodyMode?: "markdown" | "plain" | "html";
    showMineIdentity?: boolean;
    emptyContent?: ReactNode;
    portalScopeClassName?: string;
    className?: string;
    fill?: boolean;
    resolveAttachmentImageSrc?: (
      attachmentId: string,
    ) => string | null | undefined;
    onAttachmentImageClick?: (attachmentId: string) => void;
    resolveActions?: (message: MessageThreadItem) => MessageThreadAction[];
  };

  export function rewriteInlinePendingInMarkdown(
    bodyText: string,
    pendingToUuid: Record<string, string>,
  ): string;

  export function listInlinePendingIdsFromMarkdown(bodyText: string): string[];

  export function listInlineAttachmentIdsFromMarkdown(bodyText: string): string[];

  export function createDashboardMessageThread(
    prefix: string,
  ): ComponentType<DashboardMessageThreadProps>;

  export type MentionComposerLabels = {
    placeholder: string;
    sendAriaLabel: string;
    attachAriaLabel: string;
    mentionListAriaLabel: string;
    mentionEmptyLabel: string;
    formatToggleAriaLabel?: string;
    formatBoldAriaLabel?: string;
    formatItalicAriaLabel?: string;
    formatStrikeAriaLabel?: string;
    formatUnderlineAriaLabel?: string;
    formatListAriaLabel?: string;
    formatOrderedListAriaLabel?: string;
    formatCodeAriaLabel?: string;
    formatQuoteAriaLabel?: string;
    formatLinkAriaLabel?: string;
    formatAlignLeftAriaLabel?: string;
    formatAlignCenterAriaLabel?: string;
    formatAlignRightAriaLabel?: string;
    formatAlignJustifyAriaLabel?: string;
    formatFontSizeAriaLabel?: string;
    formatFontSizeDecreaseAriaLabel?: string;
    formatFontSizeIncreaseAriaLabel?: string;
    formatUndoAriaLabel?: string;
    formatRedoAriaLabel?: string;
    formatEmojiAriaLabel?: string;
    emojiMenuAriaLabel?: string;
  };

  export type MentionComposerPendingAttachment = {
    id: string;
    fileName: string;
    contentType?: string | null;
    file?: File | null;
    previewUrl?: string | null;
    detail?: string;
    busy?: boolean;
    kind?: "clip" | "inline";
  };

  export type MentionComposerInlineImageInsert = {
    pendingId: string;
    file: File;
  };

  export type DashboardMentionComposerProps = {
    value: string;
    onChange: (value: string) => void;
    onSubmit: (markdown: string) => void;
    labels: MentionComposerLabels;
    mentionHits?: readonly unknown[];
    disabled?: boolean;
    submitting?: boolean;
    showAttach?: boolean;
    fileAccept?: string;
    pendingAttachments?: readonly MentionComposerPendingAttachment[];
    onFilesSelected?: (files: File[]) => void;
    onRemovePendingAttachment?: (id: string) => void;
    onInlineImagesInserted?: (
      items: readonly MentionComposerInlineImageInsert[],
    ) => void;
    onInlineImageRemoved?: (pendingId: string) => void;
    onInlineAttachmentRemoved?: (pendingId: string) => void;
    resolveAttachmentImageSrc?: (
      attachmentId: string,
    ) => string | null | undefined;
    portalScopeClassName?: string;
    submitOnEnter?: boolean;
    submitOnModEnter?: boolean;
  };

  export function createDashboardMentionComposer(
    prefix: string,
  ): ComponentType<DashboardMentionComposerProps>;

  export type DashboardRoomConversationChatColumnProps = {
    msgsRef?: React.Ref<HTMLDivElement | null>;
    onMsgsScroll?: React.UIEventHandler<HTMLDivElement>;
    children: ReactNode;
    dock: ReactNode;
  };

  export type DashboardRoomPanelProps = {
    children: ReactNode;
    "aria-label"?: string;
  };

  export function createDashboardRoomConversationShell(prefix: string): {
    Shell: ComponentType<Record<string, unknown>>;
    ChatColumn: ComponentType<DashboardRoomConversationChatColumnProps>;
    Panel: ComponentType<DashboardRoomPanelProps>;
    classNames: Record<string, string>;
  };

  export type FloatingNoticeVariant = "error" | "warning" | "success" | "info";

  export type FloatingNoticeInput = {
    id?: string;
    title?: string;
    message: string;
    variant?: FloatingNoticeVariant;
    autoDismissMs?: number | null;
  };

  export type FloatingNoticeItem = FloatingNoticeInput & { id: string };

  export function useFloatingNotices(): {
    items: FloatingNoticeItem[];
    push: (notice: FloatingNoticeInput | string) => string;
    dismiss: (id: string) => void;
    clear: () => void;
  };

  export function createFloatingNoticeStack(config: {
    prefix: string;
    portalScopeClassName?: string;
    labels?: { stackAriaLabel?: string; dismissAriaLabel?: string };
  }): ComponentType<{
    items: FloatingNoticeItem[];
    onDismiss: (id: string) => void;
  }>;

  export type DashboardTextAreaFieldProps = {
    label: string;
    value: string;
    onChange: (value: string) => void;
    hint?: string;
    placeholder?: string;
    rows?: number;
    disabled?: boolean;
    required?: boolean;
    id?: string;
    icon?: ReactNode;
  };

  export function textAreaFieldBemClasses(prefix: string): TextFieldClassNames;

  export function createDashboardTextAreaField(config: {
    classNames: TextFieldClassNames;
  }): ComponentType<DashboardTextAreaFieldProps>;

  export type DataRecordCardField = {
    id: string;
    label: ReactNode;
    value: ReactNode;
    present?: boolean;
  };

  export type DashboardDataRecordCardProps = {
    title: ReactNode;
    subtitle?: ReactNode;
    status?: ReactNode;
    fields?: DataRecordCardField[];
    href?: string;
    onNavigate?: (event: MouseEvent<HTMLAnchorElement>) => void;
    ariaLabel?: string;
  };

  export function createDashboardDataRecordCard(config: {
    prefix: string;
  }): ComponentType<DashboardDataRecordCardProps>;

  export type TableColumnVisibilityItem = {
    key: string;
    label: string;
  };

  export type TableColumnVisibilityMenuLabels = {
    trigger: string;
    panelTitle: string;
    reset: string;
    hint: string;
    columnAriaLabel: (columnLabel: string) => string;
    panelAriaLabel?: string;
    reorderAriaLabel?: (columnLabel: string) => string;
  };

  export type TableColumnVisibilityMenuProps = {
    columns: readonly TableColumnVisibilityItem[];
    visibility: Record<string, boolean>;
    onToggleColumn: (key: string, visible: boolean) => void;
    onReset: () => void;
    labels: TableColumnVisibilityMenuLabels;
    className?: string;
    keepAtLeastOne?: boolean;
    enableReorder?: boolean;
    onReorderColumns?: (fromKey: string, toKey: string) => void;
  };

  export function TableColumnVisibilityMenu(props: TableColumnVisibilityMenuProps): ReactElement;

  export function useTableColumnVisibility(options: {
    storageKey: string;
    columns: readonly TableColumnVisibilityItem[];
    enabled?: boolean;
    defaultVisibility?: Record<string, boolean>;
    keepAtLeastOne?: boolean;
    emptyFallbackKeys?: readonly string[];
    legacyStorageKeys?: readonly string[];
    saveDebounceMs?: number;
  }): {
    visibility: Record<string, boolean>;
    order: string[];
    orderedColumns: TableColumnVisibilityItem[];
    visibleKeys: string[];
    visibleColumnCount: number;
    setColumnVisible: (key: string, visible: boolean) => void;
    setColumnOrder: (order: string[]) => void;
    reorderColumns: (fromKey: string, toKey: string) => void;
    applyVisibleOrder: (visibleKeysInOrder: string[]) => void;
    reset: () => void;
    filterColumns: <T extends { key: string }>(columns: readonly T[]) => T[];
  };

  export function uniqueClipboardImageFiles(data: DataTransfer | null | undefined): File[];
  export function collectClipboardImageFiles(data: DataTransfer | null | undefined): File[];
  export function collectPasteImageFiles(data: DataTransfer | null | undefined): File[];
  export function extractClipboardHtmlImageFiles(html: string | null | undefined): File[];
  export function clipboardLooksLikeImagePaste(data: DataTransfer | null | undefined): boolean;
  export function shouldTryAsyncClipboardImageRead(data: DataTransfer | null | undefined): boolean;
  export function readClipboardImageFiles(): Promise<File[]>;
  export function isRichTextClipboardImageFile(file: File): boolean;
}

declare module "@delpi/plugin-ui/styles" {}
