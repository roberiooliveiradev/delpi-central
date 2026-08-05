import {
  createDashboardLoadingActivityCard,
  dataTableBemClasses,
  emptyStateCardBemClasses,
  navigationCardBemClasses,
  pageHeaderBrandBemClasses,
  sectionCardPacBemClasses,
  stateBannerBemClasses,
  statusBadgeBemClasses,
} from "@delpi/plugin-ui/index";

export const UI_PREFIX = "cm";

export const cmPageHeaderClassNames = pageHeaderBrandBemClasses(UI_PREFIX);
export const cmNavCardClassNames = navigationCardBemClasses(UI_PREFIX);
export const cmSectionCardClassNames = sectionCardPacBemClasses(UI_PREFIX);
export const cmDataTableClassNames = dataTableBemClasses(UI_PREFIX);
export const cmEmptyStateClassNames = emptyStateCardBemClasses(UI_PREFIX);
export const cmStateBannerClassNames = stateBannerBemClasses(UI_PREFIX);
export const cmStatusBadgeClassNames = statusBadgeBemClasses(UI_PREFIX);

export const cmSectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

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
