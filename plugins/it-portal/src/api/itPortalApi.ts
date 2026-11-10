/** Contrato da BFF `it-portal-api` (operationIds estáveis no OpenAPI). */
import { apiGet, apiPost, apiPut, apiUrl } from "./httpClient";

export type UnitCode = "01" | "02";
export type Environment = "production" | "staging" | "development";
export type ServerType = "physical" | "virtual" | "cloud";
export type Criticality = "low" | "medium" | "high" | "critical";
export type AdministrativeStatus = "planned" | "in_operation" | "maintenance" | "decommissioning";
export type ActionPriority = "low" | "medium" | "high" | "urgent";
export type ActionStatus = "pending" | "in_progress" | "done" | "cancelled";

export type Server = {
  id: string;
  code: string;
  name: string;
  hostname: string;
  ip_address: string | null;
  unit_code: UnitCode;
  location: string | null;
  environment: Environment;
  server_type: ServerType;
  purpose: string | null;
  operating_system: string | null;
  criticality: Criticality;
  administrative_status: AdministrativeStatus;
  responsible: string | null;
  description: string | null;
  revision: number;
  archived: boolean;
  archived_at: string | null;
  archived_by_name: string | null;
  open_action_count: number;
  created_at: string;
  created_by_name: string;
  updated_at: string;
  updated_by_name: string;
};

export type ServerInput = {
  name: string;
  hostname: string;
  ip_address: string;
  unit_code: string;
  location: string;
  environment: string;
  server_type: string;
  purpose: string;
  operating_system: string;
  criticality: string;
  administrative_status: string;
  responsible: string;
  description: string;
};

export type ServerNote = {
  id: string;
  server_id: string;
  body: string;
  author_name: string;
  created_at: string;
};

export type HistoryEvent = {
  id: string;
  entity_type: "server" | "server_note" | "action_plan";
  entity_id: string;
  event_type: string;
  changes: Record<string, unknown>;
  actor_name: string;
  occurred_at: string;
};

export type ActionPlan = {
  id: string;
  code: string;
  server_id: string;
  server: {
    id: string;
    code: string;
    name: string;
    hostname: string;
    environment: Environment;
    unit_code: UnitCode;
    archived: boolean;
  };
  title: string;
  description: string | null;
  responsible: string | null;
  priority: ActionPriority;
  status: ActionStatus;
  due_date: string | null;
  completed_at: string | null;
  is_overdue: boolean;
  revision: number;
  created_at: string;
  created_by_name: string;
  updated_at: string;
  updated_by_name: string;
};

export type ActionPlanInput = {
  title: string;
  description: string;
  responsible: string;
  priority: string;
  due_date: string | null;
};

export type Page<T> = { items: T[]; total: number; page: number; page_size: number };

export type Dashboard = {
  reference_date: string;
  generated_at: string;
  servers: { total: number; high_or_critical: number };
  recent_servers: Server[];
  action_plans: { open: number; overdue: number } | null;
  attention_action_plans: ActionPlan[] | null;
};

export type Capabilities = {
  display_name: string;
  can_view_servers: boolean;
  can_manage_servers: boolean;
  can_create_notes: boolean;
  can_view_action_plans: boolean;
  can_manage_action_plans: boolean;
};

export type ServerListQuery = {
  q?: string;
  unit_code?: string;
  environment?: string;
  criticality?: string;
  archived?: "active" | "archived" | "all";
  sort?: string;
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

export type ActionPlanListQuery = {
  status?: readonly string[];
  server_id?: string;
  priority?: string;
  overdue_only?: boolean;
  q?: string;
  sort?: string;
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

export const itPortalApi = {
  capabilities: (signal?: AbortSignal) => apiGet<Capabilities>(apiUrl("/me/capabilities"), signal),
  dashboard: (signal?: AbortSignal) => apiGet<Dashboard>(apiUrl("/dashboard"), signal),

  listServers: (query: ServerListQuery, signal?: AbortSignal) =>
    apiGet<Page<Server>>(apiUrl("/servers", query), signal),
  getServer: (id: string, signal?: AbortSignal) =>
    apiGet<Server>(apiUrl(`/servers/${encodeURIComponent(id)}`), signal),
  createServer: (input: ServerInput) => apiPost<Server>(apiUrl("/servers"), input),
  updateServer: (id: string, input: ServerInput, revision: number) =>
    apiPut<Server>(apiUrl(`/servers/${encodeURIComponent(id)}`), { ...input, revision }),
  archiveServer: (id: string, revision: number) =>
    apiPost<Server>(apiUrl(`/servers/${encodeURIComponent(id)}/archive`), { revision }),
  restoreServer: (id: string, revision: number) =>
    apiPost<Server>(apiUrl(`/servers/${encodeURIComponent(id)}/restore`), { revision }),

  listNotes: (serverId: string, signal?: AbortSignal) =>
    apiGet<ServerNote[]>(apiUrl(`/servers/${encodeURIComponent(serverId)}/notes`), signal),
  createNote: (serverId: string, body: string) =>
    apiPost<ServerNote>(apiUrl(`/servers/${encodeURIComponent(serverId)}/notes`), { body }),
  listHistory: (serverId: string, signal?: AbortSignal) =>
    apiGet<HistoryEvent[]>(apiUrl(`/servers/${encodeURIComponent(serverId)}/history`), signal),

  listActionPlans: (query: ActionPlanListQuery, signal?: AbortSignal) =>
    apiGet<Page<ActionPlan>>(apiUrl("/action-plans", query), signal),
  createActionPlan: (serverId: string, input: ActionPlanInput) =>
    apiPost<ActionPlan>(apiUrl(`/servers/${encodeURIComponent(serverId)}/action-plans`), input),
  updateActionPlan: (id: string, input: ActionPlanInput, revision: number) =>
    apiPut<ActionPlan>(apiUrl(`/action-plans/${encodeURIComponent(id)}`), { ...input, revision }),
  changeActionPlanStatus: (id: string, status: ActionStatus, revision: number) =>
    apiPost<ActionPlan>(apiUrl(`/action-plans/${encodeURIComponent(id)}/status`), { status, revision }),
};

/** Transições aceitas pela API (o backend revalida — isto só orienta a UI). */
export const ACTION_STATUS_TRANSITIONS: Record<ActionStatus, readonly ActionStatus[]> = {
  pending: ["in_progress", "done", "cancelled"],
  in_progress: ["pending", "done", "cancelled"],
  done: ["in_progress"],
  cancelled: ["pending"],
};
