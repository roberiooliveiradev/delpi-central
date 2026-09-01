import { httpGet, httpJson, PRODUCTION_PULSE_API_BASE } from "./httpClient";
import type { DeviceListItem, DeviceSummary } from "../types/device";

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

export async function pollDevice(deviceId: string): Promise<void> {
  await httpJson("POST", `${PRODUCTION_PULSE_API_BASE}/devices/${deviceId}/poll`);
}
