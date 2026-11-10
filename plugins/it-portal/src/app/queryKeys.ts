import type { ActionPlanListQuery, ServerListQuery } from "../api/itPortalApi";

export const queryKeys = {
  capabilities: ["it-portal", "capabilities"] as const,
  dashboard: ["it-portal", "dashboard"] as const,
  servers: ["it-portal", "servers"] as const,
  serverList: (query: ServerListQuery) => ["it-portal", "servers", "list", query] as const,
  server: (id: string) => ["it-portal", "servers", "detail", id] as const,
  notes: (id: string) => ["it-portal", "servers", "notes", id] as const,
  history: (id: string) => ["it-portal", "servers", "history", id] as const,
  actionPlans: ["it-portal", "action-plans"] as const,
  actionPlanList: (query: ActionPlanListQuery) => ["it-portal", "action-plans", "list", query] as const,
};
