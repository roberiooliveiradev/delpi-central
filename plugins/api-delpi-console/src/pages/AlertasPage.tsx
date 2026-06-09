import { useCallback, useEffect, useState } from "react";
import { Bell, RefreshCw } from "lucide-react";
import {
  evaluateConsoleAlerts,
  fetchConsoleHealth,
  type ConsoleAlert,
  type ConsoleHealthPayload,
} from "../lib/consoleAlerts";

type Props = {
  onNavigate: (path: string) => void;
};

function severityClass(severity: string): string {
  if (severity === "critical") return "adc-badge adc-badge--err";
  if (severity === "warning") return "adc-badge adc-badge--warn";
  return "adc-badge adc-badge--ok";
}

export function AlertasPage({ onNavigate }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<ConsoleHealthPayload | null>(null);
  const [evaluating, setEvaluating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await fetchConsoleHealth();
      if (!payload) {
        throw new Error("Falha ao carregar saúde do console");
      }
      setHealth(payload);
    } catch (e) {
      setHealth(null);
      setError(e instanceof Error ? e.message : "Erro ao carregar alertas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 60_000);
    return () => window.clearInterval(timer);
  }, [load]);

  const runEvaluate = async (notify: boolean) => {
    setEvaluating(true);
    try {
      await evaluateConsoleAlerts(notify);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao avaliar alertas");
    } finally {
      setEvaluating(false);
    }
  };

  const renderAlert = (alert: ConsoleAlert, key: string) => (
    <article key={key} className="adc-panel adc-panel--table">
      <div className="adc-toolbar">
        <span className={severityClass(alert.severity)}>{alert.severity}</span>
        <code className="adc-mono-sm">{alert.code}</code>
      </div>
      <p>{alert.message}</p>
    </article>
  );

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Alertas</h1>
          <p className="adc-subtitle">
            Smoke com falha, p95 acima do limiar e SQL lento — webhook opcional e visão no Admin
            Stats.
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
          <button
            type="button"
            className="adc-btn adc-btn--primary"
            onClick={() => void runEvaluate(true)}
            disabled={evaluating}
          >
            <Bell size={16} />
            Avaliar e notificar
          </button>
        </div>
      </header>

      {error ? <div className="adc-panel adc-panel--danger">{error}</div> : null}

      {health ? (
        <div className="adc-metrics adc-metrics--grid adc-metrics--compact">
          <div className="adc-stat">
            <span className="adc-stat__label">Status</span>
            <strong>{health.status}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Alertas abertos</span>
            <strong>{health.open_alert_count}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">p95 (ms)</span>
            <strong>
              {health.metrics.p95_ms} / {health.thresholds.p95_ms}
            </strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Webhook</span>
            <strong>{health.webhook_configured ? "Configurado" : "Desligado"}</strong>
          </div>
        </div>
      ) : null}

      {loading && !health ? (
        <div className="adc-panel adc-muted">Carregando alertas…</div>
      ) : null}

      {health && health.open_alerts.length > 0 ? (
        <section>
          <h2 className="adc-section-title">Alertas abertos</h2>
          {health.open_alerts.map((alert) => renderAlert(alert, `open-${alert.code}-${alert.message}`))}
        </section>
      ) : health ? (
        <div className="adc-panel adc-muted">Nenhum alerta aberto no momento.</div>
      ) : null}

      {health && health.recent_alerts.length > 0 ? (
        <section className="adc-panel adc-panel--table">
          <h2 className="adc-section-title">Histórico recente</h2>
          <div className="adc-table-wrap">
            <table className="adc-table">
              <thead>
                <tr>
                  <th>Severidade</th>
                  <th>Código</th>
                  <th>Mensagem</th>
                  <th>Quando</th>
                  <th>Webhook</th>
                </tr>
              </thead>
              <tbody>
                {health.recent_alerts.map((alert) => (
                  <tr key={`${alert.code}-${alert.recorded_at}`}>
                    <td>
                      <span className={severityClass(alert.severity)}>{alert.severity}</span>
                    </td>
                    <td>
                      <code className="adc-mono-sm">{alert.code}</code>
                    </td>
                    <td>{alert.message}</td>
                    <td className="adc-muted">{alert.recorded_at ?? "—"}</td>
                    <td>{alert.notified ? "Sim" : "Não"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
