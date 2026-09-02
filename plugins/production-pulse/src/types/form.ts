import {
  POLL_INTERVAL_DEFAULT_MS,
} from "../content/deviceValidationContent";

export type AnchorType = "work_center" | "machine" | "equipment" | "area" | "standalone";

export type DeviceFormValues = {
  name: string;
  branch: string;
  ipAddress: string;
  driverKey: string;
  pollIntervalMs: number;
  enabled: boolean;
};

export type BindingFormValues = {
  anchorType: AnchorType;
  workCenterCode: string;
  workCenterName: string;
  machineLabel: string;
  equipmentLabel: string;
  areaLabel: string;
  resourceCode: string;
  toolCode: string;
  notes: string;
};

export type DriverCatalogMetric = {
  key: string;
  labelPt?: string;
  unit?: string;
  primary?: boolean;
};

export type DriverCatalogItem = {
  key: string;
  roleKey: string;
  labelPt: string;
  descriptionPt?: string;
  metrics?: DriverCatalogMetric[];
  commands?: string[];
  operatorSurface?: string;
};

export type WorkCenterCatalogItem = {
  branch: string;
  workCenterCode: string;
  workCenterName: string;
  isFinalInspection?: boolean;
};

export type ProbeResult = {
  driverKey: string;
  online: boolean;
  metrics?: Record<string, number | string>;
  latencyMs?: number;
  error?: string;
  errorMessage?: string;
};

export const DEFAULT_BINDING_VALUES: BindingFormValues = {
  anchorType: "equipment",
  workCenterCode: "",
  workCenterName: "",
  machineLabel: "",
  equipmentLabel: "",
  areaLabel: "",
  resourceCode: "",
  toolCode: "",
  notes: "",
};

export const DEFAULT_DEVICE_FORM_VALUES: DeviceFormValues = {
  name: "",
  branch: "01",
  ipAddress: "",
  driverKey: "esp8266_counter_v1",
  pollIntervalMs: POLL_INTERVAL_DEFAULT_MS,
  enabled: true,
};
