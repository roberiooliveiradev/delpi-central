import { createDashboardDetailFieldGrid } from "@delpi/plugin-ui";

export type { DetailField } from "@delpi/plugin-ui";

export const DetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: "dp",
  labels: {
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
});
