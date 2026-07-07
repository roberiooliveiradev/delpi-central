import { createDashboardDetailCard, detailCardRichBemClasses } from "@delpi/plugin-ui";

export const DetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses("lmps"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
