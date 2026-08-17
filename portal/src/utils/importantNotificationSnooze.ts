/** Overlay snooze for important notification attention (session-scoped). */

export const IMPORTANT_NOTIFICATION_SNOOZE_MS = 15 * 60 * 1000;
export const IMPORTANT_NOTIFICATION_SNOOZE_KEY = "delpi.importantNotificationSnoozeUntil";
export const IMPORTANT_NOTIFICATION_SNOOZE_IDS_KEY = "delpi.importantNotificationSnoozeKnownIds";

export function readImportantNotificationSnoozeUntil(now = Date.now()): number | null {
  try {
    const raw = sessionStorage.getItem(IMPORTANT_NOTIFICATION_SNOOZE_KEY);
    if (!raw) return null;
    const until = Number(raw);
    if (!Number.isFinite(until) || until <= now) {
      clearImportantNotificationSnooze();
      return null;
    }
    return until;
  } catch {
    return null;
  }
}

export function readImportantNotificationSnoozeKnownIds(): string[] {
  try {
    const raw = sessionStorage.getItem(IMPORTANT_NOTIFICATION_SNOOZE_IDS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === "string");
  } catch {
    return [];
  }
}

export function isImportantNotificationSnoozed(now = Date.now()): boolean {
  return readImportantNotificationSnoozeUntil(now) != null;
}

/**
 * Returns true when snooze should end early because a new important unread appeared.
 */
export function shouldBreakImportantNotificationSnooze(
  importantUnreadIds: string[],
  now = Date.now(),
): boolean {
  if (!isImportantNotificationSnoozed(now)) return false;
  const known = new Set(readImportantNotificationSnoozeKnownIds());
  return importantUnreadIds.some((id) => !known.has(id));
}

export function snoozeImportantNotificationOverlay(
  knownImportantUnreadIds: string[] = [],
  durationMs = IMPORTANT_NOTIFICATION_SNOOZE_MS,
  now = Date.now(),
): number {
  const until = now + durationMs;
  try {
    sessionStorage.setItem(IMPORTANT_NOTIFICATION_SNOOZE_KEY, String(until));
    sessionStorage.setItem(
      IMPORTANT_NOTIFICATION_SNOOZE_IDS_KEY,
      JSON.stringify([...new Set(knownImportantUnreadIds)]),
    );
  } catch {
    /* private mode / quota — still return until for in-memory consumers */
  }
  return until;
}

export function clearImportantNotificationSnooze(): void {
  try {
    sessionStorage.removeItem(IMPORTANT_NOTIFICATION_SNOOZE_KEY);
    sessionStorage.removeItem(IMPORTANT_NOTIFICATION_SNOOZE_IDS_KEY);
  } catch {
    /* ignore */
  }
}
