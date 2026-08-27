import {
  createDashboardCreatableMultiSelectField,
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
  multiSelectCreatablePacClasses,
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
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

const CREATABLE_MULTISELECT_LABELS = {
  ...MULTISELECT_LABELS,
  emptyLabel: "Todos",
  searchPlaceholder: "Digite o código do CC…",
  emptyOptions: "Digite o código e pressione Enter.",
  emptyOptionsCreatable: "Pressione Enter ou use a opção «Adicionar».",
  createOption: (query: string) => `Adicionar «${query.trim()}»`,
  searchAriaLabel: (label: string) => `Buscar ou adicionar em ${label}`,
  removeTagAriaLabel: (value: string) => `Remover ${value}`,
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

export const PurchaseRequestsFilterCreatableMultiSelectField = createDashboardCreatableMultiSelectField({
  prefix: PREFIX,
  labels: CREATABLE_MULTISELECT_LABELS,
  classNames: {
    ...multiSelectCreatablePacClasses(PREFIX),
    root: "pr-field pr-field--multi-select",
  },
  portalScopeClassName: "dashboard-purchase-requests",
});
