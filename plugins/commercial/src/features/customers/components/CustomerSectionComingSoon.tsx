import { ActionButton } from "@delpi/plugin-ui/index";

import { navigatePluginView } from "../../../app/pluginNavigation";
import { EmptyState } from "../../../ui/EmptyState";
import type { CustomerDetailSection } from "../utils/customerDetailSection";

type CustomerSectionComingSoonProps = {
  section: CustomerDetailSection;
  basePath: string;
};

/**
 * Conta híbrida (3C): resumo/CTA interno — Oportunidades → Gestão; Contatos → Meu dia.
 */
export function CustomerSectionComingSoon({
  section,
  basePath,
}: CustomerSectionComingSoonProps) {
  if (section === "oportunidades") {
    return (
      <EmptyState
        title="Oportunidades (OV)"
        description="Acompanhe o funil e o detalhe das oportunidades deste cliente na Gestão."
        action={
          <div className="cm-nav-row">
            <ActionButton
              variant="primary"
              onClick={() =>
                navigatePluginView("gestao_oportunidades", { basePath })
              }
            >
              Ver oportunidades
            </ActionButton>
            <ActionButton
              variant="ghost"
              onClick={() => navigatePluginView("gestao", { basePath })}
            >
              Visão geral
            </ActionButton>
          </div>
        }
      />
    );
  }

  if (section === "contatos") {
    return (
      <EmptyState
        title="Contatos"
        description="Cadastro de contatos ainda não está disponível. Use o Meu dia para follow-ups e a área Propostas para documentos ADY."
        action={
          <div className="cm-nav-row">
            <ActionButton
              variant="primary"
              onClick={() => navigatePluginView("my_day", { basePath })}
            >
              Abrir Meu dia
            </ActionButton>
            <ActionButton
              variant="ghost"
              onClick={() => navigatePluginView("propostas", { basePath })}
            >
              Ver propostas
            </ActionButton>
          </div>
        }
      />
    );
  }

  return (
    <EmptyState title="Em breve" description="Esta seção ainda não está disponível." />
  );
}
