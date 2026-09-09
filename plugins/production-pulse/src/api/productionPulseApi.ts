import { httpGet, httpJson, PRODUCTION_PULSE_API_BASE, getAccessToken } from "./httpClient";
import type { DeviceListItem, DeviceSummary } from "../types/device";
import type { DeviceCommandAudit, DeviceReading, LivePollResult, PaginatedItems } from "../types/detail";
import type {
  OperatorCommandResult,
  OperatorDeviceItem,
  OperatorPlacement,
} from "../types/operator";
import type {
  DeviceFormValues,
  DriverCatalogItem,
  ProbeResult,
  WorkCenterCatalogItem,
} from "../types/form";
import { bindingToApiBody } from "../utils/deviceFormValidation";
import type { BindingFormValues } from "../types/form";

type ApiEnvelope<T> = {
  success: boolean;
  data: T;
};

export async function fetchProductionPulseHealth(): Promise<{ service: string; status: string }> {
  const payload = await httpGet<ApiEnvelope<{ service: string; status: string }>>(
    `${PRODUCTION_PULSE_API_BASE}/health`,
  );
  return payload.data;
}

export type FetchDevicesParams = {
  branch?: string;
  role?: string;
  search?: string;
  signal?: AbortSignal;
};

export async function fetchDeviceSummary(
  branch: string,
  options: { signal?: AbortSignal } = {},
): Promise<DeviceSummary> {
  const query = branch ? `?branch=${encodeURIComponent(branch)}` : "";
  const payload = await httpGet<ApiEnvelope<DeviceSummary>>(
    `${PRODUCTION_PULSE_API_BASE}/summary${query}`,
    { signal: options.signal },
  );
  return payload.data;
}

export async function fetchDevices(
  params: FetchDevicesParams,
): Promise<DeviceListItem[]> {
  const searchParams = new URLSearchParams();
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.role) searchParams.set("role", params.role);
  if (params.search?.trim()) searchParams.set("search", params.search.trim());
  const suffix = searchParams.toString();
  const payload = await httpGet<ApiEnvelope<{ items: DeviceListItem[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/devices${suffix ? `?${suffix}` : ""}`,
    { signal: params.signal },
  );
  return payload.data.items;
}

export async function fetchDevice(deviceId: string): Promise<DeviceListItem> {
  const payload = await httpGet<ApiEnvelope<DeviceListItem>>(
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}`,
  );
  return payload.data;
}

export async function fetchDriverCatalog(): Promise<DriverCatalogItem[]> {
  const payload = await httpGet<ApiEnvelope<{ drivers: DriverCatalogItem[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/catalog/drivers`,
  );
  return payload.data.drivers;
}

export async function fetchWorkCenters(
  branch: string,
  search?: string,
): Promise<WorkCenterCatalogItem[]> {
  const params = new URLSearchParams({ branch });
  if (search?.trim()) params.set("search", search.trim());
  const payload = await httpGet<ApiEnvelope<{ items: WorkCenterCatalogItem[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/catalog/work-centers?${params}`,
  );
  return payload.data.items;
}

function deviceFormToApiBody(device: DeviceFormValues): Record<string, unknown> {
  const debounceRaw = device.debounceMs.trim();
  const debounceMs = debounceRaw ? Number.parseInt(debounceRaw, 10) : null;
  const body: Record<string, unknown> = {
    name: device.name.trim(),
    branch: device.branch,
    ipAddress: device.ipAddress.trim(),
    controllerCode: device.controllerCode.trim() || null,
    firmwareSource: device.firmwareSource.trim()
      ? device.firmwareSource.replace(/^\n+|\n+$/g, "")
      : null,
    wifiSsid: device.wifiSsid.trim() || null,
    driverKey: device.driverKey,
    pollIntervalMs: device.pollIntervalMs,
    enabled: device.enabled,
    debounceMs: Number.isFinite(debounceMs as number) ? debounceMs : null,
  };
  const wifiPassword = device.wifiPassword.trim();
  if (wifiPassword) body.wifiPassword = wifiPassword;
  const apiToken = device.apiToken.trim();
  if (apiToken) body.apiToken = apiToken;
  return body;
}

export async function createDevice(device: DeviceFormValues): Promise<DeviceListItem> {
  const payload = await httpJson<ApiEnvelope<DeviceListItem>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/devices`,
    deviceFormToApiBody(device),
  );
  return payload.data;
}

export async function replaceDevice(deviceId: string, device: DeviceFormValues): Promise<DeviceListItem> {
  const payload = await httpJson<ApiEnvelope<DeviceListItem>>(
    "PUT",
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}`,
    deviceFormToApiBody(device),
  );
  return payload.data;
}

export async function upsertDeviceBinding(
  deviceId: string,
  binding: BindingFormValues,
): Promise<void> {
  await httpJson("PUT", `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/binding`, bindingToApiBody(binding));
}

