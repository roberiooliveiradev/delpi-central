import { ActionButton } from "@delpi/plugin-ui/index";

import { navigatePluginView } from "../../../app/pluginNavigation";
import { EmptyState } from "../../../ui/EmptyState";

type CustomerSectionComingSoonProps = {
  basePath: string;
  customerCode: string;
  canViewAnalytics: boolean;
};

/**
 * Oportunidades são consultadas pela página canônica, com busca real por cliente.
 */
export function CustomerSectionComingSoon({
  basePath,
  customerCode,
  canViewAnalytics,
}: CustomerSectionComingSoonProps) {
  return (
    <EmptyState
      title="Oportunidades da conta"
      description={
        canViewAnalytics
          ? "Consulte a área de Oportunidades usando o código real deste cliente."
          : "Você não possui permissão para consultar oportunidades."
      }
      action={
        canViewAnalytics && customerCode.trim() ? (
          <ActionButton
            variant="primary"
            onClick={() =>
              navigatePluginView("analytics_opportunities", {
                basePath,
                search: `?${new URLSearchParams({ search: customerCode.trim() }).toString()}`,
              })
            }
          >
            Ver oportunidades
          </ActionButton>
        ) : undefined
      }
    />
  );
}
