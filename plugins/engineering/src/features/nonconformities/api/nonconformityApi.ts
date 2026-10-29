/** Cliente do bounded context NC — exclusivamente os contratos E-NC-*
 * da Engineering API. O MFE nunca chama api-delpi nem decide
 * autorização; erros chegam já classificados pelo httpClient. */

import {
  deleteJson,
  getJson,
  postJson,
  putJson,
} from "../../../api/httpClient";
import type {
  NcContextPayload,
  NcHistoryEvent,
  NcImportReport,
  NcIndicators,
  NcListResult,
  NcPayload,
  NcProblemTag,
  Nonconformity,
} from "../types";

const BASE = "/apps/engineering-api/v1/nonconformities";

type Envelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type NcListFilters = {
  status?: string;
  sale_number?: string;
  lmp_number?: string;
  customer_name?: string;
  product_code?: string;
  problem_tag?: string;
  date_start?: string;
  date_end?: string;
  sort_by?: string;
  sort_dir?: string;
  page?: number;
  page_size?: number;
};

function qs(filters: NcListFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }
  const text = params.toString();
  return text ? `?${text}` : "";
}

export async function fetchNonconformities(
  filters: NcListFilters,
  signal?: AbortSignal,
): Promise<NcListResult> {
  const res = await getJson<Envelope<NcListResult>>(`${BASE}${qs(filters)}`, signal);
  return res.data;
}

export async function fetchNonconformity(
  recordId: string,
  signal?: AbortSignal,
): Promise<Nonconformity> {
  const res = await getJson<Envelope<Nonconformity>>(
    `${BASE}/${recordId}`,
    signal,
  );
  return res.data;
}

export async function fetchNonconformityHistory(
  recordId: string,
  signal?: AbortSignal,
): Promise<NcHistoryEvent[]> {
  const res = await getJson<Envelope<{ items: NcHistoryEvent[] }>>(
    `${BASE}/${recordId}/history`,
    signal,
  );
  return res.data.items;
}

export async function fetchNonconformityContext(
  recordId: string,
  signal?: AbortSignal,
): Promise<NcContextPayload> {
  const res = await getJson<Envelope<NcContextPayload>>(
    `${BASE}/${recordId}/context`,
    signal,
  );
  return res.data;
}

export async function fetchNcIndicators(
  signal?: AbortSignal,
): Promise<NcIndicators> {
  const res = await getJson<Envelope<NcIndicators>>(
    `${BASE}/indicators`,
    signal,
  );
  return res.data;
}

export async function fetchProblemTags(
  signal?: AbortSignal,
): Promise<NcProblemTag[]> {
  const res = await getJson<Envelope<{ items: NcProblemTag[] }>>(
    `${BASE}/problem-tags`,
    signal,
  );
  return res.data.items;
}

export async function fetchNonconformitiesExport(signal?: AbortSignal) {
  const res = await getJson<
    Envelope<{ version: number; generated_at: string; count: number; items: Nonconformity[] }>
  >(`${BASE}/export`, signal);
  return res.data;
}

export async function createNonconformity(
  payload: NcPayload,
  signal?: AbortSignal,
): Promise<Nonconformity> {
  const res = await postJson<Envelope<Nonconformity>>(BASE, payload, signal);
  return res.data;
}

export async function updateNonconformity(
  recordId: string,
  payload: NcPayload,
  signal?: AbortSignal,
): Promise<Nonconformity> {
  const res = await putJson<Envelope<Nonconformity>>(
    `${BASE}/${recordId}`,
    payload,
    signal,
  );
  return res.data;
}

export async function deleteNonconformity(
  recordId: string,
  signal?: AbortSignal,
): Promise<void> {
  await deleteJson<Envelope<{ id: string; deleted: boolean }>>(
    `${BASE}/${recordId}`,
    signal,
  );
}

export async function importNonconformities(
  items: unknown[],
  options: { dryRun: boolean; confirmReplace: boolean },
  signal?: AbortSignal,
): Promise<NcImportReport> {
  const res = await postJson<Envelope<NcImportReport>>(
    `${BASE}/import`,
    {
      items,
      dry_run: options.dryRun,
      confirm_replace: options.confirmReplace,
    },
    signal,
  );
  return res.data;
}
