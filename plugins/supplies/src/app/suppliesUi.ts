import {
  ActionButton,
  HelpTooltip,
  SectionHintLabel,
  SpeedometerGauge,
  createDashboardCatalogSearchBar,
  createDashboardChartToolbarKit,
  createDashboardCommandPalette,
  createDashboardDateField,
  createDashboardEmptyState,
  createDashboardFiltersKit,
  createDashboardHubChipRow,
  createDashboardLoadingActivityCard,
  createDashboardMultiSelectField,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardRouteChip,
  createDashboardSectionCard,
  createDashboardSectionRouteCard,
  createDashboardSegmentToggle,
  createDashboardSelectField,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTabularExportButtons,
  createDashboardTextField,
  createDashboardTitleWithHelp,
  createDashboardTopBar,
  createDashboardTopBarSearchTrigger,
  createDashboardViewTransition,
  createFilterBarShell,
  createInitialsAvatar,
  catalogSearchBarBemClasses,
  dateFieldBemClasses,
  emptyStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textFieldBemClasses,
  titleWithHelpBemClasses,
  useChartGranularitySelection,
  type SpeedometerGaugeProps,
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

export const SuppliesLoadingCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: {
    remainingProgress: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
    progressAriaDeterminate: (remainingPercent: number) =>
      `Carregamento: faltam ${remainingPercent} por cento`,
    progressAriaIndeterminate: "Carregamento em andamento",
  },
});

const SuppliesPageHeroBase = createDashboardPageHero({ prefix: UI_PREFIX });
export function SuppliesPageHero(props: ComponentProps<typeof SuppliesPageHeroBase>) {
  return createElement(SuppliesPageHeroBase, { density: "compact", ...props });
}

export const SuppliesFilterBarShell = createFilterBarShell({
  prefix: UI_PREFIX,
  withGrid: true,
  defaultAriaLabel: "Filtros",
});

export const spFiltersKit = createDashboardFiltersKit({
  prefix: UI_PREFIX,
  portalScopeClassName: SP_PORTAL_SCOPE,
  labels: {
    filtersAriaLabel: "Filtros",
  },
});

const { field: spSelectFieldClasses, control: spSelectControlClasses } =
  selectFieldPacClasses(UI_PREFIX);

export const SuppliesSelectField = createDashboardSelectField({
  field: spSelectFieldClasses,
  control: spSelectControlClasses,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "Todos",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) => (label ? `Buscar em ${label}` : "Buscar opções"),
    },
  },
});

export const SuppliesDateField = createDashboardDateField({
  classNames: dateFieldBemClasses(UI_PREFIX),
});

export const SuppliesTextField = createDashboardTextField({
  classNames: textFieldBemClasses(UI_PREFIX),
});

export const SuppliesMultiSelectField = createDashboardMultiSelectField({
  prefix: UI_PREFIX,
  portalScopeClassName: SP_PORTAL_SCOPE,
  labels: {
    emptyLabel: "Todas",
    searchPlaceholder: "Buscar…",
    selectVisible: "Selecionar visíveis",
    clear: "Limpar",
    emptyOptions: "Nenhuma opção encontrada.",
    multipleSelected: (count: number) => `${count} selecionado(s)`,
  },
});

export const SuppliesSegmentToggle = createDashboardSegmentToggle(UI_PREFIX);
export const SuppliesSectionHintLabel = SectionHintLabel;

export const SuppliesTitleWithHelp = createDashboardTitleWithHelp({
  classNames: titleWithHelpBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});

const suppliesChartToolbarKit = createDashboardChartToolbarKit({
  prefix: UI_PREFIX,
  labels: {
    groupAriaLabel: "Agrupamento do gráfico",
    exportSeries: "Exportar série",
    exportSeriesAriaLabel: "Exportar série do gráfico em CSV",
  },
});

export const SuppliesChartGranularityToggle =
  suppliesChartToolbarKit.ChartGranularityToggle;

export const SuppliesTabularExportButtons = createDashboardTabularExportButtons({
  prefix: UI_PREFIX,
  groupAriaLabel: "Exportar dados",
});

export function SuppliesSpeedometerGauge(
  props: Omit<SpeedometerGaugeProps, "prefix">,
) {
  return createElement(SpeedometerGauge, { ...props, prefix: UI_PREFIX });
}

export { HelpTooltip, useChartGranularitySelection };
