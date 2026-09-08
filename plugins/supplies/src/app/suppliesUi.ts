import {
  ActionButton,
  HelpTooltip,
  createDashboardCatalogSearchBar,
  createDashboardCommandPalette,
  createDashboardEmptyState,
  createDashboardHubChipRow,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardRouteChip,
  createDashboardSectionCard,
  createDashboardSectionRouteCard,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTopBar,
  createDashboardTopBarSearchTrigger,
  createDashboardViewTransition,
  createInitialsAvatar,
  catalogSearchBarBemClasses,
  emptyStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  stateBannerBemClasses,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps } from "react";

export const UI_PREFIX = "sp";
export const SP_PORTAL_SCOPE = "dashboard-supplies-portal";

const spEmptyStateClassNames = emptyStateCardBemClasses(UI_PREFIX);
const spStateBannerClassNames = stateBannerBemClasses(UI_PREFIX);
export const spSectionCardClassNames = sectionCardPacBemClasses(UI_PREFIX);
export const spSectionRouteCardClassNames = sectionRouteCardBemClasses(UI_PREFIX);
export const spCatalogSearchClassNames = catalogSearchBarBemClasses(UI_PREFIX);

export const SuppliesTopBar = createDashboardTopBar({ prefix: UI_PREFIX });
export const SuppliesTopBarSearchTrigger = createDashboardTopBarSearchTrigger({
  prefix: UI_PREFIX,
});
export const SuppliesCommandPalette = createDashboardCommandPalette({
  prefix: UI_PREFIX,
  portalScopeClassName: SP_PORTAL_SCOPE,
});
export const SuppliesPagePath = createDashboardPagePath({
  prefix: UI_PREFIX,
  portalScopeClassName: SP_PORTAL_SCOPE,
});
export const SuppliesEmptyState = createDashboardEmptyState({
  classNames: {
    ...spEmptyStateClassNames,
    withTitle: true,
  },
  defaultMessage: "",
});
export const SuppliesStateBanner = createDashboardStateBanner({
  classNames: spStateBannerClassNames,
});
export const SuppliesViewTransition = createDashboardViewTransition({ prefix: UI_PREFIX });

export const spSectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

export const SuppliesSectionCard = createDashboardSectionCard({
  classNames: spSectionCardClassNames,
  labels: spSectionLabels,
});
export const SuppliesSectionRouteCard = createDashboardSectionRouteCard({
  classNames: spSectionRouteCardClassNames,
});
export const SuppliesCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: spCatalogSearchClassNames,
});
export const SuppliesHubChipRow = createDashboardHubChipRow({ prefix: UI_PREFIX });
export const SuppliesRouteChip = createDashboardRouteChip({ prefix: UI_PREFIX });
export const SuppliesStatusBadge = createDashboardStatusBadge({ prefix: UI_PREFIX });
export const SuppliesActionButton = ActionButton;
export const SuppliesAvatar = createInitialsAvatar(UI_PREFIX);

const SuppliesPageHeroBase = createDashboardPageHero({ prefix: UI_PREFIX });
export function SuppliesPageHero(props: ComponentProps<typeof SuppliesPageHeroBase>) {
  return createElement(SuppliesPageHeroBase, { density: "compact", ...props });
}

export { HelpTooltip };
