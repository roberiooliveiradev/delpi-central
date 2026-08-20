import {
  ActionButton,
  createDashboardAlertQueue,
  createDashboardAttachmentFileList,
  createDashboardAttachmentPreviewStrip,
  createDashboardDetailCard,
  createDashboardEmptyState,
  createDashboardDetailFieldGrid,
  createDashboardSectionCard,
  createDashboardStatusBadge,
  createDashboardFileDropzone,
  createDashboardFiltersKit,
  createDashboardLoadingActivityCard,
  createDashboardMultiSelectField,
  createDashboardNavigationCard,
  createDashboardSectionRouteCard,
  createDashboardCatalogSearchBar,
  createDashboardCommandPalette,
  createDashboardHubChipRow,
  createDashboardRouteChip,
  createDashboardScopeChipBar,
  createDashboardSelectField,
  createDashboardTextAreaField,
  createDashboardDateField,
  createDashboardTextField,
  createDashboardTitleWithHelp,
  createDashboardStateBanner,
  createCompactPagination,
  createDashboardInlineMeter,
  createDashboardCompareSparkline,
  createDashboardTrendDelta,
  createDashboardHorizontalTimeline,
  createDashboardOrgMembershipFlow,
  createDashboardDataListToolbar,
  createDashboardDataCardsGrid,
  createDashboardDataCardsSortBar,
  createDashboardInteractiveDataCard,
  createDashboardKanbanBoard,
  createDashboardTableFontSizeControls,
  createFilterBarShell,
  createHostContainedModalShell,
  createHostContainedDrawerShell,
  dateFieldBemClasses,
  createDashboardPageHero,
  createDashboardMetricStrip,
  createDashboardPagePath,
  createDashboardDataRecordCard,
  ExcelExportButton,
  usePersistedViewLayout,
  useTableFontSize,
  createDashboardTopBar,
  createDashboardViewTransition,
  createDashboardWorklistItem,
  createMetricKpiCard,
  createSimpleKpiCard,
  createDashboardKpiCard,
  DataCellValue,
  DataTable,
  SpeedometerGauge,
  HorizontalValueBars,
  createInitialsAvatar,
  createDashboardAvatarStack,
  createDashboardSegmentToggle,
  createTimeline,
  createDashboardUnderlineNav,
  createDashboardChartToolbarKit,
  createDashboardTabularExportButtons,
  createDashboardMentionText,
  createDashboardMentionMenu,
  createDashboardMentionComposer,
  createDashboardEmojiInsertMenu,
  createDashboardMessageThread,
  createDashboardEntityUnfurlCard,
  createDashboardReactionBar,
  createDashboardReactionQuickBar,
  createDashboardRoomInboxList,
  createDashboardRoomHeader,
  createDashboardRoomContextPanel,
  createDashboardRoomSidePanel,
  createDashboardResizableColumns,
  createDashboardConversationFileDropLayer,
  useChartGranularitySelection,
  attachmentFileListBemClasses,
  attachmentPreviewStripBemClasses,
  catalogSearchBarBemClasses,
  dataTableBemClasses,
  detailCardRichBemClasses,
  emptyStateCardBemClasses,
  fileDropzoneBemClasses,
  filtersRowBemClasses,
  inlineMeterBemClasses,
  compareSparklineBemClasses,
  trendDeltaBemClasses,
  navigationCardBemClasses,
  pageHeaderBrandBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  statusBadgeBemClasses,
  textAreaFieldBemClasses,
  textFieldBemClasses,
  titleWithHelpBemClasses,
  alertQueueBemClasses,
  scopeChipBarBemClasses,
  SectionHintLabel,
  TableColumnVisibilityMenu,
  worklistItemBemClasses,
  timelineBemClasses,
  underlineNavBemClasses,
  withBemModifier,
  delpiUiClass,
  type DataCellValueProps,
  type DashboardDataTableProps,
  type SpeedometerGaugeProps,
  type HorizontalValueBarsProps,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps, type KeyboardEvent, type ReactNode } from "react";

