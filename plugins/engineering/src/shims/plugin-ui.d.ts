/**
 * Contratos tipados do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote real.
 * Em vitest: alias `pluginUiTestAliases` aponta para o fonte do kit.
 */
declare module "@delpi/plugin-ui/index" {
  import type {
    ComponentType,
    ErrorInfo,
    ForwardRefExoticComponent,
    InputHTMLAttributes,
    ReactElement,
    ReactNode,
    RefAttributes,
    RefObject,
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
    hint?: string;
    children?: ReactNode;
    actions?: ReactNode;
    className?: string;
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

  export type LoadingActivityCardVariant = "compact" | "panel";

  export type LoadingActivityCardTone = "neutral" | "info";

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
    variant?: LoadingActivityCardVariant;
    tone?: LoadingActivityCardTone;
    sticky?: boolean;
    progressPercent?: number;
    className?: string;
  };

  export function createDashboardLoadingActivityCard(config: {
    prefix: string;
    labels: LoadingActivityCardLabels;
    withCopyWrapper?: boolean;
    block?: string;
    defaultTone?: LoadingActivityCardTone;
  }): ComponentType<DashboardLoadingActivityCardProps>;

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
    prefix?: string;
    labels: {
      emptyMessage?: string;
      fieldHelpAriaLabel: (label: string) => string;
    };
    valueFallback?: string;
    wrapLabels?: boolean;
  }): ComponentType<DashboardDetailFieldGridProps>;

  export type DataTableColumn<T> = {
    key: string;
    header: string;
    headerHint?: string;
    render: (row: T) => ReactNode;
    className?: string;
    align?: "left" | "right" | "center";
    interactive?: boolean;
    rowClick?: "stop" | "propagate";
    sortable?: boolean;
    sortValue?: (row: T) => string | number | null | undefined;
    mobileLabel?: string;
    headerPrefix?: ReactNode;
  };

  export type DataTableClassNames = {
    wrapSection: string;
    wrapEmbedded: string;
    wrap?: string;
    sentenceHeadersWrap?: string;
    outerRoot?: string;
    scrollWrap?: string;
    table: string;
    tableClickable?: string;
    sortableColumn?: string;
    empty: string;
    emptyInnerWrapper?: boolean;
    headerLabel: string;
    headerText: string;
    headerHelp: string;
    sortButton: string;
    sortButtonActive: string;
    sortIndicator: string;
    rowClickable: string;
    sortableTable?: string;
    compactTable?: string;
    colNumeric?: string;
    colWide?: string;
    colActions?: string;
    actions?: string;
    sub?: string;
    rowEditing?: string;
    detailRow?: string;
    detailCell?: string;
  };

  export type DataTableLabels = {
    emptyMessage: string;
    loadingMessage: string;
    sortByAriaLabel: (header: string) => string;
    headerHelpAriaLabel: (header: string) => string;
  };

  export type DataTableProps<T> = {
    columns: DataTableColumn<T>[];
    rows: T[];
    rowKey: (row: T, index: number) => string;
    emptyMessage?: string;
    loading?: boolean;
    onRowClick?: (row: T) => void;
    getRowClassName?: (row: T, index: number) => string | undefined;
    sortKey?: string | null;
    sortDirection?: "asc" | "desc";
    onSortChange?: (columnKey: string) => void;
    layout?: "section" | "embedded" | "scroll";
    compact?: boolean;
    classNames: DataTableClassNames;
    labels: DataTableLabels;
  };

  export type DashboardDataTableProps<T> = Omit<
    DataTableProps<T>,
    "classNames" | "labels"
  >;

  export function DataTable<T>(props: DataTableProps<T>): ReactElement;

  export function dataTableBemClasses(prefix: string): DataTableClassNames;

  export type FilterInputFieldProps = {
    label: string;
    hint?: string;
    id?: string;
    type: Extract<
      InputHTMLAttributes<HTMLInputElement>["type"],
      "month" | "date" | "datetime-local" | "text" | "search"
    >;
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

  export type CompactPaginationHints = {
    info?: string;
    previous?: string;
    next?: string;
  };

  export type DashboardCompactPaginationProps = {
    page: number;
    pageSize: number;
    total: number;
    totalPages?: number;
    pageSizeOptions?: readonly number[];
    onPageChange: (page: number) => void;
    onPageSizeChange?: (pageSize: number) => void;
    hints?: CompactPaginationHints;
    hideWhenSinglePage?: boolean;
    disabled?: boolean;
  };

  export function createCompactPagination(config: {
    prefix: string;
    labels: CompactPaginationLabels;
    hints?: CompactPaginationHints;
    layout?: "grouped" | "flat";
    ghostBtnModifier?: string;
    ghostBtn?: string;
    withHints?: boolean;
  }): ComponentType<DashboardCompactPaginationProps>;

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
    className?: string;
  };

  export function EntityDirectoryPicker(props: EntityDirectoryPickerProps): ReactElement;

  export function entityDirectoryLabel(entity: EntityDirectoryOption): string;

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

  export type HelpTooltipPlacement = "top" | "bottom";
  export type HelpTooltipTrigger = "label" | "icon";
  export type HelpTooltipProps = {
    content: string;
    ariaLabel?: string;
    className?: string;
    wrap?: boolean;
    placement?: HelpTooltipPlacement;
    trigger?: HelpTooltipTrigger;
    suppressed?: boolean;
    children?: ReactNode;
  };
  export function HelpTooltip(props: HelpTooltipProps): ReactNode;

  export type MessageThreadItem = {
    id: string;
    kind: string;
    bodyText: string;
    createdAtLabel: string;
    authorName?: string | null;
    authorUserId?: string | null;
    authorSrc?: string | null;
    mine?: boolean;
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
    emptyContent?: ReactNode;
    portalScopeClassName?: string;
    className?: string;
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

  export type PluginErrorBoundaryLabels = {
    title: string;
    message?: string;
    retry?: string;
  };

  export type PluginErrorBoundaryProps = {
    children: ReactNode;
    labels: PluginErrorBoundaryLabels;
    prefix?: string;
    resetKey?: unknown;
    onError?: (error: Error, info: ErrorInfo) => void;
    onRetry?: () => void;
  };

  export const PluginErrorBoundary: ComponentType<PluginErrorBoundaryProps>;

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

  /* ---- tasks kit (Home Engenharia) ---- */

  export type TaskItemActionFlags = {
    canOpen?: boolean;
    canEdit?: boolean;
    canComplete?: boolean;
    canCancel?: boolean;
  };

  export type TaskItemPresentation = {
    id: string;
    title: string;
    description?: string | null;
    sourceLabel?: string | null;
    statusLabel: string;
    statusTone?: "neutral" | "info" | "warning" | "danger" | "success";
    assigneeLabel?: string | null;
    dueDateLabel?: string | null;
    contextLabel?: string | null;
    overdue?: boolean;
    route?: string | null;
    actions?: TaskItemActionFlags;
  };

  export type TaskItemsTableProps = {
    items: TaskItemPresentation[];
    emptyMessage?: string;
    refreshing?: boolean;
    onOpen?: (item: TaskItemPresentation) => void;
    onEdit?: (item: TaskItemPresentation) => void;
    onComplete?: (item: TaskItemPresentation) => void;
    onCancel?: (item: TaskItemPresentation) => void;
  };

  export function TaskItemsTable(
    props: TaskItemsTableProps,
  ): ReactElement;

  /* ---- portal home kit (F3.R1) ---- */

  export type FormatPortalGreetingInput = {
    displayName?: string | null;
    firstName?: string | null;
    now?: Date;
    fallback?: string | null;
  };

  export function formatPortalGreeting(
    input?: FormatPortalGreetingInput,
  ): string;

  export type PageHeroHighlightTone = "neutral" | "warning" | "danger";

  export type PageHeroHighlight = {
    id: string;
    label: ReactNode;
    value: ReactNode;
    description?: ReactNode;
    tone?: PageHeroHighlightTone;
    loading?: boolean;
    onSelect?: () => void;
    active?: boolean;
    ariaLabel?: string;
  };

  export type DashboardPageHeroProps = {
    eyebrow?: ReactNode;
    title: ReactNode;
    description?: ReactNode;
    badge?: ReactNode;
    actions?: ReactNode;
    highlights?: PageHeroHighlight[];
    children?: ReactNode;
    density?: "comfortable" | "compact";
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardPageHero(config: {
    prefix: string;
  }): ComponentType<DashboardPageHeroProps>;

  export type DashboardMetricStripProps = {
    items: PageHeroHighlight[];
    density?: "comfortable" | "compact";
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardMetricStrip(config: {
    prefix: string;
  }): ComponentType<DashboardMetricStripProps>;

  export type AlertQueueItem = {
    id: string;
    title: ReactNode;
    description?: ReactNode;
    tone?: "neutral" | "info" | "warning" | "danger" | "success";
    leadingIcon?: ReactNode;
    actionLabel?: string;
    onAction?: () => void;
  };

  export type DashboardEventsSectionProps = {
    title: string;
    subtitle?: string;
    hint?: string;
    actions?: ReactNode;
    items: AlertQueueItem[];
    children?: ReactNode;
    omitWhenEmpty?: boolean;
    emptyMessage?: string;
    listAriaLabel?: string;
    className?: string;
  };

  export function createDashboardEventsSection(config: {
    prefix: string;
    labels: { titleHelpAriaLabel: (title: string) => string };
    sectionClassNames?: Record<string, string>;
  }): ComponentType<DashboardEventsSectionProps>;

  export type CatalogSearchHit = {
    id: string;
    label: string;
    groupLabel?: string;
  };

  export type DashboardCatalogSearchBarProps = {
    value: string;
    onChange: (value: string) => void;
    onSelectHit?: (id: string) => void;
    hits?: readonly CatalogSearchHit[];
    placeholder?: string;
    clearLabel?: string;
    emptyHitsLabel?: string;
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardCatalogSearchBar(config: {
    classNames: Record<string, string>;
  }): ComponentType<DashboardCatalogSearchBarProps>;

  export function catalogSearchBarBemClasses(
    prefix: string,
  ): Record<string, string>;

  export type RecentAccessItem = {
    id: string;
    label: string;
    icon?: ReactNode;
  };

  export type DashboardRecentAccessStripProps = {
    items: RecentAccessItem[];
    onSelect: (id: string) => void;
    label?: ReactNode;
    maxVisible?: number;
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardRecentAccessStrip(config: {
    prefix: string;
  }): ComponentType<DashboardRecentAccessStripProps>;

  export type SectionRouteItem = {
    id: string;
    label: string;
    onClick: () => void;
    icon?: ReactNode;
    badge?: string | number;
    disabled?: boolean;
    pinned?: boolean;
    onPinClick?: () => void;
    pinLabel?: string;
    unpinLabel?: string;
    kind?: "navigate" | "create";
  };

  export type DashboardSectionRouteCardProps = {
    title: string;
    icon?: ReactNode;
    badge?: string | number;
    description?: string;
    hint?: string;
    routes: readonly SectionRouteItem[];
    className?: string;
    "aria-label"?: string;
  };

  export function createDashboardSectionRouteCard(config: {
    classNames: Record<string, string>;
  }): ComponentType<DashboardSectionRouteCardProps>;

  export function sectionRouteCardBemClasses(
    prefix: string,
  ): Record<string, string>;

  export type TopBarFavoritesItem = {
    id: string;
    label: string;
  };

  export type DashboardTopBarFavoritesStripProps = {
    items: readonly TopBarFavoritesItem[];
    onSelect: (id: string) => void;
    onRemove: (id: string) => void;
    title: string;
    emptyLabel: string;
    errorLabel?: string | null;
    openAriaLabel: string;
    closeAriaLabel: string;
    removeLabel: (label: string) => string;
    portalScopeClassName?: string;
    className?: string;
  };

  export function createDashboardTopBarFavoritesStrip(config: {
    prefix: string;
    portalScopeClassName?: string;
  }): ComponentType<DashboardTopBarFavoritesStripProps>;

  export type DashboardTopBarSearchTriggerProps = {
    onOpen: () => void;
    label: string;
    shortcutLabel: string;
    "aria-label": string;
    title?: string;
    expanded?: boolean;
    className?: string;
  };

  export function createDashboardTopBarSearchTrigger(config: {
    prefix: string;
  }): ForwardRefExoticComponent<
    DashboardTopBarSearchTriggerProps & RefAttributes<HTMLButtonElement>
  >;

  export type TopBarUserIdentityMenuItem = {
    id: string;
    label: string;
    onSelect: () => void;
    disabled?: boolean;
  };

  export type DashboardTopBarUserIdentityProps = {
    displayName: string | null;
    fallbackLabel?: string;
    avatarUrl?: string | null;
    loading?: boolean;
    className?: string;
    portalScopeClassName?: string;
    href?: string;
    title?: string;
    ariaLabel?: string;
    avatarHref?: string;
    avatarTitle?: string;
    menuItems?: TopBarUserIdentityMenuItem[];
    menuAriaLabel?: string;
  };

  export function createDashboardTopBarUserIdentity(config: {
    prefix: string;
  }): ComponentType<DashboardTopBarUserIdentityProps>;

  export type DashboardCommandPaletteProps = {
    open: boolean;
    onClose: () => void;
    title: string;
    anchorRef: RefObject<HTMLElement | null>;
    value: string;
    onChange: (value: string) => void;
    hits?: readonly CatalogSearchHit[];
    onSelectHit: (id: string) => void;
    placeholder?: string;
    emptyHitsLabel?: string;
    clearLabel?: string;
    portalScopeClassName?: string;
    "aria-label"?: string;
  };

  export function createDashboardCommandPalette(config: {
    prefix: string;
    portalScopeClassName: string;
  }): ComponentType<DashboardCommandPaletteProps>;

  export type PagePathLink = {
    label: string;
    href: string;
    onNavigate?: (event: {
      preventDefault: () => void;
    }) => void;
  };

  export type PagePathItem = {
    label: string;
    href?: string;
    onNavigate?: (event: {
      preventDefault: () => void;
    }) => void;
  };

  export type DashboardPagePathProps = {
    back: PagePathLink;
    items?: PagePathItem[];
    current: string;
    maxVisibleItems?: number;
    size?: "sm" | "md";
    ariaLabel?: string;
    className?: string;
  };

  export function createDashboardPagePath(config: {
    prefix: string;
    portalScopeClassName?: string;
  }): ComponentType<DashboardPagePathProps>;

  export type DashboardViewTransitionProps = {
    transitionKey: string;
    children: ReactNode;
    tone?: "page" | "panel";
    className?: string;
    "aria-live"?: "off" | "polite" | "assertive";
  };

  export function createDashboardViewTransition(config: {
    prefix: string;
  }): ComponentType<DashboardViewTransitionProps>;

  export type UserManualTocItem = {
    id: string;
    label: string;
    onSelect: () => void;
  };

  export type EngineeringUserManualKit = {
    classNames: Record<string, string>;
    Frame: ComponentType<{ children: ReactNode; className?: string }>;
    Eyebrow: ComponentType<{ children: ReactNode }>;
    Scope: ComponentType<{ children: ReactNode }>;
    Section: ComponentType<{ id?: string; children: ReactNode }>;
    Layout: ComponentType<{
      title: string;
      items: readonly UserManualTocItem[];
      children: ReactNode;
      "aria-label"?: string;
    }>;
    Concepts: ComponentType<{
      items: readonly { term: string; meaning: ReactNode }[];
    }>;
    GuideTable: ComponentType<{
      rows: readonly { want: ReactNode; where: ReactNode; how: ReactNode }[];
    }>;
    Faq: ComponentType<{
      items: readonly { q: ReactNode; a: ReactNode }[];
    }>;
    Glossary: ComponentType<{
      items: readonly { term: ReactNode; meaning: ReactNode }[];
    }>;
  };

  export function createDashboardUserManual(config: {
    prefix: string;
  }): EngineeringUserManualKit;

  // --- KPI card (mesmo componente do Dashboard Engenharia) ---

  export type KpiPerformanceBadge = {
    tone: "success" | "warning";
    statusLabel: string;
    directionLabel: string;
  };

  export type KpiScopeBadge = {
    label: string;
    tone?: "scope" | "info" | "neutral";
  };

  export type KpiComparisonTone = "positive" | "negative" | "warning";

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
    comparisonTone?: KpiComparisonTone | null;
    contextLabel?: string;
    goalLabel?: string | null;
    goalPrefix?: string | null;
    goalHint?: string | null;
    monthlyGoalLabel?: string | null;
    monthlyGoalPrefix?: string | null;
    monthlyGoalHint?: string | null;
    periodKindBadge?: string | null;
    goalScopeBadge?: KpiScopeBadge | null;
    goalScopeHint?: string | null;
    goalPerformanceBadge?: KpiPerformanceBadge | null;
    goalPerformanceBadges?: KpiPerformanceBadge[];
    iddScoreLabel?: string | null;
    goalVariant?: "default" | "per-unit";
    subtitle?: string;
    icon?: ReactNode;
    footer?: ReactNode;
    loading?: boolean;
    refreshing?: boolean;
    className?: string;
    onClick?: () => void;
  };

  export function createDashboardKpiCard(config: {
    prefix: string;
    labels: KpiCardLabels;
    cardModifier?: string;
  }): ComponentType<DashboardKpiCardProps>;

  // --- Filtros: período rápido, datas, unidade ---

  export type PeriodPresetId =
    | "today"
    | "this_week"
    | "this_month"
    | "last_month"
    | "this_quarter"
    | "this_year"
    | "last_12_months"
    | "custom";

  export type PeriodPresetRange = {
    dateStart: string;
    dateEnd: string;
    competence: string;
  };

  export const PERIOD_PRESET_OPTIONS: readonly {
    value: PeriodPresetId;
    label: string;
  }[];

  export function resolvePeriodPreset(
    preset: PeriodPresetId,
    now?: Date,
    timeZone?: string,
  ): PeriodPresetRange | null;

  export function detectPeriodPreset(
    dateStart: string,
    dateEnd: string,
    now?: Date,
    timeZone?: string,
  ): PeriodPresetId;

  export function resolveEffectivePeriodPreset(
    dateStart: string,
    dateEnd: string,
    stored?: PeriodPresetId | null,
    now?: Date,
    timeZone?: string,
  ): PeriodPresetId;

  export function parsePeriodPresetId(
    value: string | null | undefined,
  ): PeriodPresetId | null;

  export function todayIsoInTimeZone(now?: Date, timeZone?: string): string;

  export type QuickPeriodSelectorProps = {
    value: PeriodPresetId;
    onChange: (value: PeriodPresetId) => void;
    prefix?: string;
    label?: string;
    hint?: string;
    ariaLabel?: string;
    idPrefix?: string;
  };

  export function createDashboardQuickPeriodSelector(
    prefix: string,
  ): ComponentType<Omit<QuickPeriodSelectorProps, "prefix">>;

  export type DateFieldInputType = "date" | "month";

  export type DateFieldClassNames = Record<string, string>;

  export type DashboardDateFieldProps = {
    id?: string;
    label: string;
    hint?: string;
    type?: DateFieldInputType;
    value: string;
    onChange: (value: string) => void;
    required?: boolean;
    disabled?: boolean;
    wide?: boolean;
    className?: string;
  };

  export function createDashboardDateField(config: {
    classNames: DateFieldClassNames;
  }): ComponentType<DashboardDateFieldProps>;

  export function dateFieldBemClasses(prefix: string): DateFieldClassNames;

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
    labelHint?: string;
    id?: string;
    options: MultiSelectOption[];
    selectedValues: string[];
    onChange: (values: string[]) => void;
    emptyLabel?: string;
    searchable?: boolean;
    disabled?: boolean;
    className?: string;
    creatable?: boolean;
    maxCreateLength?: number;
    maxSelected?: number;
    onCreateOption?: (value: string) => void;
    showSelectedTags?: boolean;
    includeSelectedInOptions?: boolean;
    showBulkActions?: boolean;
    hint?: string;
    placeholder?: string;
  };

  export function createDashboardMultiSelectField(config: {
    prefix?: string;
    classNames?: Record<string, string>;
    labels: MultiSelectFieldLabels;
    portalScopeClassName?: string;
  }): ComponentType<DashboardMultiSelectFieldProps>;

  // --- Unidades operacionais e apresentação de metas/IDD ---

  export const OPERATIONAL_UNIT_OPTIONS: MultiSelectOption[];

  export function formatOperationalUnitCode(
    code: string | null | undefined,
    fallback?: string,
  ): string;

  export function formatFilterViewScopeLabel(
    viewMode: "consolidated" | "branch",
    branch: string,
  ): string;

  export function normalizeOperationalUnitCode(
    value: string | null | undefined,
  ): string;

  export type DashboardGoalFields = {
    goal_label?: string | null;
    goal_value?: number | null;
    comparable_goal?: number | null;
    reference_goal?: number | null;
    target?: number | null;
    has_goal?: boolean;
    goal_aggregation?: string | null;
    goal_mode?: string | null;
    goal_period_kind?: string | null;
    goal_period_partial?: boolean | null;
    goal_scope_branch?: string | null;
    goal_scope_label?: string | null;
    goal_scope_hint?: string | null;
    scope_type?: string | null;
    performance_direction?: string | null;
    value_unit?: string | null;
    value_prefix?: string | null;
    value_suffix?: string | null;
    value_decimals?: number | null;
    start_date?: string | null;
    end_date?: string | null;
  };

  export type KpiGoalPresentation = {
    goalLabel: string | null;
    goalPrefix: string | null;
    goalHint: string | null;
    monthlyGoalLabel: string | null;
    monthlyGoalPrefix: string | null;
    monthlyGoalHint: string | null;
    goalScopeBadge: GoalScopeBadge | null;
    goalScopeHint: string | null;
    goalPerformanceBadge: GoalPerformanceBadge | null;
    iddScoreLabel: string | null;
    contextLabel: string;
  };

  export function buildKpiGoalPresentation(
    contextLabel: string,
    goal?: DashboardGoalFields | null,
    formatComparable?: (value: number) => string,
    options?: {
      showGoal?: boolean;
      realizedValue?: number | null;
      dateStart?: string | null;
      dateEnd?: string | null;
      iddScoreLabel?: string | null;
    },
  ): KpiGoalPresentation;

  export function formatDashboardMetricValue(
    value: number | null | undefined,
    fields?: DashboardGoalFields | null,
    options?: { fallback?: string },
  ): string;

  export function resolveIndicatorIddScoreLabelFromSi(
    score: number | null | undefined,
  ): string | null;
}

// --- Superfície consumida pela feature LMP (G5) ------------------------------

declare module "@delpi/plugin-ui/index" {
  export type ChartGranularity = "day" | "week" | "month" | "year";

  export function useChartGranularitySelection(
    dateStart?: string,
    dateEnd?: string,
    options?: {
      resolveAutoGranularity?: (
        suggested: ChartGranularity,
      ) => ChartGranularity;
    },
  ): {
    granularity: ChartGranularity;
    setGranularity: (value: ChartGranularity) => void;
  };

  export function delpiUiClass(prefixClass: string, uiClass: string): string;
  export function ensureDelpiUiClass(
    className: string,
    requiredClass: string,
  ): string;
  export function stateBoxPlaceholderBemClasses(prefix: string): string;
  export function ghostBtnBemClasses(prefix: string): string;

  export const CHART_COLORS_LMPS: readonly string[];

  export type ChartCardClassNames = {
    section: string;
    header: string;
    heading?: string;
    headerRow?: string;
    title: string;
    titleHelp?: string;
    hint?: string;
    actions?: string;
    body: string;
  };

  export type ChartCardProps = {
    title: string;
    titleHint?: string;
    hint?: string;
    children: ReactNode;
    headerActions?: ReactNode;
    classNames: ChartCardClassNames;
    className?: string;
    titleLevel?: 2 | 3;
  };

  export function chartCardBemClasses(
    prefix: string,
    options?: {
      withHeading?: boolean;
      withActions?: boolean;
      cardModifier?: string;
      headerLayout?: "default" | "titleRow";
      wide?: boolean;
    },
  ): ChartCardClassNames;

  export function ChartCard(props: ChartCardProps): ReactElement;

  export type DetailCardClassNames = {
    card: string;
    header: string;
    icon?: string;
    heading?: string;
    title: string;
    titleHelp?: string;
    description?: string;
    hint?: string;
    actions?: string;
    body?: string;
    wrapBody: boolean;
  };

  export type DetailCardLabels = {
    titleHelpAriaLabel: (title: string) => string;
  };

  export type DetailCardProps = {
    title: string;
    titleHint?: string;
    hint?: string;
    icon?: ReactNode;
    children: ReactNode;
    className?: string;
    headerActions?: ReactNode;
    role?: string;
    classNames: DetailCardClassNames;
    labels: DetailCardLabels;
  };

  export type DashboardDetailCardProps = Omit<
    DetailCardProps,
    "classNames" | "labels"
  >;

  export function detailCardRichBemClasses(
    prefix: string,
  ): DetailCardClassNames;

  export function createDashboardDetailCard(config: {
    classNames: DetailCardClassNames;
    labels: DetailCardLabels;
  }): ComponentType<DashboardDetailCardProps>;

  export type ChartGranularityOption<T extends string = string> = {
    value: T;
    label: string;
  };

  export type ChartGranularityToggleClassNames = Record<string, string>;

  export type ChartGranularityToggleLabels = {
    groupAriaLabel: string;
  };

  export type ChartGranularityToggleProps<T extends string = string> = {
    value: T;
    onChange: (value: T) => void;
    options: readonly ChartGranularityOption<T>[];
    idPrefix?: string;
    classNames: ChartGranularityToggleClassNames;
    labels: ChartGranularityToggleLabels;
    size?: string;
  };

  export type ChartToolbarClassNames = Record<string, string | undefined>;

  export type ChartToolbarLabels = {
    exportSeries: string;
    exportSeriesAriaLabel: string;
  };

  export type ChartToolbarProps<T extends string = string> = {
    granularity: T;
    onGranularityChange: (value: T) => void;
    options: readonly ChartGranularityOption<T>[];
    idPrefix?: string;
    onExportCsv?: () => void;
    exportDisabled?: boolean;
    exportActions?: ReactNode;
    extra?: ReactNode;
    granularityHelp?: string;
    exportHelp?: string;
    granularityField?: { label: string; hint?: string };
    classNames: ChartToolbarClassNames;
    labels: ChartToolbarLabels;
    granularityToggleClassNames: ChartGranularityToggleClassNames;
    granularityToggleLabels: ChartGranularityToggleLabels;
  };

  export type DashboardChartToolbarLabels = ChartToolbarLabels &
    ChartGranularityToggleLabels;

  export type DashboardChartGranularityToggleProps<
    T extends string = string,
  > = Omit<
    ChartGranularityToggleProps<T>,
    "classNames" | "labels" | "options"
  > & {
    modes?: readonly T[];
    options: readonly ChartGranularityOption<T>[];
  };

  export type DashboardChartToolbarProps<T extends string = string> = Omit<
    ChartToolbarProps<T>,
    | "classNames"
    | "labels"
    | "granularityToggleClassNames"
    | "granularityToggleLabels"
    | "options"
  > & {
    modes?: readonly T[];
    options: readonly ChartGranularityOption<T>[];
  };

  export function createDashboardChartToolbarKit(config: {
    prefix: string;
    labels: DashboardChartToolbarLabels;
  }): {
    ChartGranularityToggle: <T extends string>(
      props: DashboardChartGranularityToggleProps<T>,
    ) => ReactElement;
    ChartToolbar: <T extends string>(
      props: DashboardChartToolbarProps<T>,
    ) => ReactElement;
  };

  export type TableColumnVisibilityItem = { key: string; label: string };
  export type TableColumnVisibilityMap = Record<string, boolean>;

  export type TableColumnVisibilityMenuLabels = {
    trigger: string;
    panelTitle: string;
    reset: string;
    hint: string;
    columnAriaLabel: (columnLabel: string) => string;
    panelAriaLabel?: string;
    reorderAriaLabel?: (columnLabel: string) => string;
  };

  export const DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS: TableColumnVisibilityMenuLabels;

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

  export function TableColumnVisibilityMenu(
    props: TableColumnVisibilityMenuProps,
  ): ReactElement;

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

  export function dataTableSectionBemClasses(
    prefix: string,
  ): DataTableSectionClassNames;

  export type UseTableColumnVisibilityOptions = {
    storageKey: string;
    columns: readonly TableColumnVisibilityItem[];
    enabled?: boolean;
    defaultVisibility?: TableColumnVisibilityMap;
    keepAtLeastOne?: boolean;
    emptyFallbackKeys?: readonly string[];
    legacyStorageKeys?: readonly string[];
    saveDebounceMs?: number;
  };

  export type UseTableColumnVisibilityResult = {
    visibility: TableColumnVisibilityMap;
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

  export function useTableColumnVisibility(
    options: UseTableColumnVisibilityOptions,
  ): UseTableColumnVisibilityResult;

  export type NativeTextControlProps = {
    id?: string;
    value: string | number;
    onChange: (value: string) => void;
    type?:
      | "text"
      | "number"
      | "url"
      | "date"
      | "datetime-local"
      | "search"
      | "password"
      | "month"
      | "time";
    placeholder?: string;
    disabled?: boolean;
    required?: boolean;
    readOnly?: boolean;
    min?: number | string;
    max?: number | string;
    step?: number | string;
    maxLength?: number;
    className?: string;
    style?: CSSProperties;
    tabIndex?: number;
    "aria-label"?: string;
    "aria-invalid"?: boolean;
    autoComplete?: string;
  };

  export const NativeTextControl: ForwardRefExoticComponent<
    NativeTextControlProps & RefAttributes<HTMLInputElement>
  >;

  // --- Metas / IDD (Strategic Indicators — apresentação) ---

  export type PerformanceDirection = "higher_is_better" | "lower_is_better";
  export type GoalPerformanceTone = "success" | "warning";
  export type GoalScopeBadgeTone = "scope" | "info";

  export type GoalPerformanceBadge = {
    tone: GoalPerformanceTone;
    statusLabel: string;
    directionLabel: string;
  };

  export type GoalScopeBadge = {
    tone: GoalScopeBadgeTone;
    label: string;
  };

  export type BranchMetricSlice<
    T extends DashboardGoalFields = DashboardGoalFields,
  > = {
    realized: number | null | undefined;
    goal?: T | null;
  };

  export type PerBranchMetricSlices<
    T extends DashboardGoalFields = DashboardGoalFields,
  > = {
    filial01: BranchMetricSlice<T> | null;
    filial02: BranchMetricSlice<T> | null;
  };

  export function calculateIndicatorIddScore(
    realized: number | null | undefined,
    goal?: DashboardGoalFields | null,
  ): number | null;

  export function formatIndicatorIddScore(
    score: number | null | undefined,
    fallback?: string,
  ): string;

  export function resolveIddScoreLabel(
    realized: number | null | undefined,
    goal?: DashboardGoalFields | null,
  ): string | null;

  export function resolveConsolidatedIddScoreLabel(
    entries: Array<{
      realized: number | null | undefined;
      goal?: DashboardGoalFields | null;
    }>,
  ): string | null;

  export function applyConsolidatedBranchIddScore(
    presentation: KpiGoalPresentation,
    options: {
      activeBranch?: string;
      branches?: PerBranchMetricSlices | null;
      iddScoreLabel?: string | null;
    },
  ): KpiGoalPresentation;

  export function buildKpiGoalPresentationWithBranchIdd<
    T extends DashboardGoalFields,
  >(
    contextLabel: string,
    consolidatedGoal: T | null | undefined,
    options: {
      realizedValue?: number | null;
      activeBranch?: string;
      branches?: PerBranchMetricSlices<T> | null;
      formatComparable?: (value: number) => string;
      showGoal?: boolean;
      dateStart?: string | null;
      dateEnd?: string | null;
      iddScoreLabel?: string | null;
    },
  ): KpiGoalPresentation;

  export function fetchPerBranchMetricSlices<
    T extends DashboardGoalFields,
  >(
    fetchMetric: (
      branch: "01" | "02",
      signal?: AbortSignal,
    ) => Promise<T>,
    getRealized: (data: T) => number | null | undefined,
    signal?: AbortSignal,
    mapGoal?: (data: T) => DashboardGoalFields | null | undefined,
  ): Promise<PerBranchMetricSlices<T>>;

  export function formatGoalScopeLabel(
    goalScopeBranch?: string | null,
    scopeType?: string | null,
  ): string;

  export function resolveGoalScopeBadge(
    goal?: DashboardGoalFields | null,
  ): GoalScopeBadge | null;

  export function formatPerformanceDirectionLabel(
    direction?: PerformanceDirection | string | null,
  ): string | null;

  export function isGoalOnTrack(
    realized: number,
    comparableGoal: number,
    direction?: PerformanceDirection | string | null,
  ): boolean;

  export function resolveOffTrackStatusLabel(
    direction?: PerformanceDirection | string | null,
  ): string;

  export function resolveGoalPerformanceBadge(
    realized: number | null | undefined,
    goal?: DashboardGoalFields | null,
  ): GoalPerformanceBadge | null;

  export function resolveGoalLabel(
    goal?: DashboardGoalFields | null,
    formatComparable?: (value: number) => string,
  ): string | null;

  export function formatGoalSubtitle(
    periodLabel: string,
    goal?: DashboardGoalFields | null,
    formatComparable?: (value: number) => string,
    realizedValue?: number | null,
  ): string;

  export function formatKpiGoalExportFragments(
    presentation: Pick<
      KpiGoalPresentation,
      "goalLabel" | "goalPrefix" | "monthlyGoalLabel" | "monthlyGoalPrefix"
    > | null | undefined,
  ): string[];

  export function joinKpiExportContext(
    ...parts: Array<string | null | undefined>
  ): string;

  // --- Unidades operacionais ---

  export const OPERATIONAL_UNIT_COLUMN_LABEL: string;
  export const OPERATIONAL_UNIT_FIELD_LABEL: string;

  export function buildOperationalUnitOptions(
    codes: string[],
  ): MultiSelectOption[];

  export function formatGoalScopeUnitLabel(
    goalScopeBranch?: string | null,
    scopeType?: string | null,
  ): string;

  export function formatOperationalUnitsFilterLabel(
    branches: string[],
    options?: { emptyLabel?: string; allSelectedCount?: number },
  ): string;

  export function formatOperationalUnitsPrintLabel(
    branches: string[],
    options?: { allSelectedCount?: number },
  ): string;

  // --- Motor tabular de exportação (CSV / XLSX / PDF) ---

  export type TabularExportFormat = "csv" | "xlsx" | "pdf";

  export type ExportAction = {
    format: TabularExportFormat;
    label: string;
    title: string;
  };

  export const TABULAR_EXPORT_ACTIONS: ReadonlyArray<ExportAction>;

  export type ExportColumn = { key: string; label: string };

  export type TableExportPayload = {
    title: string;
    columns: ExportColumn[];
    rows: Record<string, unknown>[];
  };

  export type ExportAlertFn = (message: string) => void;

  export function configureExportAlert(fn: ExportAlertFn): void;
  export function exportAlert(message: string): void;

  export function triggerFileDownload(blob: Blob, filename: string): void;
  export function triggerBlobDownload(blob: Blob, filename: string): void;
  export function csvCell(value: unknown): string;
  export function buildUtf8CsvBlob(content: string): Blob;
  export function sanitizeFilename(name: string, fallback?: string): string;
  export function sanitizeSheetName(name: string, fallback?: string): string;

  export type ExportXlsxOptions = {
    emptyMessage?: string;
    filename?: string;
  };

  export type ExportPdfOptions = {
    subtitle?: string;
  };

  export function exportPayloadToCsv(payload: TableExportPayload): void;
  export function exportPayloadToXlsx(
    payload: TableExportPayload,
    options?: ExportXlsxOptions,
  ): void;
  export function exportPayloadToPdf(
    payload: TableExportPayload,
    options?: ExportPdfOptions,
  ): void;
  export function exportPayloadsToCsv(
    title: string,
    payloads: TableExportPayload[],
  ): void;
  export function exportPayloadsToXlsx(
    title: string,
    payloads: TableExportPayload[],
  ): void;
  export function exportPayloadsToPdf(
    title: string,
    payloads: TableExportPayload[],
    options?: ExportPdfOptions,
  ): void;
  export function exportTableFormat(
    payload: TableExportPayload,
    format: TabularExportFormat,
    options?: ExportPdfOptions & ExportXlsxOptions,
  ): void;

  export type TabularExportButtonsProps = {
    actions?: ReadonlyArray<ExportAction>;
    disabled?: boolean;
    exporting?: boolean;
    className?: string;
    buttonClassName?: string;
    showIcon?: boolean;
    groupAriaLabel?: string;
    exportingLabel?: string;
    leading?: ReactNode;
    onExport: (format: TabularExportFormat) => void | Promise<void>;
  };

  export function TabularExportButtons(
    props: TabularExportButtonsProps,
  ): ReactElement;

  // --- Documento PDF DELPI ---

  export type DelpiDocumentColumn = { key: string; label: string };

  export type DelpiDocumentTable = {
    title: string;
    columns: DelpiDocumentColumn[];
    rows: Record<string, unknown>[];
    highlightStatusColumn?: boolean;
  };

  export type DelpiDocumentSummaryLine = {
    label: string;
    value: string;
  };

  export type DelpiDocumentImageSection = {
    title?: string;
    dataUrl: string;
    alt?: string;
  };

  export type DelpiDocumentTextSection = {
    title: string;
    body: string;
  };

  export type DelpiDocumentBadgeTone = "approved" | "rejected" | "neutral";

  export type DelpiDocumentSpec = {
    documentTitle: string;
    subtitle?: string;
    badge?: string;
    badgeTone?: DelpiDocumentBadgeTone;
    runningMeta?: string;
    summaryLines?: DelpiDocumentSummaryLine[];
    textSections?: DelpiDocumentTextSection[];
    tables?: DelpiDocumentTable[];
    imageSections?: DelpiDocumentImageSection[];
    footerNote?: string;
    footerContext?: string;
  };

  export function escapeDelpiDocumentHtml(value: string): string;
  export function resolveDelpiLogoUrl(): string | undefined;
  export function buildDelpiDocumentStyles(): string;
  export function buildDelpiBrandBarHtml(className: string): string;
  export function buildDelpiDocumentTableSection(
    table: DelpiDocumentTable,
  ): string;
  export function buildDelpiDocumentHtml(
    spec: DelpiDocumentSpec,
    logoUrl?: string,
  ): string;
  export function buildDefaultExportSummaryLines(
    recordCount: number,
  ): DelpiDocumentSummaryLine[];
  export function printDelpiDocumentHtml(
    html: string,
    options?: { preferPopup?: boolean; iframeTitle?: string },
  ): boolean;
  export function printDelpiDocumentSpec(spec: DelpiDocumentSpec): boolean;
  export function exportTablePayloadToPdf(
    payload: TableExportPayload,
    options?: { subtitle?: string },
  ): void;
  export function exportTablePayloadsToPdf(
    title: string,
    payloads: TableExportPayload[],
    options?: { subtitle?: string },
  ): void;
  export function exportChartPayloadToPdf(
    title: string,
    payload: TableExportPayload,
    chartDataUrl: string | null,
    options?: { subtitle?: string },
  ): void;
}

declare module "@delpi/plugin-ui/styles" {}
