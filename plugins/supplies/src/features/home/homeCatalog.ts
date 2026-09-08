import type { SuppliesCapabilityFlags } from "../../api/capabilities";
import type { HubCapabilities } from "../../content/pluginRouteCatalog";

export function toHubCapabilities(flags: SuppliesCapabilityFlags): HubCapabilities {
  return {
    analytics: flags.analytics,
    purchaseRequests: flags.purchaseRequests,
    operations: flags.operations,
    administration: flags.administration,
  };
}
