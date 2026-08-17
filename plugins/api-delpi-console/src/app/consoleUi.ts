import {
  createDashboardSectionCard,
  createMetricKpiCard,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui";

/** Prefixo BEM local; estilos visuais vêm do dual-class `delpi-ui-*` no kit. */
export const UI_PREFIX = "adc";

export const ConsoleMetricKpiCard = createMetricKpiCard(UI_PREFIX);

export const consoleSectionLabels = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  expandAriaLabel: (title: string) => `Expandir ${title}`,
  collapseAriaLabel: (title: string) => `Recolher ${title}`,
};

export const ConsoleSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(UI_PREFIX),
  labels: consoleSectionLabels,
});
