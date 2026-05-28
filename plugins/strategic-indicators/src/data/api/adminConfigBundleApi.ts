import type {
  AdminConfigBundle,
  AdminConfigImportResponse,
} from "../types/adminConfigBundle";
import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

function buildHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function safeReadError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") return payload.detail;
    if (Array.isArray(payload?.detail)) {
      return payload.detail.map((item: { msg?: string }) => item.msg).join("; ");
    }
    return payload?.message ?? "";
  } catch {
    return "";
  }
}

export async function exportAdminConfigBundle(
  getAccessToken?: GetToken,
): Promise<AdminConfigBundle> {
  const response = await fetch(`${BASE_URL}/admin/config/export`, {
    method: "GET",
    headers: buildHeaders(getAccessToken),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao exportar configuração do módulo.");
  }

  return response.json();
}

export async function importAdminConfigBundle(
  bundle: AdminConfigBundle & { include_goals?: boolean },
  getAccessToken?: GetToken,
): Promise<AdminConfigImportResponse> {
  const response = await fetch(`${BASE_URL}/admin/config/import`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(bundle),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao importar configuração do módulo.");
  }

  return response.json();
}
