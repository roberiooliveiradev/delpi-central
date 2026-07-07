import { createDashboardDetailCard, detailCardProductionBemClasses } from "@delpi/plugin-ui";

export const DetailCard = createDashboardDetailCard({
  classNames: detailCardProductionBemClasses("dp"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
