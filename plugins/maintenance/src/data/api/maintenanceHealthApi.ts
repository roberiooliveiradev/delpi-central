import { MAINTENANCE_API_BASE, buildAuthHeaders } from "./maintenanceApiBase";

export type ModuleHealthResponse = {
  status: string;
  module?: string;
  phase?: string;
  db_ready?: boolean;
  db_hint?: string | null;
};

export async function fetchModuleHealthRaw(
  getAccessToken?: () => string | undefined,
): Promise<ModuleHealthResponse> {
  const response = await fetch(`${MAINTENANCE_API_BASE}/health`, {
    headers: buildAuthHeaders(getAccessToken),
  });

  if (!response.ok) {
    throw new Error(`Health check falhou (${response.status})`);
  }

  return response.json() as Promise<ModuleHealthResponse>;
}
