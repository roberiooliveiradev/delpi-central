import {
  createDashboardLoadingActivityCard,
  type DashboardLoadingActivityCardProps,
  type LoadingActivityCardLabels,
} from "@delpi/plugin-ui";

const LABELS = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
} satisfies LoadingActivityCardLabels;

export const LoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: "kz",
  labels: LABELS,
});

export type LoadingActivityCardProps = DashboardLoadingActivityCardProps;
