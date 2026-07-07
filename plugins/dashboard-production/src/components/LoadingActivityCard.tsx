import {
  createDashboardLoadingActivityCard,
  type DashboardLoadingActivityCardProps,
  type LoadingActivityCardLabels,
  type LoadingActivityCardTone,
  type LoadingActivityCardVariant,
} from "@delpi/plugin-ui";

const LABELS = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
} satisfies LoadingActivityCardLabels;

export type { LoadingActivityCardTone, LoadingActivityCardVariant };

export const LoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: "dp",
  labels: LABELS,
});

export type LoadingActivityCardProps = DashboardLoadingActivityCardProps;
