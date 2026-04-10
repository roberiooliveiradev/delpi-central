import type {
  AdminDepartmentIndicatorsListResponse,
  AdminDepartmentsListResponse,
  CreateAdminDepartmentIndicatorRequest,
  CreateAdminDepartmentRequest,
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
  UpdateAdminDepartmentIndicatorRequest,
  UpdateAdminDepartmentRequest,
} from "../types/settings";

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type GetToken = (() => string | undefined) | undefined;

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function fetchStrategicIndicatorsSettings(
  getAccessToken?: GetToken,
  signal?: AbortSignal,
): Promise<StrategicIndicatorsSettingsResponse> {
  const response = await fetch(`${BASE_URL}/settings`, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
    signal,
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao carregar configurações do módulo.");
  }

  return response.json();
}

export async function updateStrategicIndicatorsSettings(
  payload: StrategicIndicatorsSettingsUpdateRequest,
  getAccessToken?: GetToken,
): Promise<{ message: string }> {
  const response = await fetch(`${BASE_URL}/settings`, {
    method: "PUT",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao salvar configurações globais do módulo.");
  }

  return response.json();
}

export async function fetchAdminDepartments(
  getAccessToken?: GetToken,
  signal?: AbortSignal,
): Promise<AdminDepartmentsListResponse> {
  const response = await fetch(`${BASE_URL}/admin/departments`, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
    signal,
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao carregar departamentos administrativos.");
  }

  return response.json();
}

export async function createAdminDepartment(
  payload: CreateAdminDepartmentRequest,
  getAccessToken?: GetToken,
): Promise<{ department_id: string }> {
  const response = await fetch(`${BASE_URL}/admin/departments`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao criar departamento.");
  }

  return response.json();
}

export async function updateAdminDepartment(
  departmentId: string,
  payload: UpdateAdminDepartmentRequest,
  getAccessToken?: GetToken,
): Promise<{ department_id: string }> {
  const response = await fetch(`${BASE_URL}/admin/departments/${departmentId}`, {
    method: "PUT",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao atualizar departamento.");
  }

  return response.json();
}

export async function deactivateAdminDepartment(
  departmentId: string,
  getAccessToken?: GetToken,
): Promise<{ department_id: string }> {
  const response = await fetch(
    `${BASE_URL}/admin/departments/${departmentId}/deactivate`,
    {
      method: "POST",
      headers: buildHeaders(getAccessToken),
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao desativar departamento.");
  }

  return response.json();
}

export async function deleteAdminDepartment(
  departmentId: string,
  getAccessToken?: GetToken,
): Promise<{ message: string; department_id: string }> {
  const response = await fetch(`${BASE_URL}/admin/departments/${departmentId}`, {
    method: "DELETE",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao excluir departamento.");
  }

  return response.json();
}

export async function fetchAdminDepartmentIndicators(
  departmentId: string,
  getAccessToken?: GetToken,
  signal?: AbortSignal,
): Promise<AdminDepartmentIndicatorsListResponse> {
  const response = await fetch(
    `${BASE_URL}/admin/departments/${departmentId}/indicators`,
    {
      method: "GET",
      headers: buildHeaders(getAccessToken),
      signal,
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(
      message || "Falha ao carregar indicadores estruturais do departamento.",
    );
  }

  return response.json();
}

export async function createAdminDepartmentIndicator(
  departmentId: string,
  payload: CreateAdminDepartmentIndicatorRequest,
  getAccessToken?: GetToken,
): Promise<{ indicator_id: string }> {
  const response = await fetch(
    `${BASE_URL}/admin/departments/${departmentId}/indicators`,
    {
      method: "POST",
      headers: buildHeaders(getAccessToken),
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao criar indicador estrutural.");
  }

  return response.json();
}

export async function updateAdminDepartmentIndicator(
  indicatorId: string,
  payload: UpdateAdminDepartmentIndicatorRequest,
  getAccessToken?: GetToken,
): Promise<{ indicator_id: string }> {
  const response = await fetch(`${BASE_URL}/admin/indicators/${indicatorId}`, {
    method: "PUT",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao atualizar indicador estrutural.");
  }

  return response.json();
}

export async function deactivateAdminDepartmentIndicator(
  indicatorId: string,
  getAccessToken?: GetToken,
): Promise<{ indicator_id: string }> {
  const response = await fetch(
    `${BASE_URL}/admin/indicators/${indicatorId}/deactivate`,
    {
      method: "POST",
      headers: buildHeaders(getAccessToken),
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao desativar indicador estrutural.");
  }

  return response.json();
}

export async function deleteAdminDepartmentIndicator(
  indicatorId: string,
  getAccessToken?: GetToken,
): Promise<{ message: string; indicator_id: string }> {
  const response = await fetch(`${BASE_URL}/admin/indicators/${indicatorId}`, {
    method: "DELETE",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao excluir indicador estrutural.");
  }

  return response.json();
}

async function safeReadError(response: Response): Promise<string | null> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.message === "string") return data.message;
    return null;
  } catch {
    return null;
  }
}