export type { DataTableColumn, DataTableColumnWidths } from "@delpi/plugin-ui/index";
export { usePersistedViewLayout, useTableFontSize, useChartGranularitySelection };

export const UI_PREFIX = "cm";
export const CM_PORTAL_SCOPE = "dashboard-commercial";

export const OPEN_ORDERS_TABLE_FONT_SIZE_STORAGE_KEY =
  "commercial:open-orders:table-font-size:v1";
export const OPEN_ORDERS_TABLE_FONT_SIZE_LEGACY_KEYS = [
  "pedidos-venda-abertos:table-font-size:v1",
] as const;
export const CUSTOMERS_TABLE_FONT_SIZE_STORAGE_KEY =
  "commercial:customers:table-font-size:v1";
export const CUSTOMERS_TABLE_FONT_SIZE_LEGACY_KEYS = [
  "commercial:open-orders:table-font-size:v1",
  "pedidos-venda-abertos:table-font-size:v1",
] as const;
export const OPEN_ORDERS_LAYOUT_STORAGE_KEY = "commercial:open-orders:layout";
export const CUSTOMERS_LAYOUT_STORAGE_KEY = "commercial:customers:layout";
export const PORTFOLIOS_LAYOUT_STORAGE_KEY = "commercial:seller-portfolios:layout";

export const cmPageHeaderClassNames = pageHeaderBrandBemClasses(UI_PREFIX);
export const cmNavCardClassNames = navigationCardBemClasses(UI_PREFIX);
export const cmSectionRouteCardClassNames = sectionRouteCardBemClasses(UI_PREFIX);
export const cmCatalogSearchClassNames = catalogSearchBarBemClasses(UI_PREFIX);
export const cmSectionCardClassNames = sectionCardPacBemClasses(UI_PREFIX);
export const cmDataTableClassNames = dataTableBemClasses(UI_PREFIX);
export const cmEmptyStateClassNames = emptyStateCardBemClasses(UI_PREFIX);
export const cmStateBannerClassNames = stateBannerBemClasses(UI_PREFIX);
export const cmStatusBadgeClassNames = statusBadgeBemClasses(UI_PREFIX);
export const cmInlineMeterClassNames = inlineMeterBemClasses(UI_PREFIX);
export const CommercialInlineMeter = createDashboardInlineMeter({ prefix: UI_PREFIX });
export const cmCompareSparklineClassNames = compareSparklineBemClasses(UI_PREFIX);
export const CommercialCompareSparkline = createDashboardCompareSparkline({
  prefix: UI_PREFIX,
});
export const CommercialTrendDelta = createDashboardTrendDelta({ prefix: UI_PREFIX });
export const CommercialHorizontalTimeline = createDashboardHorizontalTimeline({
  prefix: UI_PREFIX,
});
export const CommercialOrgMembershipFlow = createDashboardOrgMembershipFlow({
  prefix: UI_PREFIX,
});
export const cmAlertQueueClassNames = alertQueueBemClasses(UI_PREFIX);
export const cmScopeChipBarClassNames = scopeChipBarBemClasses(UI_PREFIX);
export const cmWorklistItemClassNames = worklistItemBemClasses(UI_PREFIX);
export const cmTimelineClassNames = timelineBemClasses(UI_PREFIX);

