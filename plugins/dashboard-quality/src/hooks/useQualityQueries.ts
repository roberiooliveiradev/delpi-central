import {
  getAudit5sSummary,
  getKaizenSummary,
  getPpmExternalSummary,
  getPpmInternalSummary,
  listNonconformities,
  listPpmExternal,
  listPpmInternal,
} from "../api/qualityApi";
import type { Audit5sSummaryParams } from "../types/audit5s";
import type { KaizenSummaryParams } from "../types/kaizen";
import type { ListNonconformitiesParams } from "../types/nonconformity";
import type { DateRangeParams, ListPpmParams } from "../types/ppm";
import { useQualityResource } from "./useQualityResource";

export function usePpmInternalSummary(
  params: DateRangeParams = {},
  enabled = true
) {
  return useQualityResource(
    (signal) => getPpmInternalSummary(params, signal),
    [params.branch, params.date_start, params.date_end],
    { enabled }
  );
}

export function usePpmExternalSummary(
  params: DateRangeParams = {},
  enabled = true
) {
  return useQualityResource(
    (signal) => getPpmExternalSummary(params, signal),
    [params.branch, params.date_start, params.date_end],
    { enabled }
  );
}

export function usePpmInternalList(params: ListPpmParams = {}, enabled = true) {
  return useQualityResource(
    (signal) => listPpmInternal(params, signal),
    [
      params.branch,
      params.date_start,
      params.date_end,
      params.page,
      params.page_size,
    ],
    { enabled }
  );
}

export function usePpmExternalList(params: ListPpmParams = {}, enabled = true) {
  return useQualityResource(
    (signal) => listPpmExternal(params, signal),
    [
      params.branch,
      params.date_start,
      params.date_end,
      params.page,
      params.page_size,
    ],
    { enabled }
  );
}

export function useKaizenSummary(
  params: KaizenSummaryParams = {},
  enabled = true
) {
  return useQualityResource(
    (signal) => getKaizenSummary(params, signal),
    [
      params.title,
      params.status,
      params.branch,
      params.date_start,
      params.date_end,
    ],
    { enabled }
  );
}

export function useAudit5sSummary(
  params: Audit5sSummaryParams = {},
  enabled = true
) {
  return useQualityResource(
    (signal) => getAudit5sSummary(params, signal),
    [params.start_date, params.end_date, params.branch],
    { enabled }
  );
}

export function useNonconformities(
  params: ListNonconformitiesParams = {},
  enabled = true
) {
  return useQualityResource(
    (signal) => listNonconformities(params, signal),
    [
      params.type,
      params.branch,
      params.date_start,
      params.date_end,
      params.status,
      params.item_code,
      params.description,
      params.page,
      params.page_size,
    ],
    { enabled }
  );
}
