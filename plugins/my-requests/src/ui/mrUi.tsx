import {
  createCompactPagination,
  createDashboardDetailFieldGrid,
  createDashboardEmptyState,
  createDashboardFileDropzone,
  createDashboardFiltersKit,
  createDashboardFormActions,
  createDashboardLoadingState,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardSegmentToggle,
  createDashboardSelectField,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextField,
  createHostContainedModalShell,
  createTimeline,
  emptyStateCardBemClasses,
  fileDropzoneBemClasses,
  formActionsBemClasses,
  loadingStateCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textFieldPacClasses,
} from "@delpi/plugin-ui/index";

/** Prefixo BEM dual-class do MFE (pares com `.delpi-ui-*` no remote). */
export const MR_UI_PREFIX = "my-requests";
export const MR_PORTAL_SCOPE = "dashboard-my-requests";

export const MyRequestsPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(MR_UI_PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const MyRequestsSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(MR_UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const MyRequestsFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(MR_UI_PREFIX),
});

export const MyRequestsStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(MR_UI_PREFIX),
});

export const MyRequestsEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(MR_UI_PREFIX),
  defaultMessage: "Nenhum item encontrado.",
});

export const MyRequestsLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(MR_UI_PREFIX),
  defaultMessage: "Carregando…",
});

export const MyRequestsTimeline = createTimeline({ prefix: MR_UI_PREFIX });

export const MyRequestsStatusBadge = createDashboardStatusBadge({
  prefix: MR_UI_PREFIX,
});

export const TextField = createDashboardTextField({
  classNames: textFieldPacClasses(MR_UI_PREFIX),
});

const selectClasses = selectFieldPacClasses(MR_UI_PREFIX);

export const SelectField = createDashboardSelectField({
  ...selectClasses,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "—",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) =>
        label ? `Buscar em ${label}` : "Buscar opções",
    },
  },
});

export const SegmentToggle = createDashboardSegmentToggle(MR_UI_PREFIX);

export const DetailFields = createDashboardDetailFieldGrid({
  prefix: MR_UI_PREFIX,
  labels: {
    fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
  wrapLabels: true,
});

const filtersKit = createDashboardFiltersKit({
  prefix: MR_UI_PREFIX,
  labels: { filtersAriaLabel: "Filtros de solicitações" },
  portalScopeClassName: MR_PORTAL_SCOPE,
});

export const MyRequestsFiltersRow = filtersKit.FiltersRow;
export const MyRequestsFilterSelectField = filtersKit.FilterSelectField;
export const MyRequestsFilterInputField = filtersKit.FilterInputField;

export const MyRequestsCompactPagination = createCompactPagination({
  prefix: MR_UI_PREFIX,
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} / ${totalPages} · ${total} solicitações`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação das solicitações",
  },
});

export const MyRequestsModal = createHostContainedModalShell({
  prefix: MR_UI_PREFIX,
  portalScopeClassName: MR_PORTAL_SCOPE,
  containedLayout: "dialog",
});

export const MyRequestsFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(MR_UI_PREFIX, "file-dropzone"),
  labels: {
    title: "Arraste um arquivo ou clique para selecionar",
    hint: "PDF ou imagem · máx. 25 MB",
  },
});
