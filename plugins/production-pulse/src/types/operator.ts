import type { DeviceListItem } from "./device";

export type OperatorAnchorFilter = "" | "work_center" | "machine" | "equipment";

export type OperatorPlacement = {
  placementKey: string;
  placementLabel: string;
  anchorType: string;
  branch: string;
  deviceCount: number;
  onlineCount: number;
  byRole: Record<string, number>;
  primaryMetricPreview: {
    key: string;
    value: number | string;
  } | null;
};

export type OperatorDeviceItem = DeviceListItem & {
  placementKey?: string;
  placementLabel?: string;
  anchorType?: string;
};

export type OperatorCommandResult = {
  commandKey: string;
  success: boolean;
  metrics?: Record<string, number | string>;
  errorMessage?: string | null;
  commandId?: string;
  readingId?: number;
};
