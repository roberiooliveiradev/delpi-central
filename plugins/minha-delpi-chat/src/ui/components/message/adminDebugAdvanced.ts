/**
 * Modo avançado do diagnóstico admin na bolha (JSON bruto).
 * Persistência local — não via query (evita poluir deep links da conversa).
 */

export const ADMIN_DEBUG_ADVANCED_STORAGE_KEY = "mdcAdminDebugAdvanced";

export function readAdminDebugAdvanced(
  storage: Pick<Storage, "getItem"> | null | undefined = typeof window !== "undefined"
    ? window.localStorage
    : null,
): boolean {
  if (!storage) {
    return false;
  }
  return storage.getItem(ADMIN_DEBUG_ADVANCED_STORAGE_KEY) === "1";
}

export function writeAdminDebugAdvanced(
  enabled: boolean,
  storage: Pick<Storage, "setItem"> | null | undefined = typeof window !== "undefined"
    ? window.localStorage
    : null,
): void {
  if (!storage) {
    return;
  }
  storage.setItem(ADMIN_DEBUG_ADVANCED_STORAGE_KEY, enabled ? "1" : "0");
}

export function shouldShowRawDebugJson(advanced: boolean): boolean {
  return advanced === true;
}

/** Extrai traceId do payload adminDebug quando presente. */
export function extractAdminDebugTraceId(
  debug: Record<string, unknown> | null | undefined,
): string | null {
  if (!debug || typeof debug !== "object") {
    return null;
  }

  for (const key of ["traceId", "trace_id", "requestId", "request_id"] as const) {
    const value = debug[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return null;
}
