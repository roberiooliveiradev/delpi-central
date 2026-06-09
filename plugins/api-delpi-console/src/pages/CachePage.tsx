import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, RefreshCw } from "lucide-react";
import { apiFetch } from "../api/httpClient";
import {
  compareSnapshots,
  downloadDiffCsv,
  loadStoredSnapshots,
  parseObservabilitySnapshot,
  saveSnapshot,
  type ObservabilitySnapshot,
  type SnapshotDiffRow,
} from "../lib/observabilitySnapshot";

type QueryCachePayload = ObservabilitySnapshot["query_cache"];
type CallerStatsPayload = ObservabilitySnapshot["caller_stats"];

type Props = {
  onNavigate: (path: string) => void;
};

function unwrapEnvelope<T>(data: unknown): T | null {
  if (!data || typeof data !== "object") return null;
  const envelope = data as { data?: T };
  return envelope.data ?? (data as T);
}

export function CachePage({ onNavigate }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cacheStats, setCacheStats] = useState<QueryCachePayload | null>(null);
  const [callerStats, setCallerStats] = useState<CallerStatsPayload | null>(null);
  const [stored, setStored] = useState(loadStoredSnapshots());
  const [diffRows, setDiffRows] = useState<SnapshotDiffRow[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cacheResponse, callerResponse] = await Promise.all([
        apiFetch("/system/query-cache/stats"),
        apiFetch("/system/caller-stats?limit=30"),
      ]);

      if (!cacheResponse.ok) {
        throw new Error(`Cache stats HTTP ${cacheResponse.status}`);
      }
      if (!callerResponse.ok) {
        throw new Error(`Caller stats HTTP ${callerResponse.status}`);
      }

      const cachePayload = unwrapEnvelope<QueryCachePayload>(cacheResponse.data);
      const callerPayload = unwrapEnvelope<CallerStatsPayload>(callerResponse.data);
      if (!cachePayload || !callerPayload) {
        throw new Error("Resposta inválida de observabilidade");
      }

      setCacheStats(cachePayload);
      setCallerStats(callerPayload);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao carregar observabilidade");
      setCacheStats(null);
      setCallerStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const captureSnapshot = useCallback(async (slot: "before" | "after") => {
    const response = await apiFetch("/system/observability-snapshot?limit=30");
    if (!response.ok) {
      throw new Error(`Snapshot HTTP ${response.status}`);
    }
    const snapshot = parseObservabilitySnapshot(response.data);
    if (!snapshot) {
      throw new Error("Snapshot inválido");
    }
    saveSnapshot(slot, snapshot);
    setStored(loadStoredSnapshots());
  }, []);

  const runCompare = useCallback(() => {
    if (!stored.before || !stored.after) return;
    setDiffRows(compareSnapshots(stored.before, stored.after));
  }, [stored.after, stored.before]);

  const compareReady = Boolean(stored.before && stored.after);

  const diffPreview = useMemo(() => diffRows.slice(0, 12), [diffRows]);

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Cache e callers</h1>
          <p className="adc-subtitle">
            Hits/miss do cache LMP e estoque, breakdown por caller app e comparador de deploy.
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

      {cacheStats ? (
        <div className="adc-metrics adc-metrics--grid adc-metrics--compact">
          <div className="adc-stat">
            <span className="adc-stat__label">Backend cache</span>
            <strong>{cacheStats.backend}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">TTL (s)</span>
            <strong>{cacheStats.ttl_seconds}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Hit rate</span>
            <strong>{cacheStats.totals.hit_rate_pct}%</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Requests rastreados</span>
            <strong>{callerStats?.total_requests ?? 0}</strong>
          </div>
        </div>
      ) : null}

      {loading && !cacheStats ? (
        <div className="adc-panel adc-muted">Carregando cache e callers…</div>
      ) : null}

      {cacheStats ? (
        <section className="adc-panel adc-panel--table">
          <h2 className="adc-section-title">Cache por namespace</h2>
          {cacheStats.namespaces.length === 0 ? (
            <p className="adc-muted">Sem lookups ainda. Acesse LMP ou estoque para aquecer o cache.</p>
          ) : (
            <div className="adc-table-wrap">
              <table className="adc-table">
                <thead>
                  <tr>
                    <th>Namespace</th>
                    <th>Hits</th>
                    <th>Misses</th>
                    <th>Sets</th>
                    <th>Hit rate</th>
                    <th>Chaves ativas</th>
                  </tr>
                </thead>
                <tbody>
                  {cacheStats.namespaces.map((row) => (
                    <tr key={row.namespace}>
                      <td>
                        <code className="adc-mono-sm">{row.namespace}</code>
                      </td>
                      <td>{row.hits}</td>
                      <td>{row.misses}</td>
                      <td>{row.sets}</td>
                      <td>{row.hit_rate_pct}%</td>
                      <td>{row.active_keys}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}

      {callerStats ? (
        <section className="adc-panel adc-panel--table">
          <h2 className="adc-section-title">Callers (X-Delpi-Caller-App)</h2>
          {callerStats.by_caller.length === 0 ? (
            <p className="adc-muted">Nenhum request com caller app registrado ainda.</p>
          ) : (
            <div className="adc-table-wrap">
              <table className="adc-table">
                <thead>
                  <tr>
                    <th>Caller</th>
                    <th>Requests</th>
                    <th>Rotas distintas</th>
                    <th>Média ms</th>
                    <th>Erros</th>
                  </tr>
                </thead>
                <tbody>
                  {callerStats.by_caller.map((row) => (
                    <tr key={row.label}>
                      <td>
                        <code className="adc-mono-sm">{row.label}</code>
                      </td>
                      <td>{row.count}</td>
                      <td>{row.route_count}</td>
                      <td>{row.avg_ms}</td>
                      <td>{row.errors}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : null}

      <section className="adc-panel">
        <h2 className="adc-section-title">Comparador antes/depois de deploy</h2>
        <p className="adc-muted adc-suite-desc">
          Capture um snapshot antes e outro depois do deploy; exporte o diff em CSV.
        </p>
        <div className="adc-toolbar">
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={() => void captureSnapshot("before").catch((e) => setError(String(e)))}
          >
            Capturar «antes»
          </button>
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={() => void captureSnapshot("after").catch((e) => setError(String(e)))}
          >
            Capturar «depois»
          </button>
          <button
            type="button"
            className="adc-btn adc-btn--primary"
            disabled={!compareReady}
            onClick={runCompare}
          >
            Comparar
          </button>
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            disabled={diffRows.length === 0}
            onClick={() =>
              downloadDiffCsv(diffRows, new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-"))
            }
          >
            <Download size={16} />
            Exportar CSV
          </button>
        </div>
        <div className="adc-metrics adc-metrics--grid adc-metrics--compact">
          <div className="adc-stat">
            <span className="adc-stat__label">Antes</span>
            <strong className="adc-mono-sm">{stored.before?.captured_at ?? "—"}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Depois</span>
            <strong className="adc-mono-sm">{stored.after?.captured_at ?? "—"}</strong>
          </div>
        </div>
        {diffRows.length > 0 ? (
          <div className="adc-table-wrap">
            <table className="adc-table">
              <thead>
                <tr>
                  <th>Seção</th>
                  <th>Chave</th>
                  <th>Antes</th>
                  <th>Depois</th>
                  <th>Delta</th>
                </tr>
              </thead>
              <tbody>
                {diffPreview.map((row) => (
                  <tr key={`${row.section}-${row.key}`}>
                    <td>{row.section}</td>
                    <td>
                      <code className="adc-mono-sm">{row.key}</code>
                    </td>
                    <td>{row.before}</td>
                    <td>{row.after}</td>
                    <td>{row.delta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {diffRows.length > diffPreview.length ? (
              <p className="adc-muted">Exibindo {diffPreview.length} de {diffRows.length} linhas no diff.</p>
            ) : null}
          </div>
        ) : null}
      </section>
    </div>
  );
}
