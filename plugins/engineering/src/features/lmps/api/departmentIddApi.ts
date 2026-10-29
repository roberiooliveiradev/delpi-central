import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/lmp";

export const DEPARTMENT_IDD_API_BASE = "/apps/engineering-api/v1/lmps";

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
  status?: string;
  item?: DepartmentIddItem | null;
  data?: { item?: DepartmentIddItem | null } | DepartmentIddItem;
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
  if (data.status === "forbidden") {
    throw new Error("Nota IDD indisponível para este usuário (owner Strategic Indicators).");
  }
  const inner = data.data as DepartmentIddResponse | DepartmentIddItem | undefined;
  const item =
    inner && typeof inner === "object" && "item" in inner
      ? (inner as DepartmentIddResponse).item
      : (inner as DepartmentIddItem | undefined);
  return item ?? data.item ?? null;
}
