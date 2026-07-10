import { createDashboardSectionCard, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses("pac"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
