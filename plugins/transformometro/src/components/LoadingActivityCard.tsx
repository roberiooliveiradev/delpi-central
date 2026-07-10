import {
  createDashboardLoadingActivityCard,
  type DashboardLoadingActivityCardProps,
  type LoadingActivityCardLabels,
} from "@delpi/plugin-ui/index";

const LABELS = {
  progressRemaining: (remainingPercent: number) => `Faltam ${remainingPercent}%`,
  progressAriaDeterminate: (remainingPercent: number) =>
    `Carregamento: faltam ${remainingPercent} por cento`,
  progressAriaIndeterminate: "Carregamento em andamento",
} satisfies LoadingActivityCardLabels;

export const LoadingActivityCard = createDashboardLoadingActivityCard({
  prefix: "ds",
  labels: LABELS,
  withCopyWrapper: true,
});

export type LoadingActivityCardProps = DashboardLoadingActivityCardProps;
