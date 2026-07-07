import { createDashboardDetailFieldGrid } from "@delpi/plugin-ui";

export type { DetailField } from "@delpi/plugin-ui";

export const DetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: "dq",
  labels: {
    emptyMessage: "Sem dados.",
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
});
