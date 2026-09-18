import type { SuppliesCapabilityFlags } from "../api/capabilities";
import type { PluginView } from "../app/pluginRoutes";

export function canAccessView(view: PluginView, capabilities: SuppliesCapabilityFlags): boolean {
  if (view === "administration") return capabilities.manage;
  if (view === "not_found") return true;
  return capabilities.access;
}

export function hasShellAdmission(capabilities: SuppliesCapabilityFlags): boolean {
  return capabilities.access || capabilities.manage;
}

export function canAccessUserProfile(
  targetUserId: string,
  session: { userId: string | null; capabilities: SuppliesCapabilityFlags },
): boolean {
  if (!hasShellAdmission(session.capabilities)) return false;
  if (session.userId && targetUserId === session.userId) return true;
  return session.capabilities.manage;
}
