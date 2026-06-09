export type QueryCacheNamespace = {
  namespace: string;
  hits: number;
  misses: number;
  sets: number;
  lookups: number;
  hit_rate_pct: number;
  active_keys: number;
};

export type ObservabilitySnapshot = {
  captured_at: string;
  label?: string;
  query_cache: {
    backend: string;
    ttl_seconds: number;
    totals: {
      hits: number;
      misses: number;
      sets: number;
      lookups: number;
      hit_rate_pct: number;
    };
    namespaces: QueryCacheNamespace[];
  };
  caller_stats: {
    total_requests: number;
    by_caller: Array<{
      caller_app?: string | null;
      label: string;
      count: number;
      avg_ms: number;
      errors: number;
      route_count?: number;
    }>;
  };
  sql_health: {
    total_samples: number;
    storage_backend?: string;
  };
};

export type SnapshotDiffRow = {
  section: string;
  key: string;
  before: string;
  after: string;
  delta: string;
};

const STORAGE_KEY = "api-delpi-console:observability-snapshots";

type StoredSnapshots = {
  before?: ObservabilitySnapshot;
  after?: ObservabilitySnapshot;
};

function unwrapSnapshot(data: unknown): ObservabilitySnapshot | null {
  if (!data || typeof data !== "object") return null;
  const envelope = data as { data?: ObservabilitySnapshot };
  const payload = envelope.data ?? (data as ObservabilitySnapshot);
  if (!payload.query_cache || !payload.caller_stats) return null;
  return payload;
}

export function parseObservabilitySnapshot(data: unknown): ObservabilitySnapshot | null {
  return unwrapSnapshot(data);
}

export function loadStoredSnapshots(): StoredSnapshots {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as StoredSnapshots;
  } catch {
    return {};
  }
}

export function saveSnapshot(slot: "before" | "after", snapshot: ObservabilitySnapshot): void {
  const stored = loadStoredSnapshots();
  stored[slot] = snapshot;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
}

export function clearStoredSnapshots(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function compareSnapshots(
  before: ObservabilitySnapshot,
  after: ObservabilitySnapshot,
): SnapshotDiffRow[] {
  const rows: SnapshotDiffRow[] = [];

  rows.push({
    section: "cache",
    key: "totals.hit_rate_pct",
    before: String(before.query_cache.totals.hit_rate_pct),
    after: String(after.query_cache.totals.hit_rate_pct),
    delta: formatDelta(
      before.query_cache.totals.hit_rate_pct,
      after.query_cache.totals.hit_rate_pct,
      "pp",
    ),
  });

  const beforeNamespaces = new Map(
    before.query_cache.namespaces.map((item) => [item.namespace, item]),
  );
  const afterNamespaces = new Map(after.query_cache.namespaces.map((item) => [item.namespace, item]));
  const namespaces = new Set([...beforeNamespaces.keys(), ...afterNamespaces.keys()]);

  for (const namespace of namespaces) {
    const left = beforeNamespaces.get(namespace);
    const right = afterNamespaces.get(namespace);
    rows.push({
      section: "cache",
      key: `${namespace}.hits`,
      before: String(left?.hits ?? 0),
      after: String(right?.hits ?? 0),
      delta: formatDelta(left?.hits ?? 0, right?.hits ?? 0),
    });
    rows.push({
      section: "cache",
      key: `${namespace}.misses`,
      before: String(left?.misses ?? 0),
      after: String(right?.misses ?? 0),
      delta: formatDelta(left?.misses ?? 0, right?.misses ?? 0),
    });
  }

  const beforeCallers = new Map(
    before.caller_stats.by_caller.map((item) => [item.label, item.count]),
  );
  const afterCallers = new Map(
    after.caller_stats.by_caller.map((item) => [item.label, item.count]),
  );
  const callers = new Set([...beforeCallers.keys(), ...afterCallers.keys()]);

  for (const caller of callers) {
    const left = beforeCallers.get(caller) ?? 0;
    const right = afterCallers.get(caller) ?? 0;
    rows.push({
      section: "caller",
      key: caller,
      before: String(left),
      after: String(right),
      delta: formatDelta(left, right),
    });
  }

  rows.push({
    section: "sql",
    key: "total_samples",
    before: String(before.sql_health.total_samples),
    after: String(after.sql_health.total_samples),
    delta: formatDelta(before.sql_health.total_samples, after.sql_health.total_samples),
  });

  return rows;
}

function formatDelta(before: number, after: number, suffix = ""): string {
  const delta = after - before;
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta}${suffix}`;
}

export function diffToCsv(rows: SnapshotDiffRow[]): string {
  const header = "section,key,before,after,delta";
  const body = rows.map((row) =>
    [row.section, row.key, row.before, row.after, row.delta]
      .map((value) => `"${String(value).replace(/"/g, '""')}"`)
      .join(","),
  );
  return [header, ...body].join("\n");
}

export function downloadDiffCsv(rows: SnapshotDiffRow[], stamp: string): void {
  const blob = new Blob([diffToCsv(rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `api-delpi-observability-diff-${stamp}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
