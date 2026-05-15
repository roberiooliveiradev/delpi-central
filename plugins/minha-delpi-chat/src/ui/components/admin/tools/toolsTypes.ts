export type AdminToolHealthStatus = "ok" | "warning" | "error" | "unknown";

export type AdminExternalActionSummary = {
  id: string;
  name: string;
  provider: string;
  status: AdminToolHealthStatus;
  lastRunLabel: string;
  calls24h: number;
};

export type AdminToolHealthItem = {
  id: string;
  label: string;
  status: AdminToolHealthStatus;
  description: string;
};

export type AdminToolsBackendPlaceholders = {
  loadExternalActions?: () => Promise<void>;
  testExternalAction?: (actionId: string) => Promise<void>;
  syncOpenApiProviders?: () => Promise<void>;
  loadToolHealth?: () => Promise<void>;
};
