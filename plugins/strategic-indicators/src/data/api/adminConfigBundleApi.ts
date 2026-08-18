import { triggerBlobDownload } from "@delpi/plugin-ui/index";
import type {
  AdminConfigBundle,
  AdminConfigImportMode,
  AdminConfigImportResponse,
  AdminConfigPreviewResponse,
} from "../types/adminConfigBundle";
import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

type GetToken = (() => string | undefined) | undefined;

export type AdminConfigImportOptions = {
  mode: AdminConfigImportMode;
  includeGoals?: boolean;
};

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

function toRequestBody(
  bundle: AdminConfigBundle,
  options: AdminConfigImportOptions,
): Record<string, unknown> {
  return {
    ...bundle,
    mode: options.mode,
    include_goals: options.includeGoals ?? true,
  };
}

export function downloadAdminConfigBundleJson(
  bundle: AdminConfigBundle,
  fileName: string,
): void {
  const blob = new Blob([JSON.stringify(bundle, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  triggerBlobDownload(blob, fileName);
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

export async function previewAdminConfigBundle(
  bundle: AdminConfigBundle,
  options: AdminConfigImportOptions,
  getAccessToken?: GetToken,
): Promise<AdminConfigPreviewResponse> {
  const response = await fetch(`${BASE_URL}/admin/config/import/preview`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(toRequestBody(bundle, options)),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao pré-visualizar configuração do módulo.");
  }

  return response.json();
}

export async function applyAdminConfigBundle(
  bundle: AdminConfigBundle,
  options: AdminConfigImportOptions,
  getAccessToken?: GetToken,
): Promise<AdminConfigImportResponse> {
  const response = await fetch(`${BASE_URL}/admin/config/import/apply`, {
    method: "POST",
    headers: buildHeaders(getAccessToken),
    body: JSON.stringify(toRequestBody(bundle, options)),
  });

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(message || "Falha ao importar configuração do módulo.");
  }

  return response.json();
}
