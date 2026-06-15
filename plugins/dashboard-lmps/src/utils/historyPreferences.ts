import type { HistoryEventFilter } from "./historyFormatting";

export type HistoryViewMode = "timeline" | "table";

const VIEW_STORAGE_KEY = "dashboard-lmps:history-view";
const FILTER_STORAGE_KEY = "dashboard-lmps:history-filter";

const VALID_FILTERS = new Set<HistoryEventFilter>([
  "all",
  "engineering",
  "open",
  "current_revision",
]);

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore quota / private mode
  }
}

export function readHistoryViewMode(): HistoryViewMode {
  const value = readStorage(VIEW_STORAGE_KEY);
  return value === "table" ? "table" : "timeline";
}

export function writeHistoryViewMode(mode: HistoryViewMode): void {
  writeStorage(VIEW_STORAGE_KEY, mode);
}

export function readHistoryEventFilter(): HistoryEventFilter {
  const value = readStorage(FILTER_STORAGE_KEY);
  if (value && VALID_FILTERS.has(value as HistoryEventFilter)) {
    return value as HistoryEventFilter;
  }

  return "current_revision";
}

export function writeHistoryEventFilter(filter: HistoryEventFilter): void {
  writeStorage(FILTER_STORAGE_KEY, filter);
}