export const CommercialNavigationCard = createDashboardNavigationCard({
  classNames: cmNavCardClassNames,
});
export const CommercialSectionRouteCard = createDashboardSectionRouteCard({
  classNames: cmSectionRouteCardClassNames,
});
export const CommercialCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: cmCatalogSearchClassNames,
});
export const CommercialHubChipRow = createDashboardHubChipRow({ prefix: UI_PREFIX });
export const CommercialRouteChip = createDashboardRouteChip({ prefix: UI_PREFIX });
export const CommercialCommandPalette = createDashboardCommandPalette({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
});
export const CommercialTopBar = createDashboardTopBar({ prefix: UI_PREFIX });
export const CommercialActionButton = ActionButton;
export const CommercialExcelExportButton = ExcelExportButton;
export const CommercialSectionHintLabel = SectionHintLabel;
export const CommercialTableColumnVisibilityMenu = TableColumnVisibilityMenu;
export function CommercialDataCellValue({
  labels,
  ...props
}: DataCellValueProps) {
  return createElement(DataCellValue, {
    ...props,
    labels: {
      nullLabel: "Dado indisponível",
      emptyLabel: "Dado indisponível",
      missingLabel: "Dado indisponível",
      ...labels,
    },
  });
}
export const CommercialPageHeroBase = createDashboardPageHero({ prefix: UI_PREFIX });
/** Default `density="compact"` — liberar viewport nas listas do portal. */
export function CommercialPageHero(
  props: ComponentProps<typeof CommercialPageHeroBase>,
) {
  return createElement(CommercialPageHeroBase, { density: "compact", ...props });
}
export const CommercialMetricStrip = createDashboardMetricStrip({ prefix: UI_PREFIX });
export const CommercialStatusBadge = createDashboardStatusBadge({ prefix: UI_PREFIX });
export const CommercialPagePath = createDashboardPagePath({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
});
export const CommercialHostDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  containedLayout: "dialog",
});
export const CommercialHostDrawer = createHostContainedDrawerShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  closeAriaLabel: "Fechar",
  backdropAriaLabel: "Fechar painel",
});
export const CommercialDataRecordCard = createDashboardDataRecordCard({
  prefix: UI_PREFIX,
});
export const CommercialTableFontSizeControls = createDashboardTableFontSizeControls({
  prefix: UI_PREFIX,
});
export const CommercialDataListToolbar = createDashboardDataListToolbar({
  prefix: UI_PREFIX,
});
export const CommercialDataCardsGrid = createDashboardDataCardsGrid({
  prefix: UI_PREFIX,
});
export const CommercialDataCardsSortBar = createDashboardDataCardsSortBar({
  prefix: UI_PREFIX,
});
export const CommercialInteractiveDataCard = createDashboardInteractiveDataCard({
  prefix: UI_PREFIX,
});
export const CommercialKanbanBoard = createDashboardKanbanBoard({
  prefix: UI_PREFIX,
});
export const CommercialEmptyState = createDashboardEmptyState({
  classNames: {
    ...cmEmptyStateClassNames,
    withTitle: true,
  },
  defaultMessage: "",
});
const CommercialMetricKpiBase = createMetricKpiCard(UI_PREFIX);
type CommercialMetricCardProps = {
  label: string;
  value: string;
  hint?: ReactNode;
  titleHint?: string;
  icon?: ReactNode;
  hero?: boolean;
  tone?: "default" | "danger";
  loading?: boolean;
  onClick?: () => void;
  "aria-label"?: string;
};
export function CommercialMetricCard({
  label,
  value,
  hint,
  titleHint,
  icon,
  hero = false,
  tone = "default",
  loading = false,
  onClick,
  "aria-label": ariaLabel,
}: CommercialMetricCardProps) {
  const card = createElement(CommercialMetricKpiBase, {
    label,
    value: loading ? "…" : value,
    hint,
    titleHint,
    icon,
    tone: tone === "danger" ? "negative" : "default",
    fitValue: hero,
    className: hero ? "cm-kpi-card--wide" : undefined,
  });
  if (!onClick) return card;
  // `div` + role="button": MetricKpiCard pode embutir HelpTooltip (também <button>).
  // Wrapper <button> aninhado quebra HTML e dispara hydration error no React.
  return createElement(
    "div",
    {
      role: "button",
      tabIndex: 0,
      className: "cm-metric-card-button",
      onClick,
      onKeyDown: (event: KeyboardEvent<HTMLDivElement>) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      },
      "aria-label": ariaLabel ?? label,
    },
    card,
  );
}

/** KPI acionável (SimpleKpiCard do kit) — preferir CommercialMetricCard em telas novas. */
export const CommercialKpiCard = createSimpleKpiCard(UI_PREFIX, {
  withBody: true,
  withSubtitle: true,
  layout: "iconEnd",
});

