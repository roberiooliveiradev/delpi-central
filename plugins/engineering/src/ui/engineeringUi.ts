import {
  createDashboardEmptyState,
  createDashboardLoadingState,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardStateBanner,
  emptyStateCardBemClasses,
  loadingStateCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  stateBannerBemClasses,
} from "@delpi/plugin-ui/index";

/** Prefixo BEM dual-class do MFE (pares com `.delpi-ui-*` no remote). */
export const ENG_UI_PREFIX = "engineering";
export const ENG_PORTAL_SCOPE = "portal-engineering";

export const EngineeringPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(ENG_UI_PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const EngineeringSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(ENG_UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const EngineeringStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(ENG_UI_PREFIX),
});

export const EngineeringEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(ENG_UI_PREFIX),
  defaultMessage: "Nenhum item no momento.",
});

export const EngineeringLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(ENG_UI_PREFIX),
  defaultMessage: "Carregando…",
});
