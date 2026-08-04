import type { ReactNode } from "react";

import { EmptyState } from "../../../ui/EmptyState";
import type { CustomerDetailSection } from "../utils/customerDetailSection";

const COPY: Partial<
  Record<CustomerDetailSection, { title: string; description: string }>
> = {
  oportunidades: {
    title: "Oportunidades em breve",
    description:
      "Aqui você acompanhará oportunidades comerciais deste cliente. Estamos preparando o cadastro.",
  },
  contatos: {
    title: "Contatos em breve",
    description:
      "Em breve você poderá registrar e consultar os contatos principais deste cliente.",
  },
};

type CustomerSectionComingSoonProps = {
  section: CustomerDetailSection;
  action?: ReactNode;
};

export function CustomerSectionComingSoon({
  section,
  action,
}: CustomerSectionComingSoonProps) {
  const copy = COPY[section] ?? {
    title: "Em breve",
    description: "Esta seção ainda não está disponível.",
  };
  return (
    <EmptyState title={copy.title} description={copy.description} action={action} />
  );
}
