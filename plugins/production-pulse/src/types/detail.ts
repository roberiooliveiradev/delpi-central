export type DeviceDetailTab = "overview" | "history" | "commands";

export type DeviceReading = {
  id: number;
  deviceId: string;
  metrics: Record<string, number | string>;
  deltaMetrics: Record<string, number | string>;
  meta: Record<string, unknown>;
  source: string;
  recordedAt: string;
  createdAt?: string;
};

export type DeviceCommandAudit = {
  id: string;
  deviceId: string;
  commandKey: string;
  issuedBy: string | null;
  success: boolean;
  errorMessage: string | null;
  requestPayload: Record<string, unknown>;
  responsePayload: Record<string, unknown>;
  createdAt: string;
};

export type PaginatedItems<T> = {
  items: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
};

export type LivePollResult = {
  metrics: Record<string, number | string>;
  recordedAt: string;
  status: string;
  online: boolean;
  graceSeconds?: number;
  deltaMetrics?: Record<string, number | string>;
  capabilities?: {
    metrics: string[];
    commands: string[];
    operatorSurface: string;
  };
  latencyMs?: number;
};
