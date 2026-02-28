// src/utils/pinnedApps.ts
export const PINNED_KEY = "delpi.portal.pinnedApps.v1";
export const PINNED_EVENT = "delpi:pinned-apps-changed";

export function getPinnedIds(): string[] {
  try {
    const raw = localStorage.getItem(PINNED_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed)
      ? parsed.filter((x) => typeof x === "string")
      : [];
  } catch {
    return [];
  }
}

export function setPinnedIds(ids: string[]) {
  localStorage.setItem(PINNED_KEY, JSON.stringify(ids));
  window.dispatchEvent(new Event(PINNED_EVENT));
}

export function togglePinnedId(appId: string) {
  const current = getPinnedIds();
  const exists = current.includes(appId);
  const next = exists ? current.filter((x) => x !== appId) : [appId, ...current];
  setPinnedIds(next);
  return next;
}