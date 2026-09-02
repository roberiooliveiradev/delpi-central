export type DeviceBinding = {
  id: string;
  deviceId: string;
  anchorType: string;
  placementLabel: string;
  placementKey: string;
  workCenterCode: string | null;
  workCenterName: string | null;
  machineCode: string | null;
  machineLabel: string | null;
  equipmentLabel: string | null;
  areaLabel: string | null;
  resourceCode: string | null;
  toolCode: string | null;
  notes: string | null;
};

export type DeviceCapabilities = {
  metrics: string[];
  commands: string[];
  operatorSurface: string;
};

export type DeviceStatus = "online" | "offline" | "disabled" | "no_binding";

export type DeviceListItem = {
  id: string;
  branch: string;
  name: string;
  ipAddress: string;
  driverKey: string;
  roleKey: string;
  enabled: boolean;
  pollIntervalSeconds: number;
  lastSeenAt: string | null;
  lastMetrics: Record<string, number | string>;
  lastError: string | null;
  status: DeviceStatus;
  online: boolean;
  graceSeconds: number;
  capabilities?: DeviceCapabilities;
  binding: DeviceBinding | null;
  periodDeltas?: {
    day?: Record<string, number>;
    shift?: Record<string, number>;
  };
};

export type DeviceSummary = {
  total: number;
  online: number;
  offline: number;
  withoutBinding: number;
  branch?: string;
  branches?: string[];
  counterDelta?: {
    day?: Record<string, number>;
    shift?: Record<string, number>;
  };
};