export async function testDeviceProbe(device: DeviceFormValues): Promise<ProbeResult> {
  const body: Record<string, unknown> = {
    branch: device.branch,
    ipAddress: device.ipAddress.trim(),
    driverKey: device.driverKey,
  };
  const apiToken = device.apiToken.trim();
  if (apiToken) body.apiToken = apiToken;
  const payload = await httpJson<ApiEnvelope<ProbeResult>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/devices/test-probe`,
    body,
  );
  return payload.data;
}

export async function testExistingDevice(deviceId: string): Promise<ProbeResult> {
  const payload = await httpJson<ApiEnvelope<ProbeResult>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/test`,
  );
  return payload.data;
}

export async function pollDevice(deviceId: string): Promise<LivePollResult> {
  const payload = await httpJson<ApiEnvelope<LivePollResult>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/poll`,
  );
  return payload.data;
}

export async function fetchDeviceLive(deviceId: string): Promise<LivePollResult> {
  const payload = await httpGet<ApiEnvelope<LivePollResult>>(
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/live`,
  );
  return payload.data;
}

export type FetchDeviceReadingsParams = {
  page?: number;
  pageSize?: number;
  from?: string;
  to?: string;
  metric?: string;
  sampleIntervalMs?: number;
  resolution?: "raw" | "hour" | "day";
  signal?: AbortSignal;
};

export async function fetchDeviceReadings(
  deviceId: string,
  params: FetchDeviceReadingsParams = {},
): Promise<PaginatedItems<DeviceReading>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.pageSize) searchParams.set("pageSize", String(params.pageSize));
  if (params.from) searchParams.set("from", params.from);
  if (params.to) searchParams.set("to", params.to);
  if (params.metric) searchParams.set("metric", params.metric);
  if (params.resolution && params.resolution !== "raw") {
    searchParams.set("resolution", params.resolution);
  }
  if (params.sampleIntervalMs != null && params.sampleIntervalMs > 0) {
    searchParams.set("sampleIntervalMs", String(params.sampleIntervalMs));
  }
  const suffix = searchParams.toString();
  const payload = await httpGet<ApiEnvelope<PaginatedItems<DeviceReading>>>(
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/readings${suffix ? `?${suffix}` : ""}`,
    { signal: params.signal },
  );
  return payload.data;
}

export type FetchDeviceCommandsParams = {
  page?: number;
  pageSize?: number;
  signal?: AbortSignal;
};

export async function fetchDeviceCommands(
  deviceId: string,
  params: FetchDeviceCommandsParams = {},
): Promise<PaginatedItems<DeviceCommandAudit>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.pageSize) searchParams.set("pageSize", String(params.pageSize));
  const suffix = searchParams.toString();
  const payload = await httpGet<ApiEnvelope<PaginatedItems<DeviceCommandAudit>>>(
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/commands${suffix ? `?${suffix}` : ""}`,
    { signal: params.signal },
  );
  return payload.data;
}

export async function executeDeviceCommand(
  deviceId: string,
  commandKey: string,
): Promise<DeviceCommandAudit> {
  const payload = await httpJson<ApiEnvelope<DeviceCommandAudit>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/commands/${encodeURIComponent(commandKey)}`,
  );
  return payload.data;
}

export type FetchOperatorPlacementsParams = {
  branch: string;
  anchorType?: string;
  search?: string;
  signal?: AbortSignal;
};

export async function fetchOperatorPlacements(
  params: FetchOperatorPlacementsParams,
): Promise<OperatorPlacement[]> {
  const searchParams = new URLSearchParams({ branch: params.branch });
  if (params.anchorType) searchParams.set("anchorType", params.anchorType);
  if (params.search?.trim()) searchParams.set("search", params.search.trim());
  const payload = await httpGet<ApiEnvelope<{ items: OperatorPlacement[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/operator/placements?${searchParams}`,
    { signal: params.signal },
  );
  return payload.data.items;
}

