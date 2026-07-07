import { createDashboardDetailFieldGrid } from "@delpi/plugin-ui";

export type { DetailField } from "@delpi/plugin-ui";

export const DetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: "lmps",
  labels: {
    emptyMessage: "Sem dados.",
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  wrapLabels: true,
});
