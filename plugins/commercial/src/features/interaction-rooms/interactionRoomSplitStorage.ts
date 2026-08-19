export const INBOX_WIDTH_STORAGE_KEY = "commercial.interactionRoom.inboxWidthPx";
export const INBOX_COLLAPSED_STORAGE_KEY =
  "commercial.interactionRoom.inboxCollapsed";

export function readInboxWidthPx(): number | undefined {
  if (typeof window === "undefined") return undefined;
  const raw = window.localStorage.getItem(INBOX_WIDTH_STORAGE_KEY);
  const value = Number(raw);
  return Number.isFinite(value) && value > 0 ? value : undefined;
}

export function writeInboxWidthPx(widthPx: number): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(INBOX_WIDTH_STORAGE_KEY, String(Math.round(widthPx)));
}

export function readInboxCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(INBOX_COLLAPSED_STORAGE_KEY) === "1";
}

export function writeInboxCollapsed(collapsed: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(INBOX_COLLAPSED_STORAGE_KEY, collapsed ? "1" : "0");
}
