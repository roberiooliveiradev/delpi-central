import {
  createContentCard,
  createDashboardEmptyState,
  createDashboardFormActions,
  createDashboardFiltersKit,
  createDashboardLoadingState,
  createDashboardNavigationCard,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardStateBanner,
  createStateBoxPanel,
  createTimeline,
  emptyStateCardBemClasses,
  formActionsBemClasses,
  loadingStateCardBemClasses,
  navigationCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  stateBannerBemClasses,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

const PREFIX = "cipa";

export const CipaPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const CipaSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const CipaContentCard = createContentCard(PREFIX, { titleLevel: 2 });

export const CipaFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(PREFIX),
});

export const CipaNavigationCard = createDashboardNavigationCard({
  classNames: navigationCardBemClasses(PREFIX),
});

const cipaFiltersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: {
    filtersAriaLabel: "Filtros de atas",
  },
  portalScopeClassName: "dashboard-cipa",
});

export const CipaFiltersRow = cipaFiltersKit.FiltersRow;
export const CipaFilterInputField = cipaFiltersKit.FilterInputField;
export const CipaFilterSelectField = cipaFiltersKit.FilterSelectField;

export const CipaStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PREFIX),
});

export const CipaEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(PREFIX),
  defaultMessage: "Nenhum item encontrado.",
});

export const CipaLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(PREFIX),
  defaultMessage: "Carregando…",
});

export const CipaTimeline = createTimeline({ prefix: PREFIX });

export const CipaStateBox = createStateBoxPanel({
  prefix: PREFIX,
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <FileQuestion size={22} />;
    return <Loader2 size={22} />;
  },
});
