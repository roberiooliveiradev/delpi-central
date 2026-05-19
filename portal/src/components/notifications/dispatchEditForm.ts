// src/components/notifications/dispatchEditForm.ts

import type {
  NotificationActionType,
  NotificationCategory,
  NotificationPresentation,
  NotificationTemplateId,
  NotificationType,
} from "../../data/coreApi";

export type DispatchPayloadRecord = Record<string, unknown>;

export type DispatchFormSnapshot = {
  broadcast: boolean;
  selectedUserIds: string[];
  selectedRoleIds: string[];
  selectedGroupIds: string[];
  excludedRoleGroupUserIds: string[];
  extraEmails: string[];
  title: string;
  message: string;
  type: NotificationType;
  category: NotificationCategory;
  presentation: NotificationPresentation;
  htmlContent: string;
  templateId: NotificationTemplateId;
  templateVars: Record<string, string>;
  actionType: NotificationActionType | "none";
  actionLabel: string;
  actionTarget: string;
  expiresEnabled: boolean;
  expiresInDays: number;
  scheduleEnabled: boolean;
  scheduledAtLocal: string;
};

function toDatetimeLocalValue(date: Date): string {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function parseExpiresInDays(expiresAt: string | null | undefined): {
  enabled: boolean;
  days: number;
} {
  if (!expiresAt) {
    return { enabled: false, days: 7 };
  }
  const target = new Date(expiresAt).getTime();
  const diffMs = target - Date.now();
  const days = Math.max(1, Math.round(diffMs / (24 * 60 * 60 * 1000)));
  return { enabled: true, days };
}

export function snapshotFromDispatchPayload(
  payload: DispatchPayloadRecord,
  scheduledAt?: string | null,
): DispatchFormSnapshot {
  const metadata = (payload.metadata as Record<string, unknown> | undefined) ?? {};
  const templateId = (metadata.templateId ?? metadata.template_id ?? payload.templateId) as
    | NotificationTemplateId
    | undefined;
  const templateVars = (metadata.vars as Record<string, string> | undefined) ?? {};
  const presentation = (payload.presentation as NotificationPresentation) || "text";
  const actionType = (payload.actionType ?? payload.action_type) as
    | NotificationActionType
    | undefined;
  const expires = parseExpiresInDays(
    (payload.expiresAt as string | undefined) ?? (payload.expires_at as string | undefined),
  );

  return {
    broadcast: Boolean(payload.broadcast),
    selectedUserIds: (payload.userIds as string[] | undefined) ?? [],
    selectedRoleIds: (payload.roleIds as string[] | undefined) ?? [],
    selectedGroupIds: (payload.groupIds as string[] | undefined) ?? [],
    excludedRoleGroupUserIds:
      (payload.excludedUserIds as string[] | undefined) ?? [],
    extraEmails: (payload.emails as string[] | undefined) ?? [],
    title: (payload.title as string | undefined) ?? "",
    message: (payload.message as string | undefined) ?? "",
    type: (payload.type as NotificationType) || "info",
    category: (payload.category as NotificationCategory) || "announcement",
    presentation,
    htmlContent: (payload.htmlContent as string | undefined) ?? "",
    templateId: templateId ?? "welcome_v1",
    templateVars,
    actionType: actionType ?? "none",
    actionLabel: (payload.actionLabel as string | undefined) ?? "",
    actionTarget: (payload.actionTarget as string | undefined) ?? "",
    expiresEnabled: expires.enabled,
    expiresInDays: expires.days,
    scheduleEnabled: Boolean(scheduledAt),
    scheduledAtLocal: scheduledAt ? toDatetimeLocalValue(new Date(scheduledAt)) : "",
  };
}

export function isEditableScheduledDispatch(
  status: string,
  scheduledAt?: string | null,
): boolean {
  if (status !== "pending" || !scheduledAt) {
    return false;
  }
  return new Date(scheduledAt).getTime() > Date.now() - 30_000;
}
