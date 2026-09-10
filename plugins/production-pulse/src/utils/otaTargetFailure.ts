import { PP_HELP } from "../content/helpTooltips";

export type OtaTargetFailureResolved = {
  title: string;
  message: string;
  technicalCode: string | null;
  variant: "error" | "warning";
};

/** Real ESP / API target error codes (not ContentCoded HTTP codes). */
const FAILURE_CATALOG: Record<string, { title: string; message: string; variant?: "error" | "warning" }> =
  {
    ota_target_stale: {
      title: PP_HELP.ota.updateInterruptedTitle,
      message: PP_HELP.ota.failureMessages.ota_target_stale,
      variant: "warning",
    },
    ota_failed: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.ota_failed,
    },
    flash_error: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.flash_error,
    },
    http_begin_failed: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.download,
    },
    missing_content_length: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.download,
    },
    download_stream_null: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.download,
    },
    download_incomplete: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.download,
    },
    missing_artifact_token: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.download,
    },
    update_begin_failed: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.flash_error,
    },
    update_write_failed: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.flash_error,
    },
    update_end_failed: {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.flash_error,
    },
  };

function resolveDownloadHttpCode(code: string): OtaTargetFailureResolved | null {
  if (!code.startsWith("download_http_")) return null;
  return {
    title: PP_HELP.ota.updateFailedTitle,
    message: PP_HELP.ota.failureMessages.download,
    technicalCode: code,
    variant: "error",
  };
}

export function resolveOtaTargetFailure(
  errorCode: string | null | undefined,
): OtaTargetFailureResolved {
  const code = (errorCode || "").trim();
  if (!code) {
    return {
      title: PP_HELP.ota.updateFailedTitle,
      message: PP_HELP.ota.failureMessages.ota_failed,
      technicalCode: null,
      variant: "error",
    };
  }
  const http = resolveDownloadHttpCode(code);
  if (http) return http;
  const entry = FAILURE_CATALOG[code];
  if (entry) {
    return {
      title: entry.title,
      message: entry.message,
      technicalCode: code,
      variant: entry.variant ?? "error",
    };
  }
  return {
    title: PP_HELP.ota.updateFailedTitle,
    message: PP_HELP.ota.failureMessages.generic,
    technicalCode: code,
    variant: "error",
  };
}
