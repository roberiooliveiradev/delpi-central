import {
  createDashboardDetailCard,
  createDashboardDetailFieldGrid,
  detailCardRichBemClasses,
} from "@delpi/plugin-ui/index";

export const DetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses("sm"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const DetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: "sm",
  labels: {
    emptyMessage: "Sem dados.",
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
  wrapLabels: true,
});

export type { DetailField } from "@delpi/plugin-ui/index";
