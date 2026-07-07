import { createDashboardLoadingActivityCard } from "@delpi/plugin-ui";

import "./LoadingActivityInline.css";

export const LoadingActivityInline = createDashboardLoadingActivityCard({
  prefix: "si",
  block: "loading-activity-inline",
  withCopyWrapper: true,
  defaultTone: "neutral",
  labels: {
    progressRemaining: (remainingPercent) => `Faltam ${remainingPercent}%`,
    progressStarting: "Iniciando…",
    progressRemainingOnlyAfterStart: true,
    progressAriaDeterminate: (remainingPercent) =>
      `Carregamento: faltam ${remainingPercent} por cento`,
    progressAriaStarting: "Carregamento: Iniciando…",
    progressAriaIndeterminate: "Carregamento em andamento",
  },
});

export type { DashboardLoadingActivityCardProps as LoadingActivityInlineProps } from "@delpi/plugin-ui";
