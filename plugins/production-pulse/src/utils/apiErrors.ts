import { ProductionPulseRequestError } from "../api/httpClient";
import { DEVICE_CONNECTIVITY_ERROR_CODES } from "../content/deviceApiMessages";

const DEVICE_CONNECTIVITY_CODE_SET = new Set<string>(DEVICE_CONNECTIVITY_ERROR_CODES);

export type ResolvedActionError =
  | { kind: "device"; message: string }
  | { kind: "infra"; message: string }
  | { kind: "unknown"; message: string };

export function isDeviceConnectivityErrorCode(code: string | undefined): boolean {
  return !!code && DEVICE_CONNECTIVITY_CODE_SET.has(code);
}

export function isDeviceConnectivityError(err: unknown): err is ProductionPulseRequestError {
  if (!(err instanceof ProductionPulseRequestError)) return false;
  if (!isDeviceConnectivityErrorCode(err.code)) return false;
  if (err.status === 422) return true;
  // Compatibilidade com API antiga que ainda devolvia 502 com JSON estruturado.
  return err.status === 502;
}

export function isApiUnavailableError(err: unknown): err is ProductionPulseRequestError {
  if (!(err instanceof ProductionPulseRequestError)) return false;
  if (isDeviceConnectivityError(err)) return false;
  return err.status === 502 || err.status === 503;
}

export function resolveDeviceActionError(err: unknown, fallback: string): ResolvedActionError {
  if (err instanceof ProductionPulseRequestError) {
    if (isDeviceConnectivityError(err)) {
      return { kind: "device", message: err.message };
    }
    if (isApiUnavailableError(err)) {
      return { kind: "infra", message: err.message };
    }
    return { kind: "unknown", message: err.message };
  }
  return {
    kind: "unknown",
    message: err instanceof Error ? err.message : fallback,
  };
}

export function resolveDeviceActionMessage(err: unknown, fallback: string): string {
  return resolveDeviceActionError(err, fallback).message;
}
