import { httpGet, httpPatch, httpPost, httpPut } from "./httpClient";

/** Catálogo global de motivos de parada — os campos OEE não fazem parte do contrato. */
export type DowntimeReason = {
  code: string;
  label: string;
  category: string;
  requiresNote: boolean;
  active: boolean;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
};

export type CreateDowntimeReasonInput = {
  code: string;
  label: string;
  category: string;
  requiresNote: boolean;
  sortOrder: number;
};

export type UpdateDowntimeReasonInput = {
  label: string;
  category: string;
  requiresNote: boolean;
  sortOrder: number;
};

export function listDowntimeReasons(signal?: AbortSignal) {
  return httpGet<{ items: DowntimeReason[] }>("/registrations/downtime-reasons", { signal });
}

export function createDowntimeReason(payload: CreateDowntimeReasonInput) {
  return httpPost<DowntimeReason>("/registrations/downtime-reasons", payload);
}

export function updateDowntimeReason(code: string, payload: UpdateDowntimeReasonInput) {
  return httpPut<DowntimeReason>(
    `/registrations/downtime-reasons/${encodeURIComponent(code)}`,
    payload,
  );
}

export function setDowntimeReasonActive(code: string, active: boolean) {
  return httpPatch<DowntimeReason>(
    `/registrations/downtime-reasons/${encodeURIComponent(code)}/active`,
    { active },
  );
}
