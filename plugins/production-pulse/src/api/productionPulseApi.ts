import { httpGet, httpJson, PRODUCTION_PULSE_API_BASE } from "./httpClient";
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

export async function createDevice(device: DeviceFormValues): Promise<DeviceListItem> {
  const payload = await httpJson<ApiEnvelope<DeviceListItem>>("POST", `${PRODUCTION_PULSE_API_BASE}/devices`, {
    name: device.name.trim(),
    branch: device.branch,
    ipAddress: device.ipAddress.trim(),
    controllerCode: device.controllerCode.trim() || null,
    firmwareSource: device.firmwareSource.trim() ? device.firmwareSource.replace(/^\n+|\n+$/g, "") : null,
    driverKey: device.driverKey,
    pollIntervalMs: device.pollIntervalMs,
    enabled: device.enabled,
  });
  return payload.data;
}

export async function replaceDevice(deviceId: string, device: DeviceFormValues): Promise<DeviceListItem> {
  const payload = await httpJson<ApiEnvelope<DeviceListItem>>(
    "PUT",
    `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}`,
    {
      name: device.name.trim(),
      branch: device.branch,
      ipAddress: device.ipAddress.trim(),
      controllerCode: device.controllerCode.trim() || null,
      firmwareSource: device.firmwareSource.trim()
        ? device.firmwareSource.replace(/^\n+|\n+$/g, "")
        : null,
      driverKey: device.driverKey,
      pollIntervalMs: device.pollIntervalMs,
      enabled: device.enabled,
    },
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
  const payload = await httpJson<ApiEnvelope<ProbeResult>>(
    "POST",
    `${PRODUCTION_PULSE_API_BASE}/devices/test-probe`,
    {
      branch: device.branch,
      ipAddress: device.ipAddress.trim(),
      driverKey: device.driverKey,
    },
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
