/**
 * Contratos tipados do remote `@delpi/plugin-ui` para o `tsc` do MFE.
 * Em runtime o Module Federation resolve o pacote real.
 * Em vitest: alias `pluginUiTestAliases` aponta para o fonte do kit.
 */
declare module "@delpi/plugin-ui/index" {
  import type {
    ComponentType,
    ErrorInfo,
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

  export type DashboardUnderlineNavProps = {
    items: UnderlineNavItem[];
    activeId: string;
    mode?: "navigation" | "tabs";
    layout?: "row" | "wrap";
    density?: "default" | "compact";
    className?: string;
    "aria-label"?: string;
  };
  export function createDashboardUnderlineNav(config: {
    prefix: string;
  }): ComponentType<DashboardUnderlineNavProps>;

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

  export type DashboardCompactPaginationProps = {
    page: number;
    pageSize: number;
    total: number;
    totalPages?: number;
    onPageChange: (page: number) => void;
    disabled?: boolean;
  };

  export function createCompactPagination(config: {
    prefix: string;
    labels: CompactPaginationLabels;
    layout?: "grouped" | "flat";
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


  /* PRC-REF-023 — contrato compartilhado de product registration
   * (utils/prcProductRegistration.ts do kit). */
  export type PrcFieldSpec = {
    path: string;
    kind: string;
    requiredCreateIntake: boolean;
    verifiable: boolean;
    officialField?: string | null;
    enumValues?: string[] | null;
    maxLength: number;
    note?: string | null;
  };
  export type PrcReferenceData = {
    schemaVersion: number;
    productTypes: string[];
    requestTypes: string[];
    statuses: string[];
    sources: string[];
    fields: PrcFieldSpec[];
    editableDraftPaths: string[];
    supplierKeys: { required: string[]; optional: string[] };
  };
  export type PrcSupplierLinkChange = {
    operation: "update" | "add" | "remove";
    key: { supplierCode: string; store: string };
    fields: { partNumber?: string; catalogNumber?: string };
    reason?: string;
    fieldReasons?: { partNumber?: string; catalogNumber?: string };
  };
  export type PrcIntakeBody = {
    source: string;
    externalRequestId?: string | null;
    externalItemId?: string | null;
    requestType: "create" | "update";
    productType: string;
    schemaVersion: number;
    requestedData?: Record<string, unknown> | null;
    officialProductCode?: string | null;
    baseRevision?: number | null;
    changes?: Array<{
      path: string;
      proposedValue: unknown;
      reason: string;
    }> | null;
    supplierLinkChanges?: PrcSupplierLinkChange[] | null;
    reasons?: {
      fields?: Record<string, string>;
      supplierLinks?: Array<{
        key: { supplierCode: string; store: string };
        reason?: string;
        fieldReasons?: { partNumber?: string; catalogNumber?: string };
      }>;
    } | null;
    baselineFingerprint?: string | null;
    editContextReadAt?: string | null;
  };
  export type PrcScalarChange = { path: string; before: string; after: string };
  export type PrcLinkKey = { supplierCode: string; store: string };
  export type PrcLinkOp =
    | {
        operation: "update" | "add";
        key: PrcLinkKey;
        fields: { partNumber?: string; catalogNumber?: string };
        supplierName?: string;
      }
    | { operation: "remove"; key: PrcLinkKey };
  export type SupplierRowOrigin = "official" | "draft";
  export type SupplierRow = {
    rowId: string;
    origin: SupplierRowOrigin;
    supplierCode: string;
    store: string;
    supplierName: string;
    supplierShortName?: string;
    partNumber: string;
    catalogNumber: string;
    query: string;
    searchOpen?: boolean;
    pnReason?: string;
    catReason?: string;
    opReason?: string;
    pnReasonOpen?: boolean;
    catReasonOpen?: boolean;
    opReasonOpen?: boolean;
    selectionError?: string;
  };
  export type PrcLinkRow = {
    rowId: string;
    origin: SupplierRowOrigin;
    supplierCode: string;
    store: string;
    supplierName?: string;
    partNumber: string;
    catalogNumber: string;
  };
  export type PrcOfficialLink = {
    supplierCode: string;
    store: string;
    supplierName?: string;
    partNumber?: string;
    catalogNumber?: string;
  };
  export type LinkDiffResult = {
    ops: PrcLinkOp[];
    ambiguousOfficialKeys: string[];
    conflictingKeys: string[];
  };
  export function linkKeyOf(code: string, store: string): string;
  export function supplierOfficialKey(code: string, store: string): string;
  export function computeScalarDiff(
    baseline: Record<string, unknown>,
    values: Record<string, string>,
    paths: string[],
  ): PrcScalarChange[];
  export function computeLinkDiff(
    official: PrcOfficialLink[],
    rows: PrcLinkRow[],
    removeRowIds?: ReadonlySet<string>,
  ): PrcLinkOp[];
  export function computeLinkDiffDetailed(
    official: PrcOfficialLink[],
    rows: PrcLinkRow[],
    removeRowIds?: ReadonlySet<string>,
  ): LinkDiffResult;
  export function linkDiffConflicts(rows: PrcLinkRow[]): string[];
  export function linkChangesWithReasons(
    ops: PrcLinkOp[],
    rows: SupplierRow[],
  ): PrcSupplierLinkChange[];
  export function buildCreateReasons(
    values: Record<string, string>,
    reasons: Record<string, string>,
    suppliers: SupplierRow[],
  ): PrcIntakeBody["reasons"];
  export function emptySupplierRow(): SupplierRow;
  export function newSupplierRowId(prefix?: string): string;
  export function toSupplierRows(value: unknown): SupplierRow[];
  export function supplierRowsToPayload(rows: SupplierRow[]): unknown[];
  export function officialSupplierRow(link: PrcOfficialLink): SupplierRow;
  export function duplicateDraftRowIds(rows: SupplierRow[]): Set<string>;
  export function findRowWithOfficialKey(
    rows: SupplierRow[],
    code: string,
    store: string,
    exceptRowId?: string,
  ): SupplierRow | undefined;
  export function supplierHitMain(hit: {
    supplier_name?: string;
  }): string;
  export function supplierHitLabel(hit: {
    supplier_code?: string;
    supplier_store?: string;
    supplier_name?: string;
  }): string;
  export function supplierHitSecondary(hit: {
    supplier_code?: string;
    supplier_store?: string;
    supplier_short_name?: string;
    supplier_name?: string;
  }): string;
  export function buildCreateIntakeBody(args: {
    source: string;
    refData: PrcReferenceData | null;
    values: Record<string, string>;
    reasons: Record<string, string>;
    suppliers: SupplierRow[];
    productType?: string;
    externalRequestId?: string | null;
    externalItemId?: string | null;
  }): PrcIntakeBody;
  export function buildUpdateIntakeBody(args: {
    source: string;
    refData: PrcReferenceData | null;
    officialCode: string;
    scalarDiff: PrcScalarChange[];
    linkOps: PrcLinkOp[];
    reasons: Record<string, string>;
    suppliers: SupplierRow[];
    productType?: string;
    baselineFingerprint?: string | null;
    editContextReadAt?: string | null;
    externalRequestId?: string | null;
    externalItemId?: string | null;
  }): PrcIntakeBody;
  export const PRC_ATTACHMENT_ACCEPT: string;
  export const PRC_ATTACHMENT_MAX_BYTES: number;
  export const PRC_ATTACHMENT_MAX_COUNT: number;
  export const PRC_ATTACHMENT_MAX_MB: number;
  export type PrcAttachmentLocalCheck =
    | { ok: true }
    | { ok: false; error: string };
  export function prcCheckAttachmentFile(
    file: File,
  ): PrcAttachmentLocalCheck;
  export function prcFormatSize(bytes: number): string;
  export const PRC_ATTACHMENT_STATE_LABELS: Record<string, string>;
  export const PRC_ATTACHMENT_MEDIA_LABELS: Record<string, string>;
  export interface PrcSupportFile {
    localId: string;
    file: File;
  }
  export interface PrcSupportPickResult {
    files: PrcSupportFile[];
    errors: Record<string, string>;
  }
  export function newSupportFileId(file: File): string;
  export function addSupportFiles(
    current: PrcSupportFile[],
    picked: File[],
    maxCount?: number,
  ): PrcSupportPickResult;
  export function removeSupportFile(
    current: PrcSupportFile[],
    localId: string,
  ): PrcSupportFile[];
  export const PRC_STATUS_LABELS: Record<string, string>;
  export const PRC_TYPE_LABELS: Record<string, string>;
  export const PRC_FIELD_LABELS: Record<string, string>;
  export const PRC_SUPPLIER_LABELS: Record<string, string>;
  export const PRC_FIELD_HELP: Record<string, string>;
  export const PRC_CATALOG_KINDS: Record<string, string>;
  export type PrcCatalogOption = { value: string; label: string };
  export function catalogOptions(
    items: readonly { code: string; label?: string | null }[],
  ): PrcCatalogOption[];
  export function enumOptions(
    path: string,
    values: readonly string[],
  ): PrcCatalogOption[];
  export function withSelectedOption(
    options: readonly PrcCatalogOption[],
    value: string,
  ): PrcCatalogOption[];

  /* PRC-REF-023-UX-PARITY-FIX-02 — controles PRC compartilhados do kit */
  export const PRC_REASON_MAX: number;
  export const PRC_SUPPLIER_TEXT: Record<string, string>;
  export function PrcReasonToggle(props: {
    id: string;
    value: string;
    open: boolean;
    onToggle: () => void;
    disabled?: boolean;
    label?: string;
  }): JSX.Element;
  export function PrcReasonEditor(props: {
    id: string;
    value: string;
    onChange: (v: string) => void;
    onCollapse: () => void;
    disabled?: boolean;
    label?: string;
  }): JSX.Element;
  export function PrcReasonField(props: {
    id: string;
    value: string;
    onChange: (v: string) => void;
    disabled?: boolean;
    label?: string;
  }): JSX.Element;
  export type PrcSupplierHitLike = {
    supplier_code?: string;
    supplier_store?: string;
    supplier_name?: string;
    supplier_short_name?: string;
    [key: string]: unknown;
  };
  export type PrcSupplierSearchFn = (
    query: string,
    signal?: AbortSignal,
  ) => Promise<PrcSupplierHitLike[]>;
  export function useSupplierSearch(
    query: string,
    fetcher: PrcSupplierSearchFn,
  ): {
    items: PrcSupplierHitLike[];
    open: boolean;
    state: "idle" | "loading" | "error";
    setOpen: (v: boolean) => void;
    setItems: (v: PrcSupplierHitLike[]) => void;
  };
  export function PrcSupplierCellLookup(props: {
    id: string;
    query: string;
    disabled?: boolean;
    searchSuppliers: PrcSupplierSearchFn;
    portalScopeClassName?: string;
    onQueryChange: (v: string) => void;
    onSelect: (hit: PrcSupplierHitLike) => void;
    onClose: () => void;
  }): JSX.Element;
  export type PrcBaselineLink = {
    supplierCode: string;
    store: string;
    supplierName?: string | null;
    partNumber?: string | null;
    catalogNumber?: string | null;
  };
  export type PrcSupplierTableProps = {
    suppliers: SupplierRow[];
    removeMarks: Set<string>;
    baselineLinks: PrcBaselineLink[];
    requestType: "create" | "update";
    busy?: boolean;
    errorsVisible?: boolean;
    partNumberLabel: string;
    catalogLabel: string;
    searchSuppliers: PrcSupplierSearchFn;
    portalScopeClassName?: string;
    onPatchRow: (rowId: string, patch: Partial<SupplierRow>) => void;
    onToggleSearch: (rowId: string) => void;
    onCloseSearch: (rowId: string) => void;
    onToggleReason: (
      rowId: string,
      flag: "pnReasonOpen" | "catReasonOpen" | "opReasonOpen",
    ) => void;
    onSetReason: (
      rowId: string,
      flag: "pnReason" | "catReason" | "opReason",
      value: string,
    ) => void;
    onDiscardDraft: (rowId: string) => void;
    onMarkRemove: (rowId: string) => void;
    onUndoRemove: (rowId: string) => void;
  };
  export function PrcSupplierTable(
    props: PrcSupplierTableProps,
  ): JSX.Element;
  export type PrcCatalogStatus =
    | "idle" | "loading" | "success" | "empty" | "error";
  export type PrcCatalogView = {
    status: PrcCatalogStatus;
    options: PrcCatalogOption[];
    hasMore: boolean;
    errorKind?: string;
  };
  export const PRC_CATALOG_PAGE_LIMIT: number;
  export type PrcCatalogFetcher = (
    kind: string,
    query: string | undefined,
    signal: AbortSignal | undefined,
    limit: number,
  ) => Promise<{ data?: { items?: unknown[]; hasMore?: boolean } }>;
  export class PrcCatalogStore {
    constructor(fetchCatalog: PrcCatalogFetcher, limit?: number);
    view(path: string): PrcCatalogView;
    getSnapshot(): Map<string, PrcCatalogView>;
    subscribe(listener: () => void): () => void;
    load(path: string, signal?: AbortSignal): void;
    loadAll(paths: Iterable<string>, signal?: AbortSignal): void;
    retry(path: string): void;
    abortAll(): void;
  }


  /* UI-FORM-UNIFICATION-05 — formulário completo PRC compartilhado. */
  export type PrcFormEditContextLink = {
    supplierCode: string;
    store: string;
    supplierName?: string;
    supplierShortName?: string;
    partNumber?: string | null;
    catalogNumber?: string | null;
  };
  export type PrcFormEditContext = {
    status?: string;
    officialCode?: string;
    readAt?: string;
    fingerprint?: string;
    fields: Record<
      string,
      { value: unknown; officialField?: string | null }
    >;
    links: PrcFormEditContextLink[];
    linksComplete?: boolean;
  };
  export type PrcFormDataProvider = {
    fetchReferenceData(signal?: AbortSignal): Promise<PrcReferenceData>;
    fetchCatalog: PrcCatalogFetcher;
    searchSuppliers: PrcSupplierSearchFn;
    fetchEditContext(
      officialCode: string,
    ): Promise<PrcFormEditContext>;
    submitIntake(
      body: PrcIntakeBody,
      idempotencyKey: string,
    ): Promise<{ requestId: string }>;
    uploadAttachment(
      requestId: string,
      file: File,
    ): Promise<unknown>;
    saveDraft?(
      requestId: string,
      expectedVersion: number,
      changes: Array<{
        path: string;
        proposedValue: unknown;
        reason: string;
      }>,
      idempotencyKey: string,
    ): Promise<unknown>;
  };
  export type PrcCaseEditInput = {
    requestId: string;
    expectedVersion: number;
    requestType: "create" | "update";
    draft: Record<string, unknown>;
    changedPaths?: Array<{ path: string; reason?: string }>;
  };
  export type PrcRequestFormProps = {
    source: string;
    dataProvider: PrcFormDataProvider;
    onCancel: () => void;
    onCompleted: (requestId: string) => void;
    portalScopeClassName?: string;
    editCase?: PrcCaseEditInput;
  };
  export function PrcRequestForm(
    props: PrcRequestFormProps,
  ): JSX.Element;

  /* UI-FIX-07 — ficha técnica em leitura + andamento do workflow,
   * mesma composição do Portal Engenharia. */
  export type PrcSheetChange = { path: string; reason: string };
  export type PrcTechnicalSheetViewProps = {
    draft: Record<string, unknown> | null | undefined;
    changedPaths?: PrcSheetChange[];
    specNotes?: Record<string, string | null | undefined> | null;
    baselineFields?: Record<string, unknown> | null;
    suppliersHeaderActions?: React.ReactNode;
    fieldAdornment?: (
      path: string,
      displayValue: string,
    ) => React.ReactNode;
    supplierAdornment?: (
      row: SupplierRow,
      attribute: "partNumber" | "catalogNumber",
    ) => React.ReactNode;
  };
  export function PrcTechnicalSheetView(
    props: PrcTechnicalSheetViewProps,
  ): JSX.Element;
  export function PrcWorkflowProgress(props: {
    status: string;
  }): JSX.Element;

  /* GRANULAR-CORRECTION-09 — devolução/correção granular compartilhada.
   * Apresentação pura: AuthZ/allowlist/CAS ficam na Engineering API. */
  export type PrcCorrectionTargetInput = {
    targetType: "FIELD" | "SUPPLIER_LINK";
    targetPath?: string | null;
    targetAttribute?: string | null;
    supplierKey?: { supplierCode: string; store: string } | null;
    reason: string;
  };
  export type PrcCorrectionTargetWire = {
    id?: string;
    ordinal?: number;
    targetType: string;
    targetPath?: string | null;
    targetAttribute?: string | null;
    supplierKey?: { supplierCode: string; store: string } | null;
    targetKey?: string | null;
    targetLabel?: string | null;
    reason: string;
    baselineValue?: unknown;
    addressedMode?: "changed" | "confirmed" | null;
  };
  export type PrcCorrectionLink = {
    supplierCode: string;
    store: string;
    supplierName?: string | null;
    supplierShortName?: string | null;
    partNumber?: string | null;
    catalogNumber?: string | null;
  };
  export type PrcCorrectionFieldOption = {
    path: string;
    label: string;
    group?: string | null;
  };
  export type PrcFieldSpecLike = {
    path: string;
    kind: string;
    enumValues?: string[] | null;
    maxLength?: number;
    note?: string | null;
  };
  export type PrcReturnedFieldChange = {
    path: string;
    proposedValue: unknown;
    reason: string;
    mode: "changed" | "confirmed";
  };
  export type PrcSupplierEditableAttribute =
    | "partNumber"
    | "catalogNumber";
  export type PrcSupplierCellSelection = {
    link: { selected: boolean; reason: string };
    partNumber: { selected: boolean; reason: string };
    catalogNumber: { selected: boolean; reason: string };
  };
  export type PrcCorrectionSelection = {
    fields: Record<string, { selected: boolean; reason: string }>;
    suppliers: Record<string, PrcSupplierCellSelection>;
  };
  export type PrcCorrectionSelectionSummary = {
    scalarFields: number;
    suppliers: number;
    supplierAttributes: number;
    totalTargets: number;
    firstMissingReason: string | null;
  };
  export type PrcReturnedChangesResult = {
    changes: PrcReturnedFieldChange[] | null;
    error: string;
    errors: PrcCorrectionTargetErrors;
  };
  /* FIX-12 — erros contextuais por alvo (chave estável). */
  export type PrcCorrectionTargetErrors = Record<string, string>;
  export type PrcCorrectionSelectionValidation = {
    targets: PrcCorrectionTargetInput[] | null;
    error: string;
    errors: PrcCorrectionTargetErrors;
  };
  export function correctionFieldTargetKey(path: string): string;
  export function correctionSupplierTargetKey(
    link: { supplierCode: string; store: string },
    cell: "link" | PrcSupplierEditableAttribute,
  ): string;
  export function orderedCorrectionTargetKeys(
    fieldOptions: PrcCorrectionFieldOption[],
    suppliers: PrcCorrectionLink[],
  ): string[];
  export function correctionReasonControlId(
    idPrefix: string,
    targetKey: string,
  ): string;
  export function returnedFieldControlId(
    idPrefix: string,
    targetKey: string,
  ): string;
  export function mapApiFieldsToCorrectionErrors(
    fields: Record<string, string> | null | undefined,
    changes: PrcReturnedFieldChange[],
  ): {
    targetErrors: PrcCorrectionTargetErrors;
    unmapped: Record<string, string>;
  };
  export function firstInvalidCorrectionTarget(
    errors: PrcCorrectionTargetErrors,
    orderedKeys: string[],
  ): string | null;
  export function pruneCorrectionErrors(
    errors: PrcCorrectionTargetErrors,
    selection: PrcCorrectionSelection,
    fieldOptions: PrcCorrectionFieldOption[],
    suppliers: PrcCorrectionLink[],
  ): PrcCorrectionTargetErrors;
  export function emptyCorrectionSelection(): PrcCorrectionSelection;
  export function dedupeCorrectionLinks(
    links: PrcCorrectionLink[] | null | undefined,
  ): PrcCorrectionLink[];
  export function summarizeCorrectionSelection(
    selection: PrcCorrectionSelection,
    suppliers: PrcCorrectionLink[],
  ): PrcCorrectionSelectionSummary;
  export function correctionTargetsFromSelection(
    selection: PrcCorrectionSelection,
    fieldOptions: PrcCorrectionFieldOption[],
    suppliers: PrcCorrectionLink[],
  ): PrcCorrectionSelectionValidation;
  export function returnedSupplierAttrMap(
    targets: PrcCorrectionTargetWire[] | null | undefined,
  ): Map<string, Set<PrcSupplierEditableAttribute>>;
  export function returnedSupplierReasonMap(
    targets: PrcCorrectionTargetWire[] | null | undefined,
  ): Map<string, string>;
  export function fieldTargetsOf(
    targets: PrcCorrectionTargetWire[] | null | undefined,
  ): PrcCorrectionTargetWire[];
  export function hasSupplierTargets(
    targets: PrcCorrectionTargetWire[] | null | undefined,
  ): boolean;
  export function prcSupplierLinkKey(code: string, store: string): string;
  export function buildReturnedChanges(input: {
    targets: PrcCorrectionTargetWire[];
    draft: Record<string, unknown>;
    supplierRows: SupplierRow[];
    fieldValues: Record<string, string>;
    justifications: Record<string, string>;
    supplierJustification?: string;
  }): PrcReturnedChangesResult;
  export function PrcCorrectionTargetSelector(props: {
    fieldOptions: PrcCorrectionFieldOption[];
    suppliers: PrcCorrectionLink[];
    selection: PrcCorrectionSelection;
    onChange: (next: PrcCorrectionSelection) => void;
    busy?: boolean;
    draft?: Record<string, unknown> | null;
    errors?: PrcCorrectionTargetErrors;
    idPrefix?: string;
  }): JSX.Element;
  export function PrcReturnedFieldsEditor(props: {
    targets: PrcCorrectionTargetWire[];
    fieldSpecs: PrcFieldSpecLike[];
    draft: Record<string, unknown>;
    busy?: boolean;
    idPrefix?: string;
    externalErrors?: PrcCorrectionTargetErrors;
    onSubmit: (changes: PrcReturnedFieldChange[]) => void;
    onCancel?: () => void;
  }): JSX.Element;
  /* UI-FIX-03 — rótulos/formatadores de timeline compartilhados */
  export const PRC_EVENT_LABELS: Record<string, string>;
  export function prcPersonLabel(
    subject: string | null | undefined,
    displayName?: string | null,
  ): string;
  export function prcRequesterLabel(requester: {
    subject: string;
    displayName?: string | null;
  }): string;
  export function prcStatusLabel(status: string): string;
  export function prcFormatTimelineDate(
    iso: string | null | undefined,
    fallback?: string,
  ): string;

  export type PrcTimelineEventLike = {
    id: string;
    sequence_number: number;
    event_type: string;
    actor_subject?: string;
    actor_display_name?: string | null;
    actor_email?: string | null;
    occurred_at: string;
    reason?: string | null;
    metadata?: Record<string, unknown> | null;
    previous_status?: string | null;
    next_status?: string | null;
  };
  export type PrcTimelineItemView = {
    id: string;
    title: string;
    occurredAt: string;
    timeLabel: string;
    actorLabel: string;
    actorUserId: string | null;
    actorEmail: string | null;
    transition: string | null;
    reasonText: string | null;
    channel: string | null;
    metaText: string;
  };
  export function prcTimelineItemViews(
    events: PrcTimelineEventLike[],
  ): PrcTimelineItemView[];
}

