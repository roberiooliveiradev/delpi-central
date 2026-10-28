import {
  ActionButton,
  catalogSearchBarBemClasses,
  createDashboardCatalogSearchBar,
  createDashboardCommandPalette,
  createDashboardEmptyState,
  createDashboardEventsSection,
  createDashboardKpiCard,
  createDashboardLoadingState,
  createDashboardMetricStrip,
  createDashboardMultiSelectField,
  createDashboardDateField,
  createDashboardQuickPeriodSelector,
  dateFieldBemClasses,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardRecentAccessStrip,
  createDashboardSectionCard,
  createDashboardSectionRouteCard,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTopBar,
  createDashboardTopBarFavoritesStrip,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarUserIdentity,
  createDashboardUserManual,
  createDashboardViewTransition,
  emptyStateCardBemClasses,
  loadingStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  stateBannerBemClasses,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps } from "react";

/** Prefixo BEM dual-class do MFE (pares com `.delpi-ui-*` no remote). */
export const ENG_UI_PREFIX = "engineering";
export const ENG_PORTAL_SCOPE = "portal-engineering";

export const EngineeringTopBar = createDashboardTopBar({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringTopBarSearchTrigger =
  createDashboardTopBarSearchTrigger({ prefix: ENG_UI_PREFIX });

export const EngineeringTopBarFavoritesStrip =
  createDashboardTopBarFavoritesStrip({ prefix: ENG_UI_PREFIX });

export const EngineeringTopBarUserIdentity =
  createDashboardTopBarUserIdentity({ prefix: ENG_UI_PREFIX });

export const EngineeringCommandPalette = createDashboardCommandPalette({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
});

export const EngineeringPageHeroBase = createDashboardPageHero({
  prefix: ENG_UI_PREFIX,
});
/** Default `density="compact"` — mesmo padrão do Portal Comercial:
 *  libera viewport nas páginas sem trocar tokens/tipografia. */
export function EngineeringPageHero(
  props: ComponentProps<typeof EngineeringPageHeroBase>,
) {
  return createElement(EngineeringPageHeroBase, {
    density: "compact",
    ...props,
  });
}

export const EngineeringMetricStrip = createDashboardMetricStrip({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringKpiCard = createDashboardKpiCard({
  prefix: ENG_UI_PREFIX,
  labels: {
    goalPrefix: "Meta",
    iddScorePrefix: "Nota IDD",
    badgesStatus: "Escopo e desempenho em relação à meta",
  },
});

export const EngineeringQuickPeriodSelector =
  createDashboardQuickPeriodSelector(ENG_UI_PREFIX);

export const EngineeringDateField = createDashboardDateField({
  classNames: dateFieldBemClasses(ENG_UI_PREFIX),
});

export const EngineeringMultiSelectField = createDashboardMultiSelectField({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
  labels: {
    emptyLabel: "Todas",
    searchPlaceholder: "Buscar…",
    selectVisible: "Selecionar visíveis",
    clear: "Limpar",
    emptyOptions: "Nenhuma opção disponível.",
    multipleSelected: (count) => `${count} selecionadas`,
    searchAriaLabel: (label) => `Buscar em ${label}`,
    selectedCountLabel: (count) => `${count} unidades selecionadas`,
    removeTagAriaLabel: (value) => `Remover ${value}`,
  },
});

export const EngineeringEventsSection = createDashboardEventsSection({
  prefix: ENG_UI_PREFIX,
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const EngineeringCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: catalogSearchBarBemClasses(ENG_UI_PREFIX),
});

export const EngineeringRecentAccessStrip = createDashboardRecentAccessStrip({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringSectionRouteCard = createDashboardSectionRouteCard({
  classNames: sectionRouteCardBemClasses(ENG_UI_PREFIX),
});

export const EngineeringUserManual = createDashboardUserManual({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringPagePath = createDashboardPagePath({
  prefix: ENG_UI_PREFIX,
  portalScopeClassName: ENG_PORTAL_SCOPE,
});

export const EngineeringViewTransition = createDashboardViewTransition({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringStatusBadge = createDashboardStatusBadge({
  prefix: ENG_UI_PREFIX,
});

export const EngineeringActionButton = ActionButton;

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


