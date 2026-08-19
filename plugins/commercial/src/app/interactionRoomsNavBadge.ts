/**
 * Badge da TopBar «Sala de interação»: soma de `unread_count` da inbox.
 */

export function sumInboxUnreadCount(
  items: ReadonlyArray<{ unread_count?: number | null }> | null | undefined,
): number {
  if (!items?.length) return 0;
  return items.reduce((sum, item) => {
    const raw = item.unread_count;
    if (typeof raw !== "number" || !Number.isFinite(raw)) return sum;
    return sum + Math.max(0, Math.trunc(raw));
  }, 0);
}
