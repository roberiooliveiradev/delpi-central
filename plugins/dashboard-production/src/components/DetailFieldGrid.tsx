import { createDashboardDetailFieldGrid } from "@delpi/plugin-ui/index";

export type { DetailField } from "@delpi/plugin-ui/index";

export const DetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: "dp",
  labels: {
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
});
