import { createDashboardDetailCard, detailCardRichBemClasses } from "@delpi/plugin-ui";

export const DetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses("dc"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
