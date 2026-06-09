import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { apiFetch } from "../api/httpClient";
import { MONITOR_REFRESH_MS } from "../constants/monitoring";
import { navigateConsole } from "../lib/consoleNavigation";
import { useConsoleSearchParams } from "../lib/useConsoleSearchParams";
import { usePolling } from "../lib/usePolling";

type SqlAggregate = {
  query_hash: string;
  preview: string;
  count: number;
  avg_ms: number;
  max_ms: number;
  total_ms: number;
  last_operation_id?: string | null;
  last_caller_app?: string | null;
  last_repository?: string | null;
};

type OperationAggregate = {
  operation_id?: string | null;
  label: string;
  count: number;
  avg_ms: number;
  max_ms: number;
  total_ms: number;
  query_count: number;
  last_caller_app?: string | null;
};

type TimelinePoint = {
  recorded_at: string;
  duration_ms: number;
  query_hash: string;
  preview: string;
  caller_app?: string | null;
  repository?: string | null;
};

type SqlHealthPayload = {
  storage_backend?: string;
  total_samples: number;
  top_by_duration: SqlAggregate[];
  top_by_count: SqlAggregate[];
  by_operation_id?: OperationAggregate[];
  filter_operation_id?: string;
  timeline?: TimelinePoint[];
  queries_in_operation?: SqlAggregate[];
};

type Props = {
  onNavigate: (path: string) => void;
};

function unwrapPayload(data: unknown): SqlHealthPayload | null {
  if (!data || typeof data !== "object") return null;
  const envelope = data as { data?: SqlHealthPayload };
  const payload = envelope.data ?? (data as SqlHealthPayload);
  if (!Array.isArray(payload.top_by_duration)) return null;
  return payload;
}

function formatRecordedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function operationLabel(operationId: string | null | undefined): string {
  if (!operationId) return "—";
  return operationId;
}

