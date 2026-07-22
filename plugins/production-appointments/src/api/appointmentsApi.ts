import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  AppointmentRow,
  AppointmentsByOpData,
  AppointmentsListData,
  AppointmentsQueryFilters,
  AppointmentsSeriesData,
  AppointmentsSummaryData,
  ByOpRow,
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

type ListRequestOptions = RequestOptions & { search?: string };

function listQuery(
  filters: AppointmentsQueryFilters,
  page: number,
  pageSize: number,
  search?: string,
) {
  return {
    ...baseQuery(filters),
    page,
    page_size: pageSize,
    search: search?.trim() || undefined,
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
  options: ListRequestOptions = {},
): Promise<AppointmentsListData> {
  return getEnvelope(
    `${queryString(listQuery(filters, page, pageSize, options.search))}`,
    options,
  );
}

export async function fetchAppointmentsByOp(
  filters: AppointmentsQueryFilters,
  page: number,
  pageSize: number,
  options: ListRequestOptions = {},
): Promise<AppointmentsByOpData> {
  return getEnvelope(
    `/by-op${queryString(listQuery(filters, page, pageSize, options.search))}`,
    options,
  );
}

const EXPORT_PAGE_SIZE = 200;

async function fetchAllPages<T>(
  fetchPage: (page: number, pageSize: number) => Promise<{ items: T[]; pagination: { total_pages: number } }>,
  options: RequestOptions = {},
): Promise<T[]> {
  const first = await fetchPage(1, EXPORT_PAGE_SIZE);
  const items = [...first.items];
  const totalPages = Math.max(1, first.pagination.total_pages);
  for (let page = 2; page <= totalPages; page += 1) {
    if (options.signal?.aborted) break;
    const next = await fetchPage(page, EXPORT_PAGE_SIZE);
    items.push(...next.items);
  }
  return items;
}

export async function fetchAllAppointments(
  filters: AppointmentsQueryFilters,
  options: ListRequestOptions = {},
): Promise<AppointmentRow[]> {
  return fetchAllPages(
    (page, pageSize) =>
      fetchAppointmentsList(filters, page, pageSize, {
        ...options,
        search: options.search,
      }),
    options,
  );
}

export async function fetchAllAppointmentsByOp(
  filters: AppointmentsQueryFilters,
  options: ListRequestOptions = {},
): Promise<ByOpRow[]> {
  return fetchAllPages(
    (page, pageSize) =>
      fetchAppointmentsByOp(filters, page, pageSize, {
        ...options,
        search: options.search,
      }),
    options,
  );
}
