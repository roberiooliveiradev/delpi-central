import { httpGet, httpJson, PRODUCTION_PULSE_API_BASE } from "./httpClient";
import type { DeviceListItem, DeviceSummary } from "../types/device";
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
    driverKey: device.driverKey,
    pollIntervalSeconds: device.pollIntervalSeconds,
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
      driverKey: device.driverKey,
      pollIntervalSeconds: device.pollIntervalSeconds,
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

export async function pollDevice(deviceId: string): Promise<void> {
  await httpJson("POST", `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/poll`);
}
