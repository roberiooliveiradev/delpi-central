import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  AppointmentsByOpData,
  AppointmentsListData,
  AppointmentsQueryFilters,
  AppointmentsSeriesData,
  AppointmentsSummaryData,
  WorkCenterItem,
} from "../types/appointments";
import { queryString } from "../utils/queryParams";

const API_BASE = "/apps/api-delpi/production/appointments";

type RequestOptions = { signal?: AbortSignal };

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

function baseQuery(filters: AppointmentsQueryFilters) {
  return {
    branch: filters.branch,
    date_start: filters.dateStart,
    date_end: filters.dateEnd,
    work_center: filters.workCenter || undefined,
    op: filters.op || undefined,
    product: filters.product || undefined,
  };
}

export async function fetchWorkCenters(
  branch: string,
  options: RequestOptions = {},
): Promise<{ items: WorkCenterItem[] }> {
  return getEnvelope(`/work-centers${queryString({ branch })}`, options);
}

export async function fetchAppointmentsSummary(
  filters: AppointmentsQueryFilters,
  options: RequestOptions = {},
): Promise<AppointmentsSummaryData> {
  return getEnvelope(`/summary${queryString(baseQuery(filters))}`, options);
}

export async function fetchAppointmentsSeries(
  filters: AppointmentsQueryFilters,
  groupBy: "day" | "day_work_center" = "day",
  options: RequestOptions = {},
): Promise<AppointmentsSeriesData> {
  return getEnvelope(
    `/series${queryString({ ...baseQuery(filters), group_by: groupBy })}`,
    options,
  );
}

export async function fetchAppointmentsList(
  filters: AppointmentsQueryFilters,
  page: number,
  pageSize: number,
  options: RequestOptions = {},
): Promise<AppointmentsListData> {
  return getEnvelope(
    `${queryString({ ...baseQuery(filters), page, page_size: pageSize })}`,
    options,
  );
}

export async function fetchAppointmentsByOp(
  filters: AppointmentsQueryFilters,
  page: number,
  pageSize: number,
  options: RequestOptions = {},
): Promise<AppointmentsByOpData> {
  return getEnvelope(
    `/by-op${queryString({ ...baseQuery(filters), page, page_size: pageSize })}`,
    options,
  );
}
