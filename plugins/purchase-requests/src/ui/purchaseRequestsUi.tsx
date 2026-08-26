import {
  createDashboardEmptyState,
  createDashboardFiltersKit,
  createDashboardLoadingState,
  createDashboardMultiSelectField,
  createDashboardSectionCard,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createHostContainedModalShell,
  createHostContainedDrawerShell,
  createTimeline,
  emptyStateCardBemClasses,
  loadingStateCardBemClasses,
  multiSelectBemClasses,
  sectionCardPacBemClasses,
  stateBannerBemClasses,
  type MultiSelectFieldLabels,
} from "@delpi/plugin-ui/index";

const PREFIX = "pr";

export const PurchaseRequestsSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});

export const PurchaseRequestsStatusBadge = createDashboardStatusBadge({ prefix: PREFIX });

export const PurchaseRequestsStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PREFIX),
});

export const PurchaseRequestsEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(PREFIX),
  defaultMessage: "Nenhuma solicitação encontrada para os filtros selecionados.",
});

export const PurchaseRequestsLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(PREFIX),
  defaultMessage: "Carregando solicitações…",
});

export const PurchaseRequestsTimeline = createTimeline({ prefix: PREFIX });

export const PurchaseRequestsModal = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: "dashboard-purchase-requests",
  containedLayout: "dialog",
  variant: "wide",
});

export const PurchaseRequestsDrawer = createHostContainedDrawerShell({
  prefix: PREFIX,
  portalScopeClassName: "dashboard-purchase-requests",
});

const filtersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtros de solicitações de compra" },
  portalScopeClassName: "dashboard-purchase-requests",
});

export const PurchaseRequestsFiltersRow = filtersKit.FiltersRow;
export const PurchaseRequestsFilterInputField = filtersKit.FilterInputField;
export const PurchaseRequestsFilterSelectField = filtersKit.FilterSelectField;

const MULTISELECT_LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar solicitante…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhum solicitante encontrado.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

export const PurchaseRequestsFilterMultiSelectField = createDashboardMultiSelectField({
  prefix: PREFIX,
  labels: MULTISELECT_LABELS,
  classNames: {
    ...multiSelectBemClasses(PREFIX),
    root: "pr-field pr-field--multi-select",
  },
  portalScopeClassName: "dashboard-purchase-requests",
});
