import {
  CommercialActionButton,
  CommercialEmptyState,
} from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";

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
    <CommercialEmptyState
      title="Oportunidades da conta"
      message={
        canViewAnalytics
          ? "Consulte a área de Oportunidades usando o código real deste cliente."
          : "Você não possui permissão para consultar oportunidades."
      }
    >
      {canViewAnalytics && customerCode.trim() ? (
          <CommercialActionButton
            variant="primary"
            onClick={() =>
              navigatePluginView("analytics_opportunities", {
                basePath,
                search: `?${new URLSearchParams({ search: customerCode.trim() }).toString()}`,
              })
            }
          >
            Ver oportunidades
          </CommercialActionButton>
      ) : null}
    </CommercialEmptyState>
  );
}
