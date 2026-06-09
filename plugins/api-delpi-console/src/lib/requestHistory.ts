import type { ApiFetchResult } from "../api/httpClient";

export type HistoryEntry = {
  id: string;
  timestamp: string;
  operationId?: string;
  path: string;
  method: string;
  status: number;
  durationMs: number;
  ok: boolean;
  operationIdHeader?: string;
  responseTimeHeader?: string;
};

const STORAGE_KEY = "api-delpi-console:history";
const MAX_ENTRIES = 50;

function readAll(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as HistoryEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeAll(entries: HistoryEntry[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)));
}

export function listHistory(): HistoryEntry[] {
  return readAll();
}

export function appendHistory(
  result: ApiFetchResult,
  meta?: { operationId?: string; path: string; method: string },
): HistoryEntry {
  const entry: HistoryEntry = {
    id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    operationId: meta?.operationId,
    path: meta?.path ?? result.url,
    method: meta?.method ?? result.method,
    status: result.status,
    durationMs: result.durationMs,
    ok: result.ok,
    operationIdHeader:
      result.headers["x-operation-id"] ?? result.headers["X-Operation-Id"],
    responseTimeHeader:
      result.headers["x-response-time-ms"] ?? result.headers["X-Response-Time-Ms"],
  };

  const entries = [entry, ...readAll()];
  writeAll(entries);
  return entry;
}

export function clearHistory(): void {
  localStorage.removeItem(STORAGE_KEY);
}
