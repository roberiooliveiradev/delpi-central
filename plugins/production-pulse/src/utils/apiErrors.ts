import { ProductionPulseRequestError } from "../api/httpClient";
import { DEVICE_CONNECTIVITY_ERROR_CODES } from "../content/deviceApiMessages";
import { PP_HELP } from "../content/helpTooltips";

const DEVICE_CONNECTIVITY_CODE_SET = new Set<string>(DEVICE_CONNECTIVITY_ERROR_CODES);

export type ResolvedActionError =
  | { kind: "device"; message: string }
  | { kind: "infra"; message: string }
  | { kind: "unknown"; message: string };

export type ProductionPulseErrorVariant = "error" | "warning" | "info" | "success";

export type ResolvedProductionPulseError = {
  /** Surface hint: field = inline form; notice = floating; structural = StateBox. */
  surface: "field" | "notice" | "structural";
  variant: ProductionPulseErrorVariant;
  title: string;
  message: string;
  code?: string;
  actionLabel?: string;
};

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

export function isApiUnavailableError(err: unknown): boolean {
  if (!(err instanceof ProductionPulseRequestError)) return false;
  if (isDeviceConnectivityErrorCode(err.code) && (err.status === 422 || err.status === 502)) {
    return false;
  }
  return err.status === 502 || err.status === 503;
}

export function resolveDeviceConnectivityMessage(code: string, fallback: string): string {
  return code.trim() || fallback;
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

export function resolveProbeErrorMessage(
  result: { error?: string; errorMessage?: string },
  fallback: string,
): string {
  if (result.errorMessage?.trim()) return result.errorMessage.trim();
  if (result.error) return resolveDeviceConnectivityMessage(result.error, fallback);
  return fallback;
}

export function resolveDeviceActionMessage(err: unknown, fallback: string): string {
  return resolveDeviceActionError(err, fallback).message;
}

type ResolveContext = {
  fallbackMessage?: string;
  /** Prefer notice for operational actions (default). */
  surface?: "field" | "notice" | "structural";
};

const OTA_CODE_TITLES: Record<string, { title: string; variant?: ProductionPulseErrorVariant }> = {
  openTargetExists: {
    title: PP_HELP.ota.alreadyInProgressTitle,
    variant: "warning",
  },
  noEligibleDevices: {
    title: PP_HELP.ota.noEligibleTitle,
    variant: "warning",
  },
  ota_target_stale: {
    title: PP_HELP.ota.updateInterruptedTitle,
    variant: "warning",
  },
  firmwareLinkIncompatible: {
    title: "Vínculo incompatível",
    variant: "error",
  },
  jobCannotCancel: {
    title: "Não foi possível cancelar",
    variant: "error",
  },
};

/**
 * Canonical operational error resolver for Production Pulse MFE.
 * Prefer `ProductionPulseRequestError.code` over string parsing.
 */
export function resolveProductionPulseError(
  err: unknown,
  context: ResolveContext = {},
): ResolvedProductionPulseError {
  const surface = context.surface ?? "notice";
  const fallback = context.fallbackMessage ?? PP_HELP.ota.deviceJobFailed;

  if (err instanceof ProductionPulseRequestError) {
    const code = err.code;
    if (code && OTA_CODE_TITLES[code]) {
      const meta = OTA_CODE_TITLES[code];
      return {
        surface,
        variant: meta.variant ?? "error",
        title: meta.title,
        message:
          code === "openTargetExists"
            ? PP_HELP.ota.alreadyInProgressMessage
            : code === "ota_target_stale"
              ? PP_HELP.ota.updateInterruptedMessage
              : err.message || fallback,
        code,
        actionLabel:
          code === "openTargetExists" ? PP_HELP.ota.alreadyInProgressAction : undefined,
      };
    }
    if (isApiUnavailableError(err)) {
      return {
        surface: "structural",
        variant: "error",
        title: "API indisponível",
        message: err.message || PP_HELP.apiErrors.apiUnavailable,
        code,
      };
    }
    return {
      surface,
      variant: "error",
      title: PP_HELP.ota.updateFailedTitle,
      message: err.message || fallback,
      code,
    };
  }

  return {
    surface,
    variant: "error",
    title: PP_HELP.ota.updateFailedTitle,
    message: err instanceof Error ? err.message : fallback,
  };
}

/** True when the same operational event must not also paint a structural StateBox. */
export function isOperationalNoticeOnly(resolved: ResolvedProductionPulseError): boolean {
  return resolved.surface === "notice" || resolved.surface === "field";
}
