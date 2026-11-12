/** Contrato da BFF `it-portal-api` (operationIds estáveis no OpenAPI). */
import { apiDelete, apiGet, apiPost, apiPut, apiUrl } from "./httpClient";

export type UnitCode = "01" | "02";
export type Environment = "production" | "staging" | "development";
export type ServerType = "physical" | "virtual" | "cloud";
export type Criticality = "low" | "medium" | "high" | "critical";
export type AdministrativeStatus = "planned" | "in_operation" | "maintenance" | "decommissioning";
export type ActionPriority = "low" | "medium" | "high" | "urgent";
export type ActionStatus = "pending" | "in_progress" | "done" | "cancelled";
export type ServiceKind = "business_application" | "platform_service";
export type ServiceType =
  | "web_application"
  | "api"
  | "identity_access"
  | "reverse_proxy"
  | "cache"
  | "messaging"
  | "file_storage"
  | "scheduler"
  | "monitoring"
  | "erp"
  | "other";
export type HostingRuntime = "container" | "native_process" | "os_service" | "virtual_machine" | "other";
export type DbmsEngine =
  | "postgresql"
  | "sql_server"
  | "mysql"
  | "mariadb"
  | "oracle"
  | "mongodb"
  | "sqlite"
  | "other";
export type NetworkScope = "corporate" | "container_runtime";
export type IntegrationProtocol =
  | "http_api"
  | "soap"
  | "grpc"
  | "smb"
  | "nfs"
  | "file_transfer"
  | "email_smtp"
  | "ldap"
  | "message_queue"
  | "webhook"
  | "other";
export type IntegrationDirection = "source_to_target" | "bidirectional";

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

export type HostService = {
  name: string;
  display_name: string;
  description: string | null;
  state: string;
  start_mode: string;
  can_stop: boolean;
  is_present: boolean;
  observed_at: string;
  updated_at: string;
};

export type HostServicesPage = {
  items: HostService[];
  total: number;
  page: number;
  page_size: number;
  current: { run_id: string; observed_at: string; received_at: string; service_count: number } | null;
};

export type HostServiceQuery = {
  q?: string;
  state?: string;
  start_mode?: string;
  present?: "yes" | "no" | "all";
  page?: number;
  page_size?: number;
};

export type ObservationPresentationStatus = "available" | "partial" | "stale" | "unavailable";

export type ObservationDivergence = {
  field: string;
  registered: string | null;
  observed: string | null;
  observed_all?: string[];
};

export type Observation = {
  id: string;
  server_id: string;
  run_id: string;
  source: string;
  collector_client_id: string;
  observed_at: string;
  received_at: string;
  schema_version: string;
  status: "complete" | "partial" | "failed" | string;
  summary: Record<string, unknown>;
  sections_status: Record<string, string>;
  divergences: ObservationDivergence[];
  created_at: string;
  presentation_status?: ObservationPresentationStatus | null;
};

export type HistoryEntityType =
  | "server"
  | "server_note"
  | "action_plan"
  | "service"
  | "service_hosting"
  | "database_instance"
  | "database_consumer"
  | "network"
  | "server_network_link"
  | "integration"
  | "service_dependency";

export type HistoryEvent = {
  id: string;
  entity_type: HistoryEntityType;
  entity_id: string;
  event_type: string;
  changes: Record<string, unknown>;
  actor_name: string;
  occurred_at: string;
};

export type ServerSummary = {
  id: string;
  code: string;
  name: string;
  hostname: string;
  environment: Environment;
  unit_code: UnitCode;
  archived: boolean;
};

