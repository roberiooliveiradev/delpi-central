import type { ReactNode } from "react";

import {
  createDashboardFormGrid,
  createDashboardSectionCard,
  formGridBemClasses,
  sectionCardKaizenBemClasses,
} from "@delpi/plugin-ui";

const SectionCard = createDashboardSectionCard({
  classNames: sectionCardKaizenBemClasses("kz"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

const FormGrid = createDashboardFormGrid({
  classNames: formGridBemClasses("kz"),
});

type FormSectionProps = {
  title: string;
  hint?: string;
  description?: string;
  children: ReactNode;
  headerActions?: ReactNode;
};

/** Seção de formulário em card, no mesmo padrão visual da ficha de edição. */
export function FormSection({
  title,
  hint,
  description,
  children,
  headerActions,
}: FormSectionProps) {
  return (
    <SectionCard
      title={title}
      hint={hint}
      subtitle={description}
      actions={headerActions}
    >
      <FormGrid>{children}</FormGrid>
    </SectionCard>
  );
}
