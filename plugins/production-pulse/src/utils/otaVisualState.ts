import type { LucideIcon } from "lucide-react";
import {
  Ban,
  CircleCheck,
  CircleX,
  Clock3,
  Download,
  LoaderCircle,
  TriangleAlert,
  WifiOff,
} from "lucide-react";

import { PP_HELP } from "../content/helpTooltips";
import { resolveOtaTargetFailure } from "./otaTargetFailure";
import {
  formatOtaBytes,
  resolveOtaProgressMode,
  resolveOtaProgressPercent,
  type OtaProgressMode,
} from "./otaStatusLabels";

export type OtaVisualTone = "muted" | "info" | "accent" | "success" | "warning" | "danger";

export type OtaVisualState = {
  phase: string;
  label: string;
  description: string;
  icon: LucideIcon;
  tone: OtaVisualTone;
  progressMode: OtaProgressMode;
  progressPercent: number | null;
  bytesLabel: string | null;
  technicalCode: string | null;
};

export function resolveOtaVisualState(input: {
  status?: string | null;
  errorCode?: string | null;
  deviceOnline?: boolean | null;
  progressPercent?: number | null;
  bytesReceived?: number | null;
  bytesTotal?: number | null;
}): OtaVisualState {
  const status = (input.status || "").trim().toLowerCase();
  const online = input.deviceOnline !== false;
  const progressMode = resolveOtaProgressMode({
    status,
    progressPercent: input.progressPercent,
  });
  const progressPercent = resolveOtaProgressPercent({
    status,
    progressPercent: input.progressPercent,
  });
  const bytesLabel = formatOtaBytes(input.bytesReceived, input.bytesTotal);

  if (status === "pending" || status === "authorized") {
    if (!online) {
      return {
        phase: status,
        label: PP_HELP.ota.phase.awaitingOffline,
        description: PP_HELP.ota.phase.awaitingOfflineHint,
        icon: WifiOff,
        tone: "warning",
        progressMode: "none",
        progressPercent: null,
        bytesLabel: null,
        technicalCode: null,
      };
    }
    return {
      phase: status,
      label: PP_HELP.ota.phase.awaiting,
      description: PP_HELP.ota.phase.awaitingHint,
      icon: Clock3,
      tone: "info",
      progressMode: "none",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }

  if (status === "downloading") {
    return {
      phase: status,
      label:
        progressPercent != null
          ? `${PP_HELP.ota.phase.downloading} · ${progressPercent}%`
          : PP_HELP.ota.phase.downloading,
      description: PP_HELP.ota.operation.downloading,
      icon: Download,
      tone: "accent",
      progressMode,
      progressPercent,
      bytesLabel,
      technicalCode: null,
    };
  }

  if (status === "applying") {
    return {
      phase: status,
      label: PP_HELP.ota.phase.applying,
      description: PP_HELP.ota.operation.applying,
      icon: LoaderCircle,
      tone: "accent",
      progressMode: "indeterminate",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }

  if (status === "updated") {
    return {
      phase: status,
      label: PP_HELP.ota.phase.updated,
      description: PP_HELP.ota.operation.updated,
      icon: CircleCheck,
      tone: "success",
      progressMode: "none",
      progressPercent: 100,
      bytesLabel: null,
      technicalCode: null,
    };
  }

  if (status === "failed") {
    const failure = resolveOtaTargetFailure(input.errorCode);
    const stale = (input.errorCode || "").trim() === "ota_target_stale";
    return {
      phase: status,
      label: stale ? PP_HELP.ota.phase.interrupted : PP_HELP.ota.phase.failed,
      description: failure.message,
      icon: stale ? TriangleAlert : CircleX,
      tone: stale ? "warning" : "danger",
      progressMode: "none",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: failure.technicalCode,
    };
  }

  if (status === "cancelled") {
    return {
      phase: status,
      label: PP_HELP.ota.phase.cancelled,
      description: PP_HELP.ota.status.cancelled,
      icon: Ban,
      tone: "muted",
      progressMode: "none",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }

  if (status === "skipped") {
    return {
      phase: status,
      label: PP_HELP.ota.status.skipped,
      description: PP_HELP.ota.status.skipped,
      icon: Ban,
      tone: "muted",
      progressMode: "none",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }

  return {
    phase: status || "idle",
    label: PP_HELP.ota.operation.idle,
    description: PP_HELP.ota.operation.idle,
    icon: Clock3,
    tone: "muted",
    progressMode: "none",
    progressPercent: null,
    bytesLabel: null,
    technicalCode: null,
  };
}