function BarChart({
  rows,
  valueKey,
  labelKey,
  unit,
  onSelect,
  selectedId,
}: {
  rows: Array<Record<string, string | number | null | undefined>>;
  valueKey: string;
  labelKey: string;
  unit: string;
  onSelect?: (id: string) => void;
  selectedId?: string | null;
}) {
  const maxValue = Math.max(...rows.map((row) => Number(row[valueKey] ?? 0)), 1);

  return (
    <div className="adc-bar-chart">
      {rows.map((row) => {
        const rawLabel = String(row[labelKey] ?? "—");
        const value = Number(row[valueKey] ?? 0);
        const width = Math.max(4, Math.round((value / maxValue) * 100));
        const opId = row.operation_id;
        const selectableId =
          typeof opId === "string" ? opId : opId == null ? "__none__" : String(opId);
        const isSelected = selectedId === selectableId;

        return (
          <div className="adc-bar-chart__row" key={`${rawLabel}-${value}`}>
            {onSelect ? (
              <button
                type="button"
                className={`adc-bar-chart__label adc-op-link${isSelected ? " adc-op-link--active" : ""}`}
                onClick={() => onSelect(selectableId)}
              >
                <code className="adc-mono-sm">{rawLabel}</code>
              </button>
            ) : (
              <span className="adc-bar-chart__label">
                <code className="adc-mono-sm">{rawLabel}</code>
              </span>
            )}
            <div className="adc-bar-chart__track" aria-hidden>
              <div className="adc-bar-chart__fill" style={{ width: `${width}%` }} />
            </div>
            <span className="adc-bar-chart__value">
              {value} {unit}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function SqlHealthPage({ onNavigate }: Props) {
  const searchParams = useConsoleSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SqlHealthPayload | null>(null);
  const [selectedOperationId, setSelectedOperationId] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const highlightedQueryHash = searchParams.get("query_hash");

  const load = useCallback(
    async (operationId?: string | null, options?: { silent?: boolean }) => {
      if (!options?.silent) {
        setLoading(true);
      }
      setError(null);
      try {
        const query: Record<string, string> = { limit: "30" };
        if (operationId) {
          query.operation_id = operationId;
        }
        const response = await apiFetch("/system/sql-health", { query });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = unwrapPayload(response.data);
        if (!payload) {
          throw new Error("Resposta inválida de /system/sql-health");
        }
        setSummary(payload);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha ao carregar telemetria SQL");
        setSummary(null);
      } finally {
        if (!options?.silent) {
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    const operationId = searchParams.get("operation_id");
    if (operationId) {
      setSelectedOperationId(operationId);
    }
  }, [searchParams]);

  useEffect(() => {
    void load(selectedOperationId);
  }, [load, selectedOperationId]);

  usePolling(() => load(selectedOperationId, { silent: true }), MONITOR_REFRESH_MS, {
    enabled: autoRefresh,
  });

  const selectOperation = (operationId: string | null) => {
    setSelectedOperationId(operationId);
    if (operationId && operationId !== "__none__") {
      navigateConsole("sql", undefined, {
        operation_id: operationId,
        query_hash: highlightedQueryHash,
      });
      return;
    }
    navigateConsole(
      "sql",
      undefined,
      highlightedQueryHash ? { query_hash: highlightedQueryHash } : undefined,
    );
  };

  const drillDownLabel = useMemo(() => {
    if (!selectedOperationId) return null;
    if (selectedOperationId === "__none__") return "—";
    return selectedOperationId;
  }, [selectedOperationId]);

  const renderOperationCell = (operationId?: string | null) => {
    const label = operationLabel(operationId);
    if (!operationId) {
      return (
        <button
          type="button"
          className="adc-op-link"
          onClick={() => selectOperation("__none__")}
        >
          <code className="adc-mono-sm">{label}</code>
        </button>
      );
    }
    return (
      <button
        type="button"
        className="adc-op-link"
        onClick={() => selectOperation(operationId)}
      >
        <code className="adc-mono-sm">{label}</code>
      </button>
    );
  };

  const renderTable = (title: string, rows: SqlAggregate[]) => (
    <section className="adc-panel adc-panel--table">
      <h2 className="adc-section-title">{title}</h2>
      {rows.length === 0 ? (
        <p className="adc-muted">Nenhuma amostra ainda. Execute rotas que consultam o Protheus.</p>
      ) : (
        <div className="adc-table-wrap">
          <table className="adc-table">
            <thead>
              <tr>
                <th>Hash</th>
                <th>Query</th>
                <th>Qtd</th>
                <th>Média ms</th>
                <th>Máx ms</th>
                <th>Operation Id</th>
                <th>Caller</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`${title}-${row.query_hash}`}
                  className={
                    highlightedQueryHash && row.query_hash === highlightedQueryHash
                      ? "adc-table__row--highlight"
                      : undefined
                  }
                >
                  <td>
                    <code className="adc-mono-sm">{row.query_hash}</code>
                  </td>
                  <td className="adc-table__preview">{row.preview}</td>
                  <td>{row.count}</td>
                  <td>{row.avg_ms}</td>
                  <td>{row.max_ms}</td>
                  <td>{renderOperationCell(row.last_operation_id)}</td>
                  <td className="adc-muted">{row.last_caller_app ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );

  const operationRows = summary?.by_operation_id ?? [];

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Saúde SQL</h1>
          <p className="adc-subtitle">
            Top queries por duração e repetição — ring buffer{" "}
            {summary?.storage_backend === "redis" ? "Redis" : "em memória"}.
            {selectedOperationId
              ? " Drill-down por operation id."
              : " Monitoramento ao vivo a cada 30 s com a aba visível."}
          </p>
        </div>
        <div className="adc-header__actions">
          {!selectedOperationId ? (
            <label className="adc-check">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(event) => setAutoRefresh(event.target.checked)}
              />
              Auto 30 s
            </label>
          ) : (
            <button
              type="button"
              className="adc-btn adc-btn--ghost"
              onClick={() => selectOperation(null)}
            >
              Voltar ao resumo
            </button>
          )}
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={() => void load(selectedOperationId)}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "adc-spin" : undefined} />
            Atualizar
          </button>
        </div>
      </header>

      {error ? <div className="adc-panel adc-panel--danger">{error}</div> : null}

      {summary ? (
        <div className="adc-metrics adc-metrics--grid adc-metrics--compact">
          <div className="adc-stat">
            <span className="adc-stat__label">Amostras no buffer</span>
            <strong>{summary.total_samples}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Armazenamento</span>
            <strong>{summary.storage_backend === "redis" ? "Redis" : "Memória"}</strong>
          </div>
          {selectedOperationId ? (
            <div className="adc-stat">
              <span className="adc-stat__label">Operation Id</span>
              <strong>
                <code className="adc-mono-sm">{drillDownLabel}</code>
              </strong>
            </div>
          ) : null}
        </div>
      ) : null}

      {loading && !summary ? (
        <div className="adc-panel adc-muted">Carregando telemetria SQL…</div>
      ) : null}

      {summary && !selectedOperationId ? (
        <section className="adc-panel">
          <h2 className="adc-section-title">Execuções por Operation Id</h2>
          {operationRows.length === 0 ? (
            <p className="adc-muted">Sem amostras com operation id ainda.</p>
          ) : (
            <BarChart
              rows={operationRows}
              valueKey="count"
              labelKey="label"
              unit="exec"
              onSelect={(id) => selectOperation(id)}
            />
          )}
        </section>
      ) : null}

      {summary && selectedOperationId && summary.timeline ? (
        <section className="adc-panel">
          <h2 className="adc-section-title">Linha do tempo — duração por execução</h2>
          {summary.timeline.length === 0 ? (
            <p className="adc-muted">Nenhuma execução para este operation id.</p>
          ) : (
            <BarChart
              rows={summary.timeline.map((point, index) => ({
                operation_id: `${point.query_hash}-${index}`,
                label: `${formatRecordedAt(point.recorded_at)} · ${point.duration_ms} ms`,
                count: point.duration_ms,
              }))}
              valueKey="count"
              labelKey="label"
              unit="ms"
            />
          )}
        </section>
      ) : null}

      {summary ? (
        <>
          {selectedOperationId && summary.queries_in_operation
            ? renderTable(`Queries em ${drillDownLabel}`, summary.queries_in_operation)
            : null}
          {!selectedOperationId ? renderTable("Mais lentas (máx ms)", summary.top_by_duration) : null}
          {!selectedOperationId ? renderTable("Mais repetidas", summary.top_by_count) : null}
        </>
      ) : null}
    </div>
  );
}
