import type { ConsoleAlert } from "./consoleAlerts";

export type AlertAction = {
  label: string;
  segment: string;
  searchParams?: Record<string, string>;
};

function asString(value: unknown): string | null {
  if (value == null) return null;
  const text = String(value).trim();
  return text || null;
}

function asNumber(value: unknown): number | null {
  if (value == null || value === "") return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

export function alertDetailRows(alert: ConsoleAlert): Array<{ label: string; value: string }> {
  const details = alert.details ?? {};
  const rows: Array<{ label: string; value: string }> = [];

  if (alert.code === "slow_sql") {
    const preview = asString(details.preview);
    const queryHash = asString(details.query_hash);
    const operationId = asString(details.operation_id);
    const maxMs = asNumber(details.max_ms);
    const threshold = asNumber(details.threshold_ms);
    const repository = asString(details.last_repository);

    if (preview) rows.push({ label: "Query", value: preview });
    if (queryHash) rows.push({ label: "Hash", value: queryHash });
    if (operationId) rows.push({ label: "Operation id", value: operationId });
    if (repository) rows.push({ label: "Repositório", value: repository });
    if (maxMs != null) rows.push({ label: "Máximo", value: `${maxMs} ms` });
    if (threshold != null) rows.push({ label: "Limiar", value: `${threshold} ms` });
  }

  if (alert.code === "p95_latency") {
    const p95 = asNumber(details.p95_ms);
    const threshold = asNumber(details.threshold_ms);
    if (p95 != null) rows.push({ label: "p95 atual", value: `${p95} ms` });
    if (threshold != null) rows.push({ label: "Limiar", value: `${threshold} ms` });
  }

  if (alert.code === "smoke_failure") {
    const suiteId = asString(details.suite_id);
    const failed = asNumber(details.failed);
    const passed = asNumber(details.passed);
    if (suiteId) rows.push({ label: "Suite", value: suiteId });
    if (passed != null && failed != null) {
      rows.push({ label: "Resultado", value: `${passed} ok · ${failed} falha(s)` });
    }
    const cases = Array.isArray(details.cases) ? details.cases : [];
    for (const item of cases.slice(0, 5)) {
      if (!item || typeof item !== "object") continue;
      const record = item as Record<string, unknown>;
      const label = asString(record.label) ?? asString(record.caseId) ?? "Caso";
      const message = asString(record.message) ?? asString(record.status) ?? "falhou";
      rows.push({ label, value: message });
    }
  }

  return rows;
}

export function alertSuggestedAction(alert: ConsoleAlert): AlertAction | null {
  const details = alert.details ?? {};

  if (alert.code === "slow_sql") {
    const operationId = asString(details.operation_id);
    const queryHash = asString(details.query_hash);
    const searchParams: Record<string, string> = {};
    if (operationId) searchParams.operation_id = operationId;
    if (queryHash) searchParams.query_hash = queryHash;
    return {
      label: "Investigar na aba SQL",
      segment: "sql",
      searchParams: Object.keys(searchParams).length > 0 ? searchParams : undefined,
    };
  }

  if (alert.code === "p95_latency") {
    return { label: "Ver callers e cache", segment: "cache" };
  }

  if (alert.code === "smoke_failure") {
    return { label: "Abrir verificações", segment: "verificacoes" };
  }

  return null;
}

export function alertGuidance(alert: ConsoleAlert): string {
  if (alert.code === "slow_sql") {
    return "Abra SQL para ver o preview completo, o operation id e quantas vezes a query repetiu. Se for LMP/estoque, confira também o hit rate na aba Cache.";
  }
  if (alert.code === "p95_latency") {
    return "Latência HTTP alta no período recente. Use Cache para ver quem está chamando a API e SQL para queries pesadas por rota.";
  }
  if (alert.code === "smoke_failure") {
    return "Uma ou mais rotas críticas falharam no smoke. Reexecute a suite em Verificações e confira operation id e status HTTP de cada caso.";
  }
  return "Monitore as métricas nas abas SQL, Cache e Verificações.";
}
