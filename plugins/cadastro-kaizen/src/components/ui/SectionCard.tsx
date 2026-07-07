import { createDashboardSectionCard, sectionCardKaizenBemClasses } from "@delpi/plugin-ui";

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardKaizenBemClasses("kz"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
