import type { ReactNode } from "react";

import { FormGrid } from "../ui/FormGrid";
import { SectionCard } from "../ui/SectionCard";

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
    <SectionCard title={title} hint={hint} subtitle={description} actions={headerActions}>
      <FormGrid>{children}</FormGrid>
    </SectionCard>
  );
}
