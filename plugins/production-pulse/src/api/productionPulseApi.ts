import { httpGet, PRODUCTION_PULSE_API_BASE } from "./httpClient";

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
