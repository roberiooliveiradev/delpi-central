/**
 * Adapter fino: fábricas do `@delpi/plugin-ui` com o prefixo `cf` do portal.
 * Nenhum componente visual é reimplementado — somente binding de classes/labels.
 */
import {
  ActionButton,
  ChartCard,
  BarSeriesChart,
  ComparativeAreaChart,
  HelpTooltip,
  HorizontalValueBars,
  chartCardBemClasses,
  createDashboardCatalogSearchBar,
  createDashboardCommandPalette,
  createDashboardDateField,
  createFilterBarShell,
  createDashboardDetailCard,
  createDashboardDistributionDonut,
  createDashboardEventsSection,
  createDashboardEmptyGuidance,
  createDashboardInlineLoadingProgress,
  createDashboardInteractiveDataCard,
  createDashboardLoadingActivityCard,
  createDashboardDataRecordCard,
  createDashboardMentionComposer,
  createDashboardMessageThread,
  createDashboardMetricStrip,
  createDashboardMultiSelectField,
  createMetricKpiCard,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardProgressSummaryBar,
  createDashboardProgressTracker,
  createDashboardRecentAccessStrip,
  createDashboardResolutionStatusCell,
  createDashboardScopeChipBar,
  createDashboardSectionCard,
  createDashboardSectionRouteCard,
  createDashboardSegmentToggle,
  createDashboardSelectField,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextAreaField,
  createDashboardTextField,
  createDashboardTitleWithHelp,
  createDashboardTopBar,
  createDashboardTopBarFavoritesStrip,
  createDashboardTopBarSearchTrigger,
  createDashboardTopBarUserIdentity,
  createDashboardTopBarUtilityCluster,
  createDashboardTrendDelta,
  createDashboardUnderlineNav,
  createDashboardViewTransition,
  createHostContainedDrawerShell,
  createHostContainedModalShell,
  createSemicircleProgressGauge,
  createTablePaginationNav,
  createTimeline,
  detailCardProductionBemClasses,
  EmptyState,
  UnifiedAvatar,
  catalogSearchBarBemClasses,
  confirmModalBemClasses,
  dateFieldBemClasses,
  emptyStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  statusBadgeBemClasses,
  textAreaFieldBemClasses,
  textFieldBemClasses,
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
export const CfTopBarFavoritesStrip = createDashboardTopBarFavoritesStrip({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
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
export const CfDataRecordCard = createDashboardDataRecordCard({
  prefix: UI_PREFIX,
});
export type { DataRecordCardField } from "@delpi/plugin-ui/index";
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
export const CfScopeChipBar = createDashboardScopeChipBar({ prefix: UI_PREFIX });
export const CfSemicircleProgressGauge = createSemicircleProgressGauge({
  prefix: UI_PREFIX,
});
export function CfHorizontalValueBars(
  props: ComponentProps<typeof HorizontalValueBars>,
) {
  return createElement(HorizontalValueBars, { prefix: UI_PREFIX, ...props });
}
export function CfComparativeAreaChart(
  props: ComponentProps<typeof ComparativeAreaChart>,
) {
  return createElement(ComparativeAreaChart, { prefix: UI_PREFIX, ...props });
}
export function CfBarSeriesChart(
  props: ComponentProps<typeof BarSeriesChart>,
) {
  return createElement(BarSeriesChart, { ...props });
}
export const CfDistributionDonut = createDashboardDistributionDonut({
  prefix: UI_PREFIX,
});
export const CfResolutionStatusCell = createDashboardResolutionStatusCell({
  prefix: UI_PREFIX,
});
export const CfUnderlineNav = createDashboardUnderlineNav({ prefix: UI_PREFIX });
export const CfProgressTracker = createDashboardProgressTracker({
  prefix: UI_PREFIX,
});
export const CfMultiSelectField = createDashboardMultiSelectField({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
  labels: {
    emptyLabel: "Todos",
    searchPlaceholder: "Buscar…",
    selectVisible: "Selecionar opções visíveis",
    clear: "Limpar seleção",
    emptyOptions: "Nenhuma opção encontrada.",
    multipleSelected: (count: number) => `${count} selecionados`,
    searchAriaLabel: (label: string) => `Buscar em ${label}`,
    selectedCountLabel: (count: number) => `${count} selecionados`,
    removeTagAriaLabel: (value: string) => `Remover ${value}`,
  },
});
export const CfDrawerShell = createHostContainedDrawerShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
});
export const CfDetailCard = createDashboardDetailCard({
  classNames: detailCardProductionBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});
export const CfEmptyGuidance = createDashboardEmptyGuidance(UI_PREFIX);
export function CfHelpTooltip(props: ComponentProps<typeof HelpTooltip>) {
  return createElement(HelpTooltip, props);
}
export function CfChartCard(props: Omit<ComponentProps<typeof ChartCard>, "classNames">) {
  return createElement(ChartCard, {
    classNames: chartCardBemClasses(UI_PREFIX),
    ...props,
  });
}
export const CfTrendDelta = createDashboardTrendDelta({ prefix: UI_PREFIX });
export const CfProgressSummaryBar = createDashboardProgressSummaryBar({
  prefix: UI_PREFIX,
  defaultLabel: "Progresso",
});
export const CfInlineLoadingProgress = createDashboardInlineLoadingProgress({
  prefix: UI_PREFIX,
  defaultLabel: "Carregando dados",
});
export const CfTablePaginationNav = createTablePaginationNav({
  prefix: UI_PREFIX,
  labels: {
    navigationAriaLabel: "Paginação",
    previous: "Página anterior",
    next: "Próxima página",
    infoBeforeCurrent: "Página",
    infoAfterCurrent: (totalPages: number) => `de ${totalPages}`,
  },
});
export const CfTextField = createDashboardTextField({
  classNames: textFieldBemClasses(UI_PREFIX),
});
export const CfTextAreaField = createDashboardTextAreaField({
  classNames: textAreaFieldBemClasses(UI_PREFIX),
});
export const CfDateField = createDashboardDateField({
  classNames: dateFieldBemClasses(UI_PREFIX),
});
export const CfFilterBarShell = createFilterBarShell({
  prefix: UI_PREFIX,
  defaultAriaLabel: "Escopo da auditoria",
});
const { field: cfSelectFieldClasses, control: cfSelectControlClasses } =
  selectFieldPacClasses(UI_PREFIX);
export const CfSelectField = createDashboardSelectField({
  field: cfSelectFieldClasses,
  control: cfSelectControlClasses,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "Todos",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) =>
        label ? `Buscar em ${label}` : "Buscar opções",
    },
  },
});
export const CfUnifiedAvatar = UnifiedAvatar;
export const cfConfirmModalClassNames = confirmModalBemClasses(UI_PREFIX);
export const CfDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
  containedLayout: "dialog",
});
export const CfWideDialog = createHostContainedModalShell({
  prefix: UI_PREFIX,
  portalScopeClassName: CF_PORTAL_SCOPE,
  containedLayout: "dialog",
  variant: "fit",
});
