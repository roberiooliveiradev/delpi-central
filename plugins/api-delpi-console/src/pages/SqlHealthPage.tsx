import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { apiFetch } from "../api/httpClient";

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

type SqlHealthPayload = {
  total_samples: number;
  top_by_duration: SqlAggregate[];
  top_by_count: SqlAggregate[];
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

export function SqlHealthPage({ onNavigate }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SqlHealthPayload | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch("/system/sql-health?limit=30");
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
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

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
                <tr key={`${title}-${row.query_hash}`}>
                  <td>
                    <code className="adc-mono-sm">{row.query_hash}</code>
                  </td>
                  <td className="adc-table__preview">{row.preview}</td>
                  <td>{row.count}</td>
                  <td>{row.avg_ms}</td>
                  <td>{row.max_ms}</td>
                  <td>
                    <code className="adc-mono-sm">{row.last_operation_id ?? "—"}</code>
                  </td>
                  <td className="adc-muted">{row.last_caller_app ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Saúde SQL</h1>
          <p className="adc-subtitle">
            Top queries por duração e repetição — amostras recentes do ring buffer em memória.
          </p>
        </div>
        <div className="adc-header__actions">
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={() => void load()}
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
        </div>
      ) : null}

      {loading && !summary ? (
        <div className="adc-panel adc-muted">Carregando telemetria SQL…</div>
      ) : null}

      {summary ? (
        <>
          {renderTable("Mais lentas (máx ms)", summary.top_by_duration)}
          {renderTable("Mais repetidas", summary.top_by_count)}
        </>
      ) : null}
    </div>
  );
}
