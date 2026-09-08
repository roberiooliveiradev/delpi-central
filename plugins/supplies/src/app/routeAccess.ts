import type { SuppliesCapabilityFlags } from "../api/capabilities";
import type { PluginView } from "../app/pluginRoutes";

export function requiredCapabilityForView(
  view: PluginView,
): keyof SuppliesCapabilityFlags | "none" {
  switch (view) {
    case "overview":
    case "negotiations":
    case "indicators":
      return "analytics";
    case "purchase_requests":
      return "purchaseRequests";
    case "purchase_orders":
    case "deliveries":
    case "suppliers":
    case "products":
    case "inventory":
    case "safety_stock":
      return "operations";
    case "administration":
      return "administration";
    case "home":
    case "my_tasks":
    case "help":
    case "user_profile":
      return "portal";
    default:
      return "none";
  }
}

export function canAccessUserProfile(
  targetUserId: string,
  session: { userId: string | null; capabilities: SuppliesCapabilityFlags },
): boolean {
  if (!session.capabilities.portal) return false;
  if (session.userId && session.userId === targetUserId) return true;
  return Boolean(session.capabilities.administration);
}

export function canAccessView(view: PluginView, capabilities: SuppliesCapabilityFlags): boolean {
  const required = requiredCapabilityForView(view);
  if (required === "none") return true;
  return Boolean(capabilities[required]);
}
