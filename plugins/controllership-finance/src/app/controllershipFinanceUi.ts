/**
 * Adapter fino: fábricas do `@delpi/plugin-ui` com o prefixo `cf` do portal.
 * Nenhum componente visual é reimplementado — somente binding de classes/labels.
 */
import {
  ActionButton,
  createDashboardCatalogSearchBar,
  createDashboardCommandPalette,
  createDashboardEventsSection,
  createDashboardInteractiveDataCard,
  createDashboardLoadingActivityCard,
  createDashboardMentionComposer,
  createDashboardMessageThread,
  createDashboardMetricStrip,
  createMetricKpiCard,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardRecentAccessStrip,
  createDashboardSectionCard,
  createDashboardSectionRouteCard,
  createDashboardSegmentToggle,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTitleWithHelp,
  createDashboardTopBar,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarUserIdentity,
  createDashboardTopBarUtilityCluster,
  createDashboardViewTransition,
  createHostContainedModalShell,
  createTimeline,
  EmptyState,
  UnifiedAvatar,
  catalogSearchBarBemClasses,
  confirmModalBemClasses,
  emptyStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  stateBannerBemClasses,
  statusBadgeBemClasses,
  titleWithHelpBemClasses,
} from "@delpi/plugin-ui/index";
import { createElement, type ComponentProps } from "react";

export const UI_PREFIX = "cf";
export const CF_PORTAL_SCOPE = "dashboard-controllership-finance";

export const cfSectionCardClassNames = sectionCardPacBemClasses(UI_PREFIX);
export const cfEmptyStateClassNames = emptyStateCardBemClasses(UI_PREFIX);
export const cfStateBannerClassNames = stateBannerBemClasses(UI_PREFIX);
export const cfStatusBadgeClassNames = statusBadgeBemClasses(UI_PREFIX);
export const cfSectionRouteCardClassNames = sectionRouteCardBemClasses(UI_PREFIX);
export const cfCatalogSearchClassNames = catalogSearchBarBemClasses(UI_PREFIX);

export const cfSectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

export const CfActionButton = ActionButton;
export const CfEmptyState = EmptyState;

const CfPageHeroBase = createDashboardPageHero({ prefix: UI_PREFIX });
export function CfPageHero(
  props: ComponentProps<typeof CfPageHeroBase>,
) {
  return createElement(CfPageHeroBase, { density: "compact", ...props });
}

export const CfStatusBadge = createDashboardStatusBadge({ prefix: UI_PREFIX });
export const CfViewTransition = createDashboardViewTransition({
  prefix: UI_PREFIX,
});
export const CfPagePath = createDashboardPagePath({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
});
export const CfTopBar = createDashboardTopBar({ prefix: UI_PREFIX });
export const CfTopBarUtilityCluster = createDashboardTopBarUtilityCluster({
  prefix: UI_PREFIX,
});
export const CfTopBarSearchTrigger = createDashboardTopBarSearchTrigger({
  prefix: UI_PREFIX,
});
export const CfTopBarUserIdentity = createDashboardTopBarUserIdentity({
  prefix: UI_PREFIX,
});
export const CfCommandPalette = createDashboardCommandPalette({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
});
export const CfSectionCard = createDashboardSectionCard({
  classNames: cfSectionCardClassNames,
  labels: cfSectionLabels,
});
export const CfSectionRouteCard = createDashboardSectionRouteCard({
  classNames: cfSectionRouteCardClassNames,
});
export const CfCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: cfCatalogSearchClassNames,
});
export const CfRecentAccessStrip = createDashboardRecentAccessStrip({
  prefix: UI_PREFIX,
});
export const CfEventsSection = createDashboardEventsSection({
  prefix: UI_PREFIX,
  labels: cfSectionLabels,
  sectionClassNames: cfSectionCardClassNames,
});
export const CfLoadingCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: {
    progressRemaining: (remainingPercent: number) =>
      `Faltam ${remainingPercent}%`,
    progressAriaDeterminate: (remainingPercent: number) =>
      `Carregamento: faltam ${remainingPercent} por cento`,
    progressAriaIndeterminate: "Carregamento em andamento",
  },
});
export const CfStateBanner = createDashboardStateBanner({
  classNames: cfStateBannerClassNames,
});
export const CfMetricStrip = createDashboardMetricStrip({
  prefix: UI_PREFIX,
});
export const CfMetricKpiCard = createMetricKpiCard(UI_PREFIX);
export const CfInteractiveDataCard = createDashboardInteractiveDataCard({
  prefix: UI_PREFIX,
});
export const CfTitleWithHelp = createDashboardTitleWithHelp({
  classNames: titleWithHelpBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});
export const CfSegmentToggle = createDashboardSegmentToggle(UI_PREFIX);
export const CfMessageThread = createDashboardMessageThread(UI_PREFIX);
export const CfMentionComposer = createDashboardMentionComposer(UI_PREFIX);
export const CfTimeline = createTimeline({ prefix: UI_PREFIX });
export const CfUnifiedAvatar = UnifiedAvatar;
export const cfConfirmModalClassNames = confirmModalBemClasses(UI_PREFIX);
export const CfDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
  containedLayout: "dialog",
});
