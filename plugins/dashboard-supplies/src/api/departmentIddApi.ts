import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";

export const DEPARTMENT_IDD_API_BASE = "/apps/api-delpi/dashboard";

export type DepartmentIddItem = {
  department_id: string;
  department_name?: string | null;
  score?: number | null;
  classification?: string | null;
  contribution?: number | null;
  variation?: {
    absolute?: number | null;
    percent?: number | null;
  } | null;
  partial_success?: boolean;
};

type DepartmentIddResponse = {
  item: DepartmentIddItem | null;
};

export type DepartmentIddQuery = {
  departmentId: string;
  competence?: string;
  startDate?: string;
  endDate?: string;
  branch?: string;
  signal?: AbortSignal;
};

function buildDepartmentIddQuery(params: DepartmentIddQuery): string {
  const searchParams = new URLSearchParams();
  searchParams.set("department_id", params.departmentId);
  if (params.competence) searchParams.set("competence", params.competence);
  if (params.startDate) searchParams.set("start_date", params.startDate);
  if (params.endDate) searchParams.set("end_date", params.endDate);
  if (params.branch) searchParams.set("branch", params.branch);
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function fetchDepartmentIdd(
  params: DepartmentIddQuery
): Promise<DepartmentIddItem | null> {
  const response = await httpGet<ApiSuccessResponse<DepartmentIddResponse>>(
    `${DEPARTMENT_IDD_API_BASE}/department-idd${buildDepartmentIddQuery(params)}`,
    { signal: params.signal }
  );

  const data = unwrapApiDelpiEnvelope(response, "Erro ao consultar IDD departamental");
  return data.item ?? null;
}

export type DepartmentIndicatorScoreItem = {
  indicator_id?: string | null;
  score?: number | null;
  name?: string | null;
};

export type DepartmentIndicatorsItem = {
  department_id: string;
  department_name?: string | null;
  score?: number | null;
  idd?: number | null;
  classification?: string | null;
  indicators?: DepartmentIndicatorScoreItem[] | null;
  partial_success?: boolean;
};

type DepartmentIndicatorsResponse = {
  item: DepartmentIndicatorsItem | null;
};

export async function fetchDepartmentIndicators(
  params: DepartmentIddQuery
): Promise<DepartmentIndicatorsItem | null> {
  const response = await httpGet<ApiSuccessResponse<DepartmentIndicatorsResponse>>(
    `${DEPARTMENT_IDD_API_BASE}/department-indicators${buildDepartmentIddQuery(params)}`,
    { signal: params.signal }
  );

  const data = unwrapApiDelpiEnvelope(
    response,
    "Erro ao consultar indicadores departamentais"
  );
  return data.item ?? null;
}
