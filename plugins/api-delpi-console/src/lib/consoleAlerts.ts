import { apiFetch } from "../api/httpClient";
import type { SmokeSuiteResult } from "./smokeRunner";

export type ConsoleAlert = {
  code: string;
  severity: string;
  message: string;
  details?: Record<string, unknown>;
};

export type ConsoleHealthPayload = {
  status: "ok" | "warning" | "critical";
  open_alert_count: number;
  open_alerts: ConsoleAlert[];
  recent_alerts: Array<
    ConsoleAlert & {
      recorded_at?: string;
      notified?: boolean;
      portal_notified?: boolean;
    }
  >;
  metrics: {
    p95_ms: number;
    caller_requests: number;
    sql_samples: number;
    cache_hit_rate_pct: number;
  };
  thresholds: {
    p95_ms: number;
    slow_sql_ms: number;
  };
  webhook_configured: boolean;
  portal_notifications_configured?: boolean;
  captured_at?: string;
  monitoring?: {
    mode: string;
    recommended_refresh_seconds: number;
    description: string;
  };
};

function unwrap<T>(data: unknown): T | null {
  if (!data || typeof data !== "object") return null;
  const envelope = data as { data?: T };
  return envelope.data ?? (data as T);
}

export async function fetchConsoleHealth(): Promise<ConsoleHealthPayload | null> {
  const response = await apiFetch("/system/console-health");
  if (!response.ok) return null;
  return unwrap<ConsoleHealthPayload>(response.data);
}

export async function evaluateConsoleAlerts(notify = false): Promise<ConsoleAlert[]> {
  const response = await apiFetch(`/system/console-alerts/evaluate?notify=${notify ? "true" : "false"}`, {
    method: "POST",
  });
  if (!response.ok) return [];
  const payload = unwrap<{ alerts: ConsoleAlert[] }>(response.data);
  return payload?.alerts ?? [];
}

export async function notifySmokeAlerts(result: SmokeSuiteResult): Promise<void> {
  await apiFetch("/system/console-alerts/smoke?notify=true", {
    method: "POST",
    body: {
      suiteId: result.suiteId,
      passed: result.passed,
      failed: result.failed,
      totalMs: result.totalMs,
      startedAt: result.startedAt,
      finishedAt: result.finishedAt,
      cases: result.cases.map((item) => ({
        caseId: item.caseId,
        label: item.label,
        ok: item.ok,
        status: item.status,
        durationMs: item.durationMs,
        message: item.message,
        operationIdHeader: item.operationIdHeader,
      })),
    },
  });
}
