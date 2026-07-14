/** Preferência persistente: top bar (abas + ribbon) recolhida. */

const STORAGE_COLLAPSED_KEY = "td-deck-chrome-collapsed";

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function readDeckChromeCollapsed(): boolean {
  if (!canUseStorage()) return false;
  try {
    return window.localStorage.getItem(STORAGE_COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
}

export function writeDeckChromeCollapsed(collapsed: boolean): void {
  if (!canUseStorage()) return;
  try {
    window.localStorage.setItem(STORAGE_COLLAPSED_KEY, collapsed ? "1" : "0");
  } catch {
    /* ignore quota / private mode */
  }
}