/** KPI com Meta / Nota IDD / badges — paridade dashboard-commercial. */
export const CommercialDashboardKpiCard = createDashboardKpiCard({
  prefix: UI_PREFIX,
  labels: {
    goalPrefix: "Meta",
    iddScorePrefix: "Nota IDD",
    badgesStatus: "Escopo e desempenho em relação à meta",
  },
});

/** Thin wrapper do kit — herda `DashboardDataTableProps` (incl. expand `expandedRowKey` / `renderExpandedRow`). */
export function CommercialDataTable<T>(props: DashboardDataTableProps<T>) {
  return createElement(DataTable<T>, {
    classNames: cmDataTableClassNames,
    labels: cmDataTableLabels,
    ...props,
  });
}
export const CommercialViewTransition = createDashboardViewTransition({
  prefix: UI_PREFIX,
});
export const CommercialUnderlineNav = createDashboardUnderlineNav({ prefix: UI_PREFIX });
export const cmUnderlineNavClassNames = underlineNavBemClasses(UI_PREFIX);

export const cmSectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

export const CommercialSectionCard = createDashboardSectionCard({
  classNames: cmSectionCardClassNames,
  labels: cmSectionLabels,
});

export const CommercialFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(UI_PREFIX, "file-dropzone"),
  labels: {
    title: "Arraste um arquivo ou clique para selecionar",
    hint: "PDF, imagem, TXT, Word ou Excel · máx. 10 MB",
  },
});

export const CommercialAttachmentFileList = createDashboardAttachmentFileList({
  classNames: attachmentFileListBemClasses(UI_PREFIX),
  labels: {
    open: "Abrir",
    download: "Baixar",
    remove: "Remover",
    empty: "Nenhum anexo nesta tarefa.",
  },
});

export const CommercialAttachmentPreviewStrip = createDashboardAttachmentPreviewStrip({
  classNames: attachmentPreviewStripBemClasses(UI_PREFIX),
  labels: {
    empty: "Nenhum anexo nesta tarefa.",
    openAriaLabel: (fileName: string) => `Abrir prévia de ${fileName}`,
    removeAriaLabel: (fileName: string) => `Remover ${fileName}`,
  },
});

export const CommercialTitleWithHelp = createDashboardTitleWithHelp({
  classNames: titleWithHelpBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});

export const cmDataTableLabels = {
  emptyMessage: "Sem linhas para exibir.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

const loadingLabels = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
};

export const CommercialLoadingCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: loadingLabels,
});

export const CommercialAlertQueue = createDashboardAlertQueue({ prefix: UI_PREFIX });
export const CommercialScopeChipBar = createDashboardScopeChipBar({ prefix: UI_PREFIX });
export const CommercialWorklistItem = createDashboardWorklistItem({ prefix: UI_PREFIX });
export const CommercialActivityTimeline = createTimeline({ prefix: UI_PREFIX });

export const CommercialStateBanner = createDashboardStateBanner({
  classNames: cmStateBannerClassNames,
});

export const CommercialFilterBarShell = createFilterBarShell({
  prefix: UI_PREFIX,
  withGrid: true,
  defaultAriaLabel: "Filtros",
});

