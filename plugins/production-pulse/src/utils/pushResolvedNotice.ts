import {
  isOperationalNoticeOnly,
  resolveProductionPulseError,
  type ProductionPulseErrorVariant,
  type ResolvedProductionPulseError,
} from "./apiErrors";
import { resolveOtaTargetFailure } from "./otaTargetFailure";

type NoticeInput = {
  id?: string;
  variant?: ProductionPulseErrorVariant;
  title?: string;
  message: string;
  action?: { label: string; onClick: () => void };
};

type PushFn = (notice: NoticeInput | string) => string;


export type PushResolvedNoticeOptions = {
  /** Deterministic id for semantic dedupe (upsert). */
  id?: string;
  /** Open job/target panel or similar. */
  onAction?: () => void;
};

/**
 * Single entry for operational OTA/request feedback → PpFloatingNotices.
 * Structural surfaces must be handled by the caller (StateBox), not here.
 */
export function pushResolvedProductionPulseNotice(
  push: PushFn,
  errOrResolved: unknown | ResolvedProductionPulseError,
  options: PushResolvedNoticeOptions = {},
): ResolvedProductionPulseError | null {
  const resolved =
    errOrResolved &&
    typeof errOrResolved === "object" &&
    "surface" in errOrResolved &&
    "title" in errOrResolved &&
    "message" in errOrResolved
      ? (errOrResolved as ResolvedProductionPulseError)
      : resolveProductionPulseError(errOrResolved);

  if (!isOperationalNoticeOnly(resolved)) {
    return resolved;
  }

  const actionLabel = resolved.actionLabel;
  push({
    id: options.id,
    variant: resolved.variant,
    title: resolved.title,
    message: resolved.message,
    action:
      actionLabel && options.onAction
        ? { label: actionLabel, onClick: options.onAction }
        : undefined,
  });
  return resolved;
}

export function otaActiveNoticeId(deviceId: string): string {
  return `ota-target-active:${deviceId}`;
}

export function otaJobCreatedNoticeId(jobId: string): string {
  return `ota-job-created:${jobId}`;
}

export function otaTargetFailedNoticeId(targetId: string): string {
  return `ota-target-failed:${targetId}`;
}

export function otaTargetUpdatedNoticeId(targetId: string): string {
  return `ota-target-updated:${targetId}`;
}

export function pushOtaTargetFailureNotice(
  push: PushFn,
  input: { targetId: string; errorCode?: string | null; deviceName?: string },
): void {
  const failure = resolveOtaTargetFailure(input.errorCode);
  push({
    id: otaTargetFailedNoticeId(input.targetId),
    variant: failure.variant,
    title: failure.title,
    message: input.deviceName
      ? `${input.deviceName}: ${failure.message}`
      : failure.message,
  });
}