export type ActionPlan = {
  id: string;
  code: string;
  server_id: string;
  server: ServerSummary;
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

export type Service = {
  id: string;
  code: string;
  name: string;
  description: string | null;
  service_kind: ServiceKind;
  service_type: ServiceType;
  technology: string | null;
  environment: Environment;
  unit_code: UnitCode;
  port: number | null;
  criticality: Criticality;
  responsible: string;
  administrative_status: AdministrativeStatus;
  revision: number;
  archived: boolean;
  archived_at: string | null;
  archived_by_name: string | null;
  hosting_count: number;
  database_count: number;
  created_at: string;
  created_by_name: string;
  updated_at: string;
  updated_by_name: string;
};

export type ServiceInput = {
  name: string;
  description: string;
  service_kind: string;
  service_type: string;
  technology: string;
  environment: string;
  unit_code: string;
  port: string;
  criticality: string;
  responsible: string;
  administrative_status: string;
};

export type ServiceSummary = {
  id: string;
  code: string;
  name: string;
  service_kind: ServiceKind;
  environment: Environment;
  criticality: Criticality;
  archived: boolean;
};

export type DatabaseInstance = {
  id: string;
  code: string;
  name: string;
  dbms: DbmsEngine;
  version: string | null;
  server_id: string;
  server: ServerSummary;
  port: number | null;
  environment: Environment;
  purpose: string | null;
  criticality: Criticality;
  responsible: string;
  administrative_status: AdministrativeStatus;
  technical_notes: string | null;
  revision: number;
  archived: boolean;
  archived_at: string | null;
  archived_by_name: string | null;
  consumer_count: number;
  created_at: string;
  created_by_name: string;
  updated_at: string;
  updated_by_name: string;
};

export type DatabaseInstanceInput = {
  name: string;
  dbms: string;
  version: string;
  server_id: string;
  port: string;
  environment: string;
  purpose: string;
  criticality: string;
  responsible: string;
  administrative_status: string;
  technical_notes: string;
};

export type DatabaseSummary = {
  id: string;
  code: string;
  name: string;
  dbms: DbmsEngine;
  environment: Environment;
  criticality: Criticality;
  archived: boolean;
};

export type ServiceHosting = {
  id: string;
  service_id: string;
  server_id: string;
  runtime: HostingRuntime;
  instance_name: string | null;
  notes: string | null;
  created_at: string;
  created_by_name: string;
  service: ServiceSummary;
  server: ServerSummary;
};

export type ServiceHostingInput = {
  service_id: string;
  server_id: string;
  runtime: string;
  instance_name: string;
  notes: string;
};

export type DatabaseConsumer = {
  id: string;
  database_instance_id: string;
  service_id: string;
  notes: string | null;
  created_at: string;
  created_by_name: string;
  database: DatabaseSummary;
  service: ServiceSummary;
};

export type DatabaseConsumerInput = {
  database_instance_id: string;
  service_id: string;
  notes: string;
};

export type Network = {
  id: string;
  code: string;
  name: string;
  cidr: string;
  vlan_id: number | null;
  gateway: string | null;
  unit_code: UnitCode;
  location: string | null;
  purpose: string | null;
  environment: Environment;
  zone: string | null;
  network_scope: NetworkScope;
  criticality: Criticality;
  responsible: string;
  notes: string | null;
  revision: number;
  archived: boolean;
  archived_at: string | null;
  archived_by_name: string | null;
  server_count: number;
  created_at: string;
  created_by_name: string;
  updated_at: string;
  updated_by_name: string;
};

export type NetworkInput = {
  name: string;
  cidr: string;
  vlan_id: string;
  gateway: string;
  unit_code: string;
  location: string;
  purpose: string;
  environment: string;
  zone: string;
  network_scope: string;
  criticality: string;
  responsible: string;
  notes: string;
};

export type NetworkSummary = {
  id: string;
  code: string;
  name: string;
  cidr: string;
  vlan_id: number | null;
  network_scope: NetworkScope;
  environment: Environment;
  unit_code: UnitCode;
  archived: boolean;
};

export type ServerNetworkLink = {
  id: string;
  server_id: string;
  network_id: string;
  ip_address: string | null;
  interface_name: string | null;
  notes: string | null;
  created_at: string;
  created_by_name: string;
  server: ServerSummary;
  network: NetworkSummary;
};

export type ServerNetworkLinkInput = {
  server_id: string;
  network_id: string;
  ip_address: string;
  interface_name: string;
  notes: string;
};

export type Integration = {
  id: string;
  code: string;
  name: string;
  source_service_id: string | null;
  source_external_name: string | null;
  source_service: ServiceSummary | null;
  target_service_id: string | null;
  target_external_name: string | null;
  target_service: ServiceSummary | null;
  protocol: IntegrationProtocol;
  direction: IntegrationDirection;
  purpose: string | null;
  criticality: Criticality;
  responsible: string;
  administrative_status: AdministrativeStatus;
  notes: string | null;
  revision: number;
  archived: boolean;
  archived_at: string | null;
  archived_by_name: string | null;
  created_at: string;
  created_by_name: string;
  updated_at: string;
  updated_by_name: string;
};

export type IntegrationInput = {
  name: string;
  source_service_id: string | null;
  source_external_name: string | null;
  target_service_id: string | null;
  target_external_name: string | null;
  protocol: string;
  direction: string;
  purpose: string;
  criticality: string;
  responsible: string;
  administrative_status: string;
  notes: string;
};

export type ServiceDependency = {
  id: string;
  dependent_service_id: string;
  required_service_id: string;
  notes: string | null;
  created_at: string;
  created_by_name: string;
  dependent_service: ServiceSummary;
  required_service: ServiceSummary;
};

export type ServiceDependencyInput = {
  dependent_service_id: string;
  required_service_id: string;
  notes: string;
};

export type LinkRemoved = { id: string };

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
  can_view_services: boolean;
  can_manage_services: boolean;
  can_view_databases: boolean;
  can_manage_databases: boolean;
  can_view_networks: boolean;
  can_manage_networks: boolean;
  can_view_integrations: boolean;
  can_manage_integrations: boolean;
};

