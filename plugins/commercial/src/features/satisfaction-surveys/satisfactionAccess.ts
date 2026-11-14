import type { CommercialCapabilities } from "../../types/portfolio";

/**
 * Visibilidade de UI da gestão da Pesquisa de Satisfação.
 * Não autoriza nada: `commercial-api` valida `commercial.marketing` OU `commercial.manage`.
 */
export function resolveCanManageSatisfaction(
  capabilities: Pick<CommercialCapabilities, "manage" | "marketing" | "satisfaction_manage">,
): boolean {
  return Boolean(
    capabilities.satisfaction_manage || capabilities.marketing || capabilities.manage,
  );
}
