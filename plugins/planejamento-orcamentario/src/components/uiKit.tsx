import {
  createDashboardLoadingActivityCard,
  createDashboardSectionCard,
  createDashboardStateBox,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";

export const UI_PREFIX = "po";

const LOADING_LABELS = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
};

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(UI_PREFIX),
  labels: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
});

export const LoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: UI_PREFIX,
  labels: LOADING_LABELS,
});

export const StateBox = createDashboardStateBox({ prefix: UI_PREFIX });
