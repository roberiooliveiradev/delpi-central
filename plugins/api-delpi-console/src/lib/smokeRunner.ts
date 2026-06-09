import { apiFetch, type ApiFetchResult } from "../api/httpClient";
import { smokeSuites } from "../content/smokeSuites";

export type SmokeCase = {
  id: string;
  label: string;
  method: string;
  path: string;
  query?: Record<string, string>;
  expectStatus?: number[];
  maxDurationMs?: number;
};

export type SmokeSuite = {
  id: string;
  name: string;
  description: string;
  cases: SmokeCase[];
};

export type SmokeCaseResult = {
  caseId: string;
  label: string;
  path: string;
  method: string;
  ok: boolean;
  status: number;
  durationMs: number;
  operationIdHeader?: string;
  message: string;
  result: ApiFetchResult;
};

export type SmokeSuiteResult = {
  suiteId: string;
  startedAt: string;
  finishedAt: string;
  totalMs: number;
  passed: number;
  failed: number;
  cases: SmokeCaseResult[];
};

const STORAGE_KEY = "api-delpi-console:smoke-last-result";

type ApiEnvelope<T> = {
  data?: T;
  meta?: unknown;
};

type SmokeDefinitionsPayload = {
  version?: string;
  suites: SmokeSuite[];
};

let resolvedSuitesCache: SmokeSuite[] | null = null;

function resolveOperationId(response: ApiFetchResult): string | undefined {
  const header =
    response.headers["x-operation-id"] ?? response.headers["X-Operation-Id"];
  if (header) return header;

  const payload = response.data;
  if (!payload || typeof payload !== "object") return undefined;

  const envelope = payload as { meta?: { operationId?: string } };
  const operationId = envelope.meta?.operationId;
  return typeof operationId === "string" && operationId.trim() ? operationId.trim() : undefined;
}

function unwrapSmokeDefinitions(data: unknown): SmokeSuite[] | null {
  if (!data || typeof data !== "object") return null;
  const envelope = data as ApiEnvelope<SmokeDefinitionsPayload>;
  const payload = envelope.data ?? (data as SmokeDefinitionsPayload);
  if (!Array.isArray(payload.suites) || payload.suites.length === 0) return null;
  return payload.suites;
}

export function listSmokeSuites(): SmokeSuite[] {
  return resolvedSuitesCache ?? smokeSuites.suites;
}

export async function resolveSmokeSuites(): Promise<SmokeSuite[]> {
  if (resolvedSuitesCache) return resolvedSuitesCache;

  try {
    const response = await apiFetch<ApiEnvelope<SmokeDefinitionsPayload>>(
      "/system/smoke-definitions",
    );
    const suites = response.ok ? unwrapSmokeDefinitions(response.data) : null;
    if (suites) {
      resolvedSuitesCache = suites;
      return suites;
    }
  } catch {
    /* fallback local */
  }

  resolvedSuitesCache = smokeSuites.suites;
  return resolvedSuitesCache;
}

export async function runSmokeSuite(suite: SmokeSuite): Promise<SmokeSuiteResult> {
  const started = performance.now();
  const startedAt = new Date().toISOString();
  const cases: SmokeCaseResult[] = [];

  for (const testCase of suite.cases) {
    const response = await apiFetch(testCase.path, {
      method: testCase.method,
      query: testCase.query,
    });

    const expected = testCase.expectStatus ?? [200];
    const statusOk = expected.includes(response.status);
    const durationOk =
      testCase.maxDurationMs === undefined || response.durationMs <= testCase.maxDurationMs;

    let message = "OK";
    if (!statusOk) {
      message = `Status ${response.status} (esperado: ${expected.join(", ")})`;
    } else if (!durationOk) {
      message = `Lento: ${response.durationMs} ms (limite ${testCase.maxDurationMs} ms)`;
    }

    const operationIdHeader = resolveOperationId(response);

    cases.push({
      caseId: testCase.id,
      label: testCase.label,
      path: testCase.path,
      method: testCase.method,
      ok: statusOk && durationOk,
      status: response.status,
      durationMs: response.durationMs,
      operationIdHeader,
      message,
      result: response,
    });
  }

  const finishedAt = new Date().toISOString();
  const suiteResult: SmokeSuiteResult = {
    suiteId: suite.id,
    startedAt,
    finishedAt,
    totalMs: Math.round(performance.now() - started),
    passed: cases.filter((c) => c.ok).length,
    failed: cases.filter((c) => !c.ok).length,
    cases,
  };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(suiteResult));
  return suiteResult;
}

export function loadLastSmokeResult(): SmokeSuiteResult | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SmokeSuiteResult;
  } catch {
    return null;
  }
}

function csvEscape(value: string | number | boolean): string {
  return `"${String(value).replace(/"/g, '""')}"`;
}

export function smokeResultToCsv(result: SmokeSuiteResult): string {
  const header =
    "suite_id,case_id,label,method,path,ok,status,duration_ms,operation_id,message";
  const rows = result.cases.map((item) =>
    [
      result.suiteId,
      item.caseId,
      item.label,
      item.method,
      item.path,
      item.ok,
      item.status,
      item.durationMs,
      item.operationIdHeader ?? "",
      item.message,
    ]
      .map(csvEscape)
      .join(","),
  );
  return [header, ...rows].join("\n");
}

export function downloadSmokeResult(result: SmokeSuiteResult, format: "csv" | "json"): void {
  const stamp = result.finishedAt.slice(0, 19).replace(/[:T]/g, "-");
  const filename = `api-delpi-smoke-${result.suiteId}-${stamp}.${format}`;
  const content =
    format === "json" ? JSON.stringify(result, null, 2) : smokeResultToCsv(result);
  const mime = format === "json" ? "application/json" : "text/csv;charset=utf-8";
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
