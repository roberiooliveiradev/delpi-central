import { createDashboardLoadingActivityCard } from "@delpi/plugin-ui/index";

export const LoadingActivityInline = createDashboardLoadingActivityCard({
  prefix: "lmps",
  block: "loading-activity-inline",
  withCopyWrapper: true,
  defaultTone: "info",
  labels: {
    progressRemaining: (remainingPercent) => `Faltam ${remainingPercent}%`,
    progressAriaDeterminate: (remainingPercent) =>
      `Carregamento: faltam ${remainingPercent} por cento`,
    progressAriaIndeterminate: "Carregamento em andamento",
  },
});

export type { DashboardLoadingActivityCardProps as LoadingActivityInlineProps } from "@delpi/plugin-ui/index";
