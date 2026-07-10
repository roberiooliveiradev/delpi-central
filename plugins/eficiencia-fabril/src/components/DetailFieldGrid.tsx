import { createDashboardDetailFieldGrid } from "@delpi/plugin-ui/index";

export type { DetailField } from "@delpi/plugin-ui/index";

export const DetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: "ef",
  labels: {
    emptyMessage: "Sem dados.",
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
});