export type ArchiveFilter = "active" | "archived" | "all";

export type NetworkListQuery = {
  q?: string;
  unit_code?: string;
  environment?: string;
  network_scope?: string;
  criticality?: string;
  archived?: ArchiveFilter;
  sort?: string;
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

export type IntegrationListQuery = {
  q?: string;
  service_id?: string;
  protocol?: string;
  criticality?: string;
  administrative_status?: string;
  archived?: ArchiveFilter;
  sort?: string;
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

export type ServiceListQuery = {
  q?: string;
  service_kind?: string;
  environment?: string;
  unit_code?: string;
  criticality?: string;
  archived?: ArchiveFilter;
  sort?: string;
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

export type DatabaseListQuery = {
  q?: string;
  dbms?: string;
  environment?: string;
  criticality?: string;
  server_id?: string;
  archived?: ArchiveFilter;
  sort?: string;
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
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
  getLatestObservation: (serverId: string, signal?: AbortSignal) =>
    apiGet<Observation | null>(
      apiUrl(`/servers/${encodeURIComponent(serverId)}/observations/latest`),
      signal,
    ),
  listHostServices: (serverId: string, query: HostServiceQuery, signal?: AbortSignal) =>
    apiGet<HostServicesPage>(apiUrl(`/servers/${encodeURIComponent(serverId)}/host-services`, query), signal),
  listObservations: (serverId: string, signal?: AbortSignal) =>
    apiGet<Observation[]>(apiUrl(`/servers/${encodeURIComponent(serverId)}/observations`), signal),

  listActionPlans: (query: ActionPlanListQuery, signal?: AbortSignal) =>
    apiGet<Page<ActionPlan>>(apiUrl("/action-plans", query), signal),
  createActionPlan: (serverId: string, input: ActionPlanInput) =>
    apiPost<ActionPlan>(apiUrl(`/servers/${encodeURIComponent(serverId)}/action-plans`), input),
  updateActionPlan: (id: string, input: ActionPlanInput, revision: number) =>
    apiPut<ActionPlan>(apiUrl(`/action-plans/${encodeURIComponent(id)}`), { ...input, revision }),
  changeActionPlanStatus: (id: string, status: ActionStatus, revision: number) =>
    apiPost<ActionPlan>(apiUrl(`/action-plans/${encodeURIComponent(id)}/status`), { status, revision }),

  listServices: (query: ServiceListQuery, signal?: AbortSignal) =>
    apiGet<Page<Service>>(apiUrl("/services", query), signal),
  getService: (id: string, signal?: AbortSignal) =>
    apiGet<Service>(apiUrl(`/services/${encodeURIComponent(id)}`), signal),
  createService: (input: ServiceInput) => apiPost<Service>(apiUrl("/services"), input),
  updateService: (id: string, input: ServiceInput, revision: number) =>
    apiPut<Service>(apiUrl(`/services/${encodeURIComponent(id)}`), { ...input, revision }),
  archiveService: (id: string, revision: number) =>
    apiPost<Service>(apiUrl(`/services/${encodeURIComponent(id)}/archive`), { revision }),
  restoreService: (id: string, revision: number) =>
    apiPost<Service>(apiUrl(`/services/${encodeURIComponent(id)}/restore`), { revision }),
  listServiceHistory: (id: string, signal?: AbortSignal) =>
    apiGet<HistoryEvent[]>(apiUrl(`/services/${encodeURIComponent(id)}/history`), signal),
  listServiceHostings: (id: string, signal?: AbortSignal) =>
    apiGet<ServiceHosting[]>(apiUrl(`/services/${encodeURIComponent(id)}/hostings`), signal),
  listServiceDatabases: (id: string, signal?: AbortSignal) =>
    apiGet<DatabaseConsumer[]>(apiUrl(`/services/${encodeURIComponent(id)}/database-instances`), signal),
  listServerHostings: (serverId: string, signal?: AbortSignal) =>
    apiGet<ServiceHosting[]>(apiUrl(`/servers/${encodeURIComponent(serverId)}/service-hostings`), signal),
  createHosting: (input: ServiceHostingInput) => apiPost<ServiceHosting>(apiUrl("/service-hostings"), input),
  deleteHosting: (id: string) => apiDelete<LinkRemoved>(apiUrl(`/service-hostings/${encodeURIComponent(id)}`)),

  listDatabases: (query: DatabaseListQuery, signal?: AbortSignal) =>
    apiGet<Page<DatabaseInstance>>(apiUrl("/database-instances", query), signal),
  getDatabase: (id: string, signal?: AbortSignal) =>
    apiGet<DatabaseInstance>(apiUrl(`/database-instances/${encodeURIComponent(id)}`), signal),
  createDatabase: (input: DatabaseInstanceInput) =>
    apiPost<DatabaseInstance>(apiUrl("/database-instances"), input),
  updateDatabase: (id: string, input: DatabaseInstanceInput, revision: number) =>
    apiPut<DatabaseInstance>(apiUrl(`/database-instances/${encodeURIComponent(id)}`), { ...input, revision }),
  archiveDatabase: (id: string, revision: number) =>
    apiPost<DatabaseInstance>(apiUrl(`/database-instances/${encodeURIComponent(id)}/archive`), { revision }),
  restoreDatabase: (id: string, revision: number) =>
    apiPost<DatabaseInstance>(apiUrl(`/database-instances/${encodeURIComponent(id)}/restore`), { revision }),
  listDatabaseHistory: (id: string, signal?: AbortSignal) =>
    apiGet<HistoryEvent[]>(apiUrl(`/database-instances/${encodeURIComponent(id)}/history`), signal),
  listDatabaseConsumers: (id: string, signal?: AbortSignal) =>
    apiGet<DatabaseConsumer[]>(apiUrl(`/database-instances/${encodeURIComponent(id)}/consumers`), signal),
  createConsumer: (input: DatabaseConsumerInput) =>
    apiPost<DatabaseConsumer>(apiUrl("/database-consumers"), input),
  deleteConsumer: (id: string) =>
    apiDelete<LinkRemoved>(apiUrl(`/database-consumers/${encodeURIComponent(id)}`)),

  listNetworks: (query: NetworkListQuery, signal?: AbortSignal) =>
    apiGet<Page<Network>>(apiUrl("/networks", query), signal),
  getNetwork: (id: string, signal?: AbortSignal) =>
    apiGet<Network>(apiUrl(`/networks/${encodeURIComponent(id)}`), signal),
  createNetwork: (input: NetworkInput) => apiPost<Network>(apiUrl("/networks"), input),
  updateNetwork: (id: string, input: NetworkInput, revision: number) =>
    apiPut<Network>(apiUrl(`/networks/${encodeURIComponent(id)}`), { ...input, revision }),
  archiveNetwork: (id: string, revision: number) =>
    apiPost<Network>(apiUrl(`/networks/${encodeURIComponent(id)}/archive`), { revision }),
  restoreNetwork: (id: string, revision: number) =>
    apiPost<Network>(apiUrl(`/networks/${encodeURIComponent(id)}/restore`), { revision }),
  listNetworkHistory: (id: string, signal?: AbortSignal) =>
    apiGet<HistoryEvent[]>(apiUrl(`/networks/${encodeURIComponent(id)}/history`), signal),
  listNetworkServerLinks: (id: string, signal?: AbortSignal) =>
    apiGet<ServerNetworkLink[]>(apiUrl(`/networks/${encodeURIComponent(id)}/server-links`), signal),
  listServerNetworkLinks: (serverId: string, signal?: AbortSignal) =>
    apiGet<ServerNetworkLink[]>(apiUrl(`/servers/${encodeURIComponent(serverId)}/network-links`), signal),
  createServerNetworkLink: (input: ServerNetworkLinkInput) =>
    apiPost<ServerNetworkLink>(apiUrl("/server-network-links"), input),
  deleteServerNetworkLink: (id: string) =>
    apiDelete<LinkRemoved>(apiUrl(`/server-network-links/${encodeURIComponent(id)}`)),

  listIntegrations: (query: IntegrationListQuery, signal?: AbortSignal) =>
    apiGet<Page<Integration>>(apiUrl("/integrations", query), signal),
  getIntegration: (id: string, signal?: AbortSignal) =>
    apiGet<Integration>(apiUrl(`/integrations/${encodeURIComponent(id)}`), signal),
  createIntegration: (input: IntegrationInput) => apiPost<Integration>(apiUrl("/integrations"), input),
  updateIntegration: (id: string, input: IntegrationInput, revision: number) =>
    apiPut<Integration>(apiUrl(`/integrations/${encodeURIComponent(id)}`), { ...input, revision }),
  archiveIntegration: (id: string, revision: number) =>
    apiPost<Integration>(apiUrl(`/integrations/${encodeURIComponent(id)}/archive`), { revision }),
  restoreIntegration: (id: string, revision: number) =>
    apiPost<Integration>(apiUrl(`/integrations/${encodeURIComponent(id)}/restore`), { revision }),
  listIntegrationHistory: (id: string, signal?: AbortSignal) =>
    apiGet<HistoryEvent[]>(apiUrl(`/integrations/${encodeURIComponent(id)}/history`), signal),
  listServiceIntegrations: (serviceId: string, signal?: AbortSignal) =>
    apiGet<Integration[]>(apiUrl(`/services/${encodeURIComponent(serviceId)}/integrations`), signal),
  listServerIntegrations: (serverId: string, signal?: AbortSignal) =>
    apiGet<Integration[]>(apiUrl(`/servers/${encodeURIComponent(serverId)}/integrations`), signal),

  listServiceDependencies: (serviceId: string, signal?: AbortSignal) =>
    apiGet<ServiceDependency[]>(apiUrl(`/services/${encodeURIComponent(serviceId)}/dependencies`), signal),
  createServiceDependency: (input: ServiceDependencyInput) =>
    apiPost<ServiceDependency>(apiUrl("/service-dependencies"), input),
  deleteServiceDependency: (id: string) =>
    apiDelete<LinkRemoved>(apiUrl(`/service-dependencies/${encodeURIComponent(id)}`)),
};

/** Transições aceitas pela API (o backend revalida — isto só orienta a UI). */
export const ACTION_STATUS_TRANSITIONS: Record<ActionStatus, readonly ActionStatus[]> = {
  pending: ["in_progress", "done", "cancelled"],
  in_progress: ["pending", "done", "cancelled"],
  done: ["in_progress"],
  cancelled: ["pending"],
};
