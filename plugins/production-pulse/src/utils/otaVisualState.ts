import type { LucideIcon } from "lucide-react";
import {
  Ban,
  Bell,
  BellOff,
  CircleCheck,
  CircleX,
  Clock3,
  Download,
  LoaderCircle,
  Megaphone,
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

export type OtaWakeStatus = "pending" | "accepted" | "failed" | string | null | undefined;

function resolveAwaitingWakeState(input: {
  status: string;
  wakeStatus?: OtaWakeStatus;
  online: boolean;
}): OtaVisualState | null {
  if (input.status !== "pending" && input.status !== "authorized") {
    return null;
  }
  if (!input.online) {
    return {
      phase: input.status,
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

  const wake = (input.wakeStatus || "").trim().toLowerCase();
  if (input.status === "authorized" && wake === "pending") {
    return {
      phase: "wake_pending",
      label: PP_HELP.ota.phase.wakePending,
      description: PP_HELP.ota.phase.wakePendingHint,
      icon: Megaphone,
      tone: "info",
      progressMode: "indeterminate",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }
  if (input.status === "authorized" && wake === "accepted") {
    return {
      phase: "wake_accepted",
      label: PP_HELP.ota.phase.wakeAccepted,
      description: PP_HELP.ota.phase.wakeAcceptedHint,
      icon: Bell,
      tone: "info",
      progressMode: "none",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }
  if (input.status === "authorized" && wake === "failed") {
    return {
      phase: "wake_failed",
      label: PP_HELP.ota.phase.wakeFailed,
      description: PP_HELP.ota.phase.wakeFailedHint,
      icon: BellOff,
      tone: "warning",
      progressMode: "none",
      progressPercent: null,
      bytesLabel: null,
      technicalCode: null,
    };
  }

  return {
    phase: input.status,
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

export function resolveOtaVisualState(input: {
  status?: string | null;
  errorCode?: string | null;
  deviceOnline?: boolean | null;
  progressPercent?: number | null;
  bytesReceived?: number | null;
  bytesTotal?: number | null;
  wakeStatus?: OtaWakeStatus;
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

  const awaiting = resolveAwaitingWakeState({
    status,
    wakeStatus: input.wakeStatus,
    online,
  });
  if (awaiting) {
    return awaiting;
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