export async function fetchOperatorPlacementDevices(
  placementKey: string,
  branch: string,
  options: { signal?: AbortSignal } = {},
): Promise<OperatorDeviceItem[]> {
  const params = new URLSearchParams({ branch });
  const payload = await httpGet<ApiEnvelope<{ items: OperatorDeviceItem[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/operator/placements/${encodeURIComponent(placementKey)}/devices?${params}`,
    { signal: options.signal },
  );
  return payload.data.items;
}

export async function fetchOperatorDevice(deviceId: string): Promise<OperatorDeviceItem> {
  const payload = await httpGet<ApiEnvelope<OperatorDeviceItem>>(
    `${PRODUCTION_PULSE_API_BASE}/operator/devices/${deviceId}`,
  );
  return payload.data;
}

export async function executeOperatorCommand(
  deviceId: string,
  commandKey: string,
): Promise<OperatorCommandResult> {
  const payload = await httpJson<ApiEnvelope<OperatorCommandResult>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/operator/devices/${deviceId}/commands/${encodeURIComponent(commandKey)}`,
  );
  return payload.data;
}

export type FirmwareCatalogItem = {
  id: string;
  firmwareKey: string;
  driverKey: string;
  version: string;
  displayName: string;
  artifactSha256: string;
  artifactSizeBytes: number;
  releaseNotes: string | null;
  minCompatibleVersion: string | null;
  publishedAt: string | null;
  createdAt: string | null;
};

export type FirmwareUpdateJob = {
  id: string;
  firmwareId: string;
  branch: string;
  trigger: "manual" | "scheduled";
  scheduledAt: string | null;
  status: string;
  filter: Record<string, unknown>;
  createdAt: string | null;
};

export type FirmwareUpdateTarget = {
  id: string;
  jobId: string;
  deviceId: string;
  status: string;
  fromVersion: string | null;
  toVersion: string | null;
  errorCode: string | null;
  bytesReceived?: number | null;
  bytesTotal?: number | null;
  progressPercent?: number | null;
  updatedAt?: string | null;
};

export type DeviceFirmwareUpdateStatus = {
  active: boolean;
  jobId?: string | null;
  targetId?: string | null;
  status?: string | null;
  fromVersion?: string | null;
  toVersion?: string | null;
  errorCode?: string | null;
  firmwareKey?: string | null;
  bytesReceived?: number | null;
  bytesTotal?: number | null;
  progressPercent?: number | null;
  jobStatus?: string | null;
  updatedAt?: string | null;
  target?: FirmwareUpdateTarget | null;
};

export type FirmwareUpdateSummary = {
  branch: string;
  firmwareKey: string | null;
  total: number;
  updated: number;
  updating: number;
  failed: number;
};

export async function fetchFirmwares(params: {
  firmwareKey?: string;
  driverKey?: string;
  signal?: AbortSignal;
} = {}): Promise<FirmwareCatalogItem[]> {
  const searchParams = new URLSearchParams();
  if (params.firmwareKey) searchParams.set("firmwareKey", params.firmwareKey);
  if (params.driverKey) searchParams.set("driverKey", params.driverKey);
  const suffix = searchParams.toString();
  const payload = await httpGet<ApiEnvelope<{ items: FirmwareCatalogItem[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/firmwares${suffix ? `?${suffix}` : ""}`,
    { signal: params.signal },
  );
  return payload.data.items;
}

export async function publishFirmware(form: FormData): Promise<FirmwareCatalogItem> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": "production-pulse",
  };
  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${PRODUCTION_PULSE_API_BASE}/firmwares`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!response.ok) {
    const text = await response.text();
    let message = `Erro HTTP ${response.status}`;
    try {
      const body = JSON.parse(text) as { error?: { message?: string } };
      message = body.error?.message ?? message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  const payload = (await response.json()) as ApiEnvelope<FirmwareCatalogItem>;
  return payload.data;
}

export async function fetchFirmwareUpdateJobs(branch?: string): Promise<FirmwareUpdateJob[]> {
  const query = branch ? `?branch=${encodeURIComponent(branch)}` : "";
  const payload = await httpGet<ApiEnvelope<{ items: FirmwareUpdateJob[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/firmware-update-jobs${query}`,
  );
  return payload.data.items;
}

export async function createFirmwareUpdateJob(body: {
  firmwareId: string;
  branch: string;
  trigger: "manual" | "scheduled";
  scheduledAt?: string;
  filter?: Record<string, unknown>;
}): Promise<FirmwareUpdateJob> {
  const payload = await httpJson<ApiEnvelope<FirmwareUpdateJob>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/firmware-update-jobs`,
    body,
  );
  return payload.data;
}

export async function fetchFirmwareUpdateTargets(jobId: string): Promise<FirmwareUpdateTarget[]> {
  const payload = await httpGet<ApiEnvelope<{ items: FirmwareUpdateTarget[] }>>(
    `${PRODUCTION_PULSE_API_BASE}/firmware-update-jobs/${jobId}/targets`,
  );
  return payload.data.items;
}

export async function cancelFirmwareUpdateJob(jobId: string): Promise<FirmwareUpdateJob> {
  const payload = await httpJson<ApiEnvelope<FirmwareUpdateJob>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/firmware-update-jobs/${jobId}/cancel`,
  );
  return payload.data;
}

export async function fetchFirmwareUpdateSummary(
  branch: string,
  firmwareKey?: string,
): Promise<FirmwareUpdateSummary> {
  const params = new URLSearchParams({ branch });
  if (firmwareKey) params.set("firmwareKey", firmwareKey);
  const payload = await httpGet<ApiEnvelope<FirmwareUpdateSummary>>(
    `${PRODUCTION_PULSE_API_BASE}/firmware-update-summary?${params}`,
  );
  return payload.data;
}

export async function putDeviceFirmwareLink(
  deviceId: string,
  firmwareKey: string | null,
): Promise<DeviceListItem> {
  const payload = await httpJson<ApiEnvelope<DeviceListItem>>(
    "PUT",
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/firmware-link`,
    { firmwareKey },
  );
  return payload.data;
}

export async function fetchDeviceFirmwareUpdateStatus(
  deviceId: string,
  signal?: AbortSignal,
): Promise<DeviceFirmwareUpdateStatus> {
  const payload = await httpGet<ApiEnvelope<DeviceFirmwareUpdateStatus>>(
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/firmware-update-status`,
    { signal },
  );
  return payload.data;
}
