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
  createDashboardScopeChipBar,
  createDashboardSelectField,
  createDashboardTextAreaField,
  createDashboardDateField,
  createDashboardTextField,
  createDashboardTitleWithHelp,
  createDashboardStateBanner,
  createCompactPagination,
  createDashboardInlineMeter,
  createDashboardHorizontalTimeline,
  createDashboardDataListToolbar,
  createDashboardDataCardsGrid,
  createDashboardDataCardsSortBar,
  createDashboardInteractiveDataCard,
  createDashboardTableFontSizeControls,
  createFilterBarShell,
  createHostContainedModalShell,
  dateFieldBemClasses,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardDataRecordCard,
  ExcelExportButton,
  usePersistedViewLayout,
  useTableFontSize,
  createDashboardTopBar,
  createDashboardViewTransition,
  createDashboardWorklistItem,
  createMetricKpiCard,
  DataCellValue,
  DataTable,
  createInitialsAvatar,
  createTimeline,
  createDashboardUnderlineNav,
  createDashboardChartToolbarKit,
  useChartGranularitySelection,
  attachmentFileListBemClasses,
  attachmentPreviewStripBemClasses,
  dataTableBemClasses,
  detailCardRichBemClasses,
  emptyStateCardBemClasses,
  fileDropzoneBemClasses,
  filtersRowBemClasses,
  inlineMeterBemClasses,
  navigationCardBemClasses,
  pageHeaderBrandBemClasses,
  sectionCardPacBemClasses,
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
  type DataCellValueProps,
  type DashboardDataTableProps,
} from "@delpi/plugin-ui/index";
import { createElement, type ReactNode } from "react";

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
export const cmSectionCardClassNames = sectionCardPacBemClasses(UI_PREFIX);
export const cmDataTableClassNames = dataTableBemClasses(UI_PREFIX);
export const cmEmptyStateClassNames = emptyStateCardBemClasses(UI_PREFIX);
export const cmStateBannerClassNames = stateBannerBemClasses(UI_PREFIX);
export const cmStatusBadgeClassNames = statusBadgeBemClasses(UI_PREFIX);
export const cmInlineMeterClassNames = inlineMeterBemClasses(UI_PREFIX);
export const CommercialInlineMeter = createDashboardInlineMeter({ prefix: UI_PREFIX });
export const CommercialHorizontalTimeline = createDashboardHorizontalTimeline({
  prefix: UI_PREFIX,
});
export const cmAlertQueueClassNames = alertQueueBemClasses(UI_PREFIX);
export const cmScopeChipBarClassNames = scopeChipBarBemClasses(UI_PREFIX);
export const cmWorklistItemClassNames = worklistItemBemClasses(UI_PREFIX);
export const cmTimelineClassNames = timelineBemClasses(UI_PREFIX);

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
export const CommercialPageHero = createDashboardPageHero({ prefix: UI_PREFIX });
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
}: CommercialMetricCardProps) {
  return createElement(CommercialMetricKpiBase, {
    label,
    value: loading ? "…" : value,
    hint,
    titleHint,
    icon,
    tone: tone === "danger" ? "negative" : "default",
    fitValue: hero,
    className: hero ? "cm-kpi-card--wide" : undefined,
  });
}

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
