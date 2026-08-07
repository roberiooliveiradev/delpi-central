import {
  createDashboardAlertQueue,
  createDashboardAttachmentFileList,
  createDashboardAttachmentPreviewStrip,
  createDashboardDetailCard,
  createDashboardDetailFieldGrid,
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
  createHostContainedDrawerShell,
  createHostContainedModalShell,
  createDashboardInlineMeter,
  createDashboardHorizontalTimeline,
  createFilterBarShell,
  dateFieldBemClasses,
  createDashboardPageHero,
  createDashboardTopBar,
  createDashboardViewTransition,
  createDashboardWorklistItem,
  createInitialsAvatar,
  createTimeline,
  createDashboardUnderlineNav,
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
  worklistItemBemClasses,
  timelineBemClasses,
  underlineNavBemClasses,
  withBemModifier,
} from "@delpi/plugin-ui/index";

export const UI_PREFIX = "cm";
export const CM_PORTAL_SCOPE = "dashboard-commercial";

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
export const CommercialPageHero = createDashboardPageHero({ prefix: UI_PREFIX });
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

export const CommercialDrawerShell = createHostContainedDrawerShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  closeAriaLabel: "Fechar painel",
  backdropAriaLabel: "Fechar painel",
});

/** Modal workbench (fill) — detalhe de linha / painéis amplos sem cobrir sidebar. */
export const CommercialWorkbenchModal = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CM_PORTAL_SCOPE,
  containedLayout: "fill",
  variant: "page",
  closeAriaLabel: "Fechar",
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