export const CommercialPagination = createCompactPagination({
  prefix: UI_PREFIX,
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} de ${totalPages} · ${total.toLocaleString("pt-BR")} registro(s)`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação de pedidos",
  },
});

const { field: cmSelectFieldClasses, control: cmSelectControlClasses } =
  selectFieldPacClasses(UI_PREFIX);

export const CommercialSelectField = createDashboardSelectField({
  field: cmSelectFieldClasses,
  control: cmSelectControlClasses,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "Todos",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) => (label ? `Buscar em ${label}` : "Buscar opções"),
    },
  },
});

export const CommercialMultiSelectField = createDashboardMultiSelectField({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  labels: {
    emptyLabel: "Nenhum selecionado",
    searchPlaceholder: "Buscar…",
    selectVisible: "Selecionar visíveis",
    clear: "Limpar",
    emptyOptions: "Nenhuma opção encontrada.",
    multipleSelected: (count: number) => `${count} selecionado(s)`,
  },
});

export const CommercialTextField = createDashboardTextField({
  classNames: textFieldBemClasses(UI_PREFIX),
});

export const CommercialDateField = createDashboardDateField({
  classNames: dateFieldBemClasses(UI_PREFIX),
});

export const CommercialTextAreaField = createDashboardTextAreaField({
  classNames: textAreaFieldBemClasses(UI_PREFIX),
});

export const CommercialDetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: UI_PREFIX,
  labels: {
    fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
  },
});

export const CommercialDetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});

export const CommercialAvatar = createInitialsAvatar(UI_PREFIX);
export const CommercialAvatarStack = createDashboardAvatarStack(UI_PREFIX);
export const CommercialSegmentToggle = createDashboardSegmentToggle(UI_PREFIX);

export { CommercialEntityLink } from "../components/CommercialEntityLink";
export type { CommercialEntityLinkProps } from "../components/CommercialEntityLink";

export const cmFiltersKit = createDashboardFiltersKit({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  labels: {
    filtersAriaLabel: "Filtros",
  },
});

export const cmFiltersRowClassNames = filtersRowBemClasses(UI_PREFIX);
export const cmFiltersRowWideClassNames = {
  ...cmFiltersRowClassNames,
  filterBox: withBemModifier(cmFiltersRowClassNames.filterBox, "wide"),
};

const commercialChartToolbarKit = createDashboardChartToolbarKit({
  prefix: UI_PREFIX,
  labels: {
    groupAriaLabel: "Agrupamento do gráfico",
    exportSeries: "Exportar série",
    exportSeriesAriaLabel: "Exportar série do gráfico em CSV",
  },
});

export const CommercialChartToolbar = commercialChartToolbarKit.ChartToolbar;
export const CommercialChartGranularityToggle =
  commercialChartToolbarKit.ChartGranularityToggle;

export const CommercialTabularExportButtons = createDashboardTabularExportButtons({
  prefix: UI_PREFIX,
  groupAriaLabel: "Exportar dados",
});

export const cmSpeedometerGaugeRowClass = delpiUiClass(
  `${UI_PREFIX}-speedometer-gauge-row`,
  "delpi-ui-speedometer-gauge-row",
);

export function CommercialSpeedometerGauge(props: Omit<SpeedometerGaugeProps, "prefix">) {
  return createElement(SpeedometerGauge, { ...props, prefix: UI_PREFIX });
}

export function CommercialHorizontalValueBars(
  props: Omit<HorizontalValueBarsProps, "prefix">,
) {
  return createElement(HorizontalValueBars, { ...props, prefix: UI_PREFIX });
}

/** Interaction room — kit factories (dual-class `cm` + `delpi-ui-*`). */
export const CommercialMentionText = createDashboardMentionText(UI_PREFIX);
export const CommercialMentionMenu = createDashboardMentionMenu(UI_PREFIX);
export const CommercialMentionComposer = createDashboardMentionComposer(UI_PREFIX);
export const CommercialEmojiInsertMenu = createDashboardEmojiInsertMenu(UI_PREFIX);
export const CommercialMessageThread = createDashboardMessageThread(UI_PREFIX);
export const CommercialEntityUnfurlCard = createDashboardEntityUnfurlCard(UI_PREFIX);
export const CommercialReactionBar = createDashboardReactionBar(UI_PREFIX);
export const CommercialReactionQuickBar = createDashboardReactionQuickBar(UI_PREFIX);
export const CommercialRoomInboxList = createDashboardRoomInboxList(UI_PREFIX);
export const CommercialRoomHeader = createDashboardRoomHeader(UI_PREFIX);
export const CommercialRoomContextPanel = createDashboardRoomContextPanel(UI_PREFIX);
export const CommercialRoomSidePanel = createDashboardRoomSidePanel(UI_PREFIX);
export const CommercialResizableColumns = createDashboardResizableColumns(UI_PREFIX);
export const CommercialConversationFileDropLayer =
  createDashboardConversationFileDropLayer(UI_PREFIX);
