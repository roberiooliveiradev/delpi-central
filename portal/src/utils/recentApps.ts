// src/utils/recentApps.ts

const RECENT_KEY = "delpi.portal.recentApps.v1";
const MAX_ITEMS = 5;

export function getRecentAppIds(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  } 
}

export function pushRecentApp(appId: string) {
  const current = getRecentAppIds();
  const next = [appId, ...current.filter((id) => id !== appId)].slice(
    0,
    MAX_ITEMS
  );
  localStorage.setItem(RECENT_KEY, JSON.stringify(next));
}