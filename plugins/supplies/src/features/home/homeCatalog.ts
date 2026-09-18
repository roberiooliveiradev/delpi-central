import type { SuppliesCapabilityFlags } from "../../api/capabilities";
import type { HubCapabilities } from "../../content/pluginRouteCatalog";

export function toHubCapabilities(flags: SuppliesCapabilityFlags): HubCapabilities {
  return {
    analytics: flags.access,
    purchaseRequests: flags.access,
    operations: flags.access,
    administration: flags.manage,
  };
}
