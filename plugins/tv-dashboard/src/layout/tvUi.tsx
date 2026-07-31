import {
  createContentCard,
  createDashboardNavigationCard,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createFilterBarShell,
  navigationCardBemClasses,
  pageHeaderBrandBemClasses,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";

const PREFIX = "td";

export const TvPageHeader = createDashboardPageHeader({
  layout: "brand",
  classNames: pageHeaderBrandBemClasses(PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const TvNavigationCard = createDashboardNavigationCard({
  classNames: navigationCardBemClasses(PREFIX),
});

export const TvContentCard = createContentCard(PREFIX, { titleLevel: 2 });

export const TvSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const TvFilterBarShell = createFilterBarShell({
  prefix: PREFIX,
  withGrid: false,
  embeddedByDefault: true,
  defaultAriaLabel: "Filtros",
});